# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import math
import fife
import logging
import random

import horizons.main

from horizons.util import ActionSetLoader, Circle, Point, decorators, Rect
from horizons.command.building import Build
from horizons.command.sounds import PlaySound
from navigationtool import NavigationTool
from selectiontool import SelectionTool
from horizons.i18n import load_xml_translated
from horizons.constants import RES
from horizons.extscheduler import ExtScheduler

class BuildingTool(NavigationTool):
	"""Represents a dangling tool after a building was selected from the list.
	Builder visualizes if and why a building can not be built under the cursor position.
	@param building: selected building type"
	@param ship: If building from a ship, restrict to range of ship
	"""
	log = logging.getLogger("gui.buildingtool")

	buildable_color = (255, 255, 255)
	not_buildable_color = (255, 0, 0)
	nearby_objects_transparency = 180
	nearby_objects_radius = 2

	def __init__(self, session, building, ship = None):
		super(BuildingTool, self).__init__(session)
		self.renderer = self.session.view.renderer['InstanceRenderer']
		self.ship = ship
		self._class = building
		self.buildings = []
		self.modified_objects = set()
		self.rotation = 45 + random.randint(0, 3)*90
		self.startPoint, self.endPoint = None, None
		self.last_change_listener = None
		self.gui = None
		if self._class.show_buildingtool_preview_tab:
			self.load_gui()
			self.gui.show()
			self.session.ingame_gui.minimap_to_front()

		self.session.gui.on_escape = self.on_escape

		if ship is None:
			self.highlight_buildable()
		else:
			self.highlight_ship_radius()

	@decorators.make_constants()
	def highlight_buildable(self):
		"""Highlights all buildable tiles."""
		ground_build_satisfied_fun = self._class._is_ground_build_requirement_satisfied
		add_colored = self.renderer.addColored
		player = self.session.world.player
		for island in self.session.world.islands:
			for tile in island.grounds:
				try:
					if tile.settlement.owner == player and \
					   ground_build_satisfied_fun(tile.x, tile.y, island) is not None:
						add_colored(tile._instance, *self.buildable_color)
						if tile.object is not None:
							add_colored(tile.object._instance, *self.buildable_color)
				except AttributeError:
					pass # tile has no settlement

	@decorators.make_constants()
	def highlight_ship_radius(self):
		"""Colors everything in the radius of the ship. Also checks whether
		there is a tile in the ships radius."""
		self.renderer.removeAllColored()
		for island in self.session.world.get_islands_in_radius(self.ship.position, self.ship.radius):
				for tile in island.get_surrounding_tiles(self.ship.position, self.ship.radius):
					# check that there is no other player's settlement
					free = (tile.settlement is None or \
									tile.settlement.owner == self.session.world.player)
					self.renderer.addColored( \
						tile._instance, *(self.buildable_color if free else (0, 0, 0)))
					if free and tile.object is not None:
						self.renderer.addColored(tile.object._instance, *self.buildable_color)

	def end(self):
		if hasattr(self._class, "deselect_building"):
			self._class.deselect_building(self.session)
		self.renderer.removeAllColored()
		for obj in self.modified_objects:
			if obj.fife_instance is not None:
				obj.fife_instance.get2dGfxVisual().setTransparency(0)
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		if self.gui is not None:
			self.session.view.remove_change_listener(self.draw_gui)
			self.gui.hide()
		self._remove_listeners()
		ExtScheduler().rem_all_classinst_calls(self)
		super(BuildingTool, self).end()

	def load_gui(self):
		self.gui = load_xml_translated("build_menu/hud_builddetail.xml")
		self.gui.mapEvents( { "rotate_left": self.rotate_left,
							  "rotate_right": self.rotate_right } )
		self.gui.stylize('menu_black')
		self.gui.findChild(name='headline').stylize('headline')
		# set building name in gui
		name_label = self.gui.findChild(name='building_name')
		name_label.stylize('headline')
		name_label.text = u'  ' + unicode(self._class.name)
		head_box = self.gui.findChild(name='head_box')
		head_box.adaptLayout()
		head_box.position = (
			self.gui.size[0]/2 - head_box.size[0]/2,
			head_box.position[1]
			)
		self.gui.position = (
			horizons.main.fife.settings.getScreenWidth() - self.gui.size[0] - 14,
			157
		)
		self.gui.findChild(name='running_costs').text = unicode(self._class.running_costs)
		top_bar = self.gui.findChild(name='top_bar')
		top_bar.position = (self.gui.size[0]/2 - top_bar.size[0]/2 -16, 50)
		self.draw_gui()
		self.session.view.add_change_listener(self.draw_gui)

	def draw_gui(self):
		action_set, preview_action_set = self.session.db("SELECT action_set_id, preview_action_set_id FROM action_set WHERE object_id=?", self._class.id)[0]
		action_sets = ActionSetLoader.get_action_sets()
		if preview_action_set in action_sets:
			action_set = preview_action_set
		if 'idle' in action_sets[action_set]:
			self.action = 'idle'
		elif 'idle_full' in action_sets[action_set]:
			self.action = 'idle_full'
		else: # If no idle animation found, use the first you find
			self.action = action_sets[action_set].keys()[0]
		image = sorted(action_sets[action_set][self.action][(self.rotation+int(self.session.view.cam.getRotation())-45)%360].keys())[0]
		building_icon = self.gui.findChild(name='building')
		building_icon.image = image
		building_icon.position = (self.gui.size[0]/2 - building_icon.size[0]/2, self.gui.size[1]/2 - building_icon.size[1]/2 - 70)
		self.gui.adaptLayout()

	@decorators.make_constants()
	def preview_build(self, point1, point2):
		"""Display buildings as preview if build requirements are met"""
		# remove old fife instances and coloring
		if hasattr(self._class, "deselect_building"):
			self._class.deselect_building(self.session)
		for obj in self.modified_objects:
			if obj.fife_instance is not None:
				obj.fife_instance.get2dGfxVisual().setTransparency(0)
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		# get new ones
		self.buildings = self._class.get_build_list(point1, point2, ship = self.ship, rotation = self.rotation)
		# make buildings around the preview transparent

		neededResources, usableResources = {}, {}
		settlement = None
		# check if the buildings are buildable and color them appropriatly
		for building in self.buildings:
			building_position = Rect.init_from_topleft_and_size(building['x'], building['y'],
			                                                    *self._class.size)
			# make surrounding transparent
			self._make_surrounding_transparent(building_position)

			settlement = building.get('settlement', None) if settlement is None else settlement

			building['rotation'] = self._class.check_build_rotation(building['rotation'], \
			                                                        building['x'], building['y'])
			building['instance'] = self._class.getInstance(self.session, **building)
			resources = self._class.get_build_costs(**building)
			if building.get('buildable', True):
				# building seems to buildable, check res too now
				for resource in resources:
					neededResources[resource] = neededResources.get(resource, 0) + resources[resource]
				for resource in neededResources:
					# check player, ship and settlement inventory
					available_res = 0
					# player
					available_res += self.session.world.player.inventory[resource] if resource == RES.GOLD_ID else 0
					# ship or settlement
					if self.ship is not None:
						available_res += self.ship.inventory[resource]
					elif building['settlement'] is not None:
						available_res += building['settlement'].inventory[resource]

					if available_res < neededResources[resource]:
						# can't build, not enough res
						self.renderer.addColored(building['instance'], *self.not_buildable_color)
						building['buildable'] = False
						building['missing_res'] = resource
						break
				else:
					building['buildable'] = True
					for resource in resources:
						usableResources[resource] = usableResources.get(resource, 0) + resources[resource]

			if building['buildable']:
				self.renderer.addColored(building['instance'], *self.buildable_color)
				# color radius tiles (just if building is buildable, since it's expensive)
				if hasattr(self._class, "select_building"):
					self._class.select_building(self.session, building_position, settlement)


			else:
				self.renderer.addColored(building['instance'], *self.not_buildable_color)
		self.session.ingame_gui.resourceinfo_set( \
		   self.ship if self.ship is not None else settlement, neededResources, usableResources, \
		   res_from_ship = (True if self.ship is not None else False))
		self._add_listeners(self.ship if self.ship is not None else settlement)

	def _make_surrounding_transparent(self, building_position):
		"""Makes the surrounding of building_position transparent"""
		for coord in building_position.get_radius_coordinates(self.nearby_objects_radius, include_self=True):
			p = Point(*coord)
			if not self.session.world.map_dimensions.contains_without_border(p):
				continue
			tile = self.session.world.get_tile(p)
			if tile.object is not None and tile.object.buildable_upon:
				tile.object.fife_instance.get2dGfxVisual().setTransparency( \
				  self.nearby_objects_transparency )
				self.modified_objects.add(tile.object)
	def on_escape(self):
		self.session.ingame_gui.resourceinfo_set(None)
		if self.ship is None:
			self.session.ingame_gui.show_build_menu()
		else:
			self.session.selected_instances = set([self.ship])
			self.ship.select()
			self.ship.show_menu()
		if self.gui is not None:
			self.gui.hide()
		self.session.cursor = SelectionTool(self.session)

	def mouseMoved(self, evt):
		self.log.debug("BuildingTool mouseMoved")
		super(BuildingTool, self).mouseMoved(evt)
		mapcoord = self.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
		if self.startPoint != point:
			self.startPoint = point
		self._check_update_preview(point)
		evt.consume()

	def mousePressed(self, evt):
		self.log.debug("BuildingTool mousePressed")
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mousePressed(evt)
			return
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.on_escape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			pass
		else:
			super(BuildingTool, self).mousePressed(evt)
			return
		evt.consume()

	def mouseDragged(self, evt):
		self.log.debug("BuildingTool mouseDragged")
		super(BuildingTool, self).mouseDragged(evt)
		mapcoord = self.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
		if self.startPoint is not None:
			self._check_update_preview(point)
		evt.consume()

	@decorators.make_constants()
	def mouseReleased(self, evt):
		self.log.debug("BuildingTool mouseReleased")
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mouseReleased(evt)
		elif fife.MouseEvent.LEFT == evt.getButton():
			mapcoord = self.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)

			self._check_update_preview(point)
			default_args = {'building' : self._class, 'ship' : self.ship}
			found_buildable = False
			# used to check if a building was built with this click
			# Later used to play a sound
			built = False
			for building in self.buildings:
				if building['buildable']:
					built = True
					self._remove_listeners() # Remove changelisteners for update_preview
					found_buildable = True
					self.renderer.removeColored(building['instance'])
					args = default_args.copy()
					args.update(building)
					Build(session=self.session, **args).execute()
					if self.gui is not None:
						self.gui.hide()
				else:
					building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
					# check whether to issue a missing res notification
					if 'missing_res' in building:
						res_name = horizons.main.db("SELECT name FROM resource WHERE id = ?", \
						                            building['missing_res'])[0][0]
						self.session.ingame_gui.message_widget.add(building['x'], building['y'], \
						                                           'NEED_MORE_RES', {'resource' : res_name})

			if built:
				self.session.manager.execute(PlaySound("build"))
			self.buildings = []
			if evt.isShiftPressed() or not found_buildable or self._class.class_package == 'path':
				self.startPoint = point
				self.preview_build(point, point)
			else:
				self.on_escape()
			evt.consume()
		elif fife.MouseEvent.RIGHT != evt.getButton():
			super(BuildingTool, self).mouseReleased(evt)

	def _check_update_preview(self, endpoint):
		"""Used internally if the endpoint changes"""
		if self.endPoint != endpoint:
			self.endPoint = endpoint
			self.update_preview()

	def _remove_listeners(self):
		"""Resets the ChangeListener for update_preview."""
		if self.last_change_listener is not None:
			if self.last_change_listener.has_change_listener(self.update_preview):
				self.last_change_listener.remove_change_listener(self.update_preview)
			if self.last_change_listener.has_change_listener(self.highlight_ship_radius):
				self.last_change_listener.remove_change_listener(self.highlight_ship_radius)
		self.last_change_listener = None

	def _add_listeners(self, instance):
		if self.last_change_listener != instance:
			self._remove_listeners()
			self.last_change_listener = instance
			if self.last_change_listener is not None:
				if self.last_change_listener is self.ship:
					self.last_change_listener.add_change_listener(self.highlight_ship_radius)
				self.last_change_listener.add_change_listener(self.update_preview)

	def update_preview(self):
		"""Used as callback method"""
		if self.startPoint is not None:
			self.preview_build(self.startPoint, self.startPoint if self.endPoint is None else self.endPoint)

	def rotate_right(self):
		self.rotation = (self.rotation + 270) % 360
		self.log.debug("BuildingTool: Building rotation now: %s", self.rotation)
		self.update_preview()
		self.draw_gui()

	def rotate_left(self):
		self.rotation = (self.rotation + 90) % 360
		self.log.debug("BuildingTool: Building rotation now: %s", self.rotation)
		self.update_preview()
		self.draw_gui()
