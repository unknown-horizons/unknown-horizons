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
from fife import fife
import logging
import random

import horizons.main

from horizons.util import ActionSetLoader, Point, decorators, Callback, WorldObject
from horizons.command.building import Build, Tear
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.gui.mousetools.selectiontool import SelectionTool
from horizons.command.sounds import PlaySound
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
	nearby_objects_radius = 3

	gui = None # share gui between instances

	def __init__(self, session, building, ship = None):
		super(BuildingTool, self).__init__(session)
		self.renderer = self.session.view.renderer['InstanceRenderer']
		self.ship = ship
		self._class = building
		self.buildings = [] # list of PossibleBuild objs
		self.buildings_fife_instances = {} # fife instances of possible builds
		self.buildings_missing_resources = {} # missing resources for possible builds
		self.rotation = 45 + random.randint(0, 3)*90
		self.startPoint, self.endPoint = None, None
		self.last_change_listener = None
		if self._class.show_buildingtool_preview_tab:
			self.load_gui()
			self.gui.show()
			self.session.ingame_gui.minimap_to_front()

		self.session.gui.on_escape = self.on_escape

		self._modified_objects = set() # fife instances modified for transparency
		self._buildable_tiles = [] # tiles marked as buildable

		self.highlight_buildable()

	@decorators.make_constants()
	def highlight_buildable(self, tiles_to_check = None):
		"""Highlights all buildable tiles.
		@param tiles_to_check: list of tiles to check for coloring."""
		# resolved variables from inner loops
		is_tile_buildable = self._class.is_tile_buildable
		add_colored = self.renderer.addColored
		player = self.session.world.player
		session = self.session
		buildable_tiles_append = self._buildable_tiles.append
		ship = self.ship
		buildable_color = self.buildable_color

		if tiles_to_check is not None: # only check these tiles
			for tile in tiles_to_check:
				if is_tile_buildable(session, tile, ship):
					buildable_tiles_append(tile)
					add_colored(tile._instance, *buildable_color)
					if tile.object is not None:
						add_colored(tile.object._instance, *buildable_color)

		elif self.ship is None: # default build on island
			for island in self.session.world.islands:
				# small optimisation: check only islands with player settlements
				for settlement in island.settlements:
					if settlement.owner == player:
						break
				else:
					continue
				for tile in island.grounds:
					if is_tile_buildable(session, tile, ship):
						buildable_tiles_append(tile)
						add_colored(tile._instance, *buildable_color)
						if tile.object is not None:
							add_colored(tile.object._instance, *buildable_color)

		else: # build from ship
			for island in self.session.world.get_islands_in_radius(self.ship.position, self.ship.radius):
				for tile in island.get_surrounding_tiles(self.ship.position, self.ship.radius):
					buildable_tiles_append(tile)
					# check that there is no other player's settlement
					if tile.settlement is None or tile.settlement.owner == player:
						add_colored(tile._instance, *buildable_color)
						if tile.object is not None: # color obj on tile too
							add_colored(tile.object._instance, *buildable_color)

	def end(self):
		self._remove_building_instances()
		self._remove_coloring()
		self._buildable_tiles = None
		self._modified_objects = None
		self.buildings = None
		if self.gui is not None:
			self.session.view.remove_change_listener(self.draw_gui)
			self.gui.hide()
		self._remove_listeners()
		ExtScheduler().rem_all_classinst_calls(self)
		super(BuildingTool, self).end()

	def load_gui(self):
		if self.gui is None:
			self.gui = load_xml_translated("build_menu/hud_builddetail.xml")
			self.gui.stylize('menu_black')
			self.gui.findChild(name='headline').stylize('headline')
			self.gui.findChild(name='building_name').stylize('headline')
			top_bar = self.gui.findChild(name='top_bar')
			top_bar.position = (self.gui.size[0]/2 - top_bar.size[0]/2 -16, 50)
			self.gui.position = (
				horizons.main.fife.settings.getScreenWidth() - self.gui.size[0] - 14,
				157
			)
		self.gui.mapEvents( { "rotate_left": self.rotate_left,
							  "rotate_right": self.rotate_right } )
		# set building name in gui
		self.gui.findChild(name='building_name').text = u'  ' + unicode(self._class._name)
		self.gui.findChild(name='running_costs').text = unicode(self._class.running_costs)
		head_box = self.gui.findChild(name='head_box')
		head_box.adaptLayout() # recalculates size for new content
		head_box.position = ( # calculate and set new center (pychan doesn't support it)
		  self.gui.size[0]/2 - head_box.size[0]/2,
	    head_box.position[1]
	    )
		head_box.adaptLayout()
		self.draw_gui()
		self.session.view.add_change_listener(self.draw_gui)

	def draw_gui(self):
		# TODO: change hard-coded 0 below to a variable, as soon as building leveling concept
		# is decided.
		action_set, preview_action_set = self.session.db.get_random_action_set(self._class.id, 0)
		action_sets = ActionSetLoader.get_action_sets()
		if preview_action_set in action_sets:
			action_set = preview_action_set
		if 'idle' in action_sets[action_set]:
			action = 'idle'
		elif 'idle_full' in action_sets[action_set]:
			action = 'idle_full'
		else: # If no idle animation found, use the first you find
			action = action_sets[action_set].keys()[0]
		image = sorted(action_sets[action_set][action][(self.rotation+int(self.session.view.cam.getRotation())-45)%360].keys())[0]
		building_icon = self.gui.findChild(name='building')
		building_icon.image = image
		# TODO: Remove hardcoded 70
		building_icon.position = (self.gui.size[0]/2 - building_icon.size[0]/2, self.gui.size[1]/2 - building_icon.size[1]/2 - 70)
		self.gui.adaptLayout()

	@decorators.make_constants()
	def preview_build(self, point1, point2):
		"""Display buildings as preview if build requirements are met"""
		self.log.debug("BuildingTool: preview build at %s, %s", point1, point2)
		new_buildings = self._class.check_build_line(self.session, point1, point2,
		                                             rotation = self.rotation, ship=self.ship)
		# optimisation: If only one building is in the preview and the position hasn't changed
		# => don't preview. Otherwise the preview is redrawn on every mouse move
		if len(new_buildings) == 1 and len(self.buildings) == 1:
			if new_buildings[0].position == self.buildings[0].position:
				return # we don't want to redo the preview

		# remove old fife instances and coloring
		self._remove_building_instances()

		# get new ones
		self.buildings = new_buildings
		# delete old infos
		self.buildings_fife_instances.clear()
		self.buildings_missing_resources.clear()

		settlement = None # init here so we can access it below loop
		neededResources, usableResources = {}, {}
		# check if the buildings are buildable and color them appropriatly
		for building in self.buildings:
			from horizons.world.building.buildable import _BuildPosition
			assert isinstance(building, _BuildPosition)

			# make surrounding transparent
			self._make_surrounding_transparent(building.position)

			self.buildings_fife_instances[building] = \
			    self._class.getInstance(self.session, building.position.origin.x, \
			                            building.position.origin.y, rotation=building.rotation,
			                            action=building.action)

			settlement = self.session.world.get_settlement(building.position.center())
			if building.buildable:
				# building seems to buildable, check res too now
				for resource in self._class.costs:
					neededResources[resource] = neededResources.get(resource, 0) + \
					               self._class.costs[resource]
				for resource in neededResources:
					# check player, ship and settlement inventory
					available_res = 0
					# player
					available_res += self.session.world.player.inventory[resource] if \
					              resource == RES.GOLD_ID else 0
					# ship or settlement
					if self.ship is not None:
						available_res += self.ship.inventory[resource]
					elif settlement is not None:
						available_res += settlement.inventory[resource]

					if available_res < neededResources[resource]:
						# can't build, not enough res
						self.renderer.addColored(self.buildings_fife_instances[building], \
						                         *self.not_buildable_color)
						building.buildable = False
						self.buildings_missing_resources[building] = resource
						break
				else:
					for resource in self._class.costs:
						usableResources[resource] = usableResources.get(resource, 0) + \
						               self._class.costs[resource]

			if building.buildable:
				self.renderer.addColored(self.buildings_fife_instances[building], \
				                         *self.buildable_color)
				# draw radius in a moment, and not always immediately, since it's expensive
				if hasattr(self._class, "select_building"):
					callback = Callback(self._class.select_building, self.session, \
					                    building.position, settlement)
					ExtScheduler().rem_all_classinst_calls(self)
					delay = 0.08 # Wait delay seconds
					ExtScheduler().add_new_object(callback, self, delay)

			else: # not buildable
				self.renderer.addColored(self.buildings_fife_instances[building], \
				                         *self.not_buildable_color)
		self.session.ingame_gui.resourceinfo_set( \
		   self.ship if self.ship is not None else settlement, neededResources, usableResources, \
		   res_from_ship = bool(self.ship))
		self._add_listeners(self.ship if self.ship is not None else settlement)

	@decorators.make_constants()
	def _make_surrounding_transparent(self, building_position):
		"""Makes the surrounding of building_position transparent"""
		world_contains = self.session.world.map_dimensions.contains_without_border
		get_tile = self.session.world.get_tile
		for coord in building_position.get_radius_coordinates(self.nearby_objects_radius, include_self=True):
			p = Point(*coord)
			if not world_contains(p):
				continue
			tile = get_tile(p)
			if tile.object is not None and tile.object.buildable_upon:
				tile.object.fife_instance.get2dGfxVisual().setTransparency( \
				  self.nearby_objects_transparency )
				self._modified_objects.add(tile.object)

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
		point = self._get_world_location_from_event(evt)
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
		point = self._get_world_location_from_event(evt)
		if self.startPoint is not None:
			self._check_update_preview(point)
		evt.consume()

	def mouseReleased(self, evt):
		"""Acctually build."""
		self.log.debug("BuildingTool mouseReleased")
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mouseReleased(evt)
		elif fife.MouseEvent.LEFT == evt.getButton():
			point = self._get_world_location_from_event(evt)

			# check if position has changed with this event and update everything
			self._check_update_preview(point)

			# acctually do the build
			found_buildable = self.do_build()

			# check how to continue: either build again or escapte
			if evt.isShiftPressed() or not found_buildable or self._class.class_package == 'path':
				self.startPoint = point
				self.preview_build(point, point)
			else:
				self.on_escape()
			evt.consume()
		elif fife.MouseEvent.RIGHT != evt.getButton():
			# TODO: figure out why there is a != in the comparison above. why not just use else?
			super(BuildingTool, self).mouseReleased(evt)

	@decorators.make_constants()
	def do_build(self):
		"""Acctually builds the previews
		@return whether it was possible to build anything of the previews."""
		built = False

		# first, tear down all buildings that are in the way
		# we have to check for multiple occurences of the same building to tear
		torn = set()
		for building in self.buildings:
			if building.buildable:
				for tear_id in building.tearset:
					if tear_id not in torn:
						Tear( WorldObject.get_object_by_id(tear_id) ).execute(self.session)
						torn.add(tear_id)

		# used to check if a building was built with this click, later used to play a sound
		built = False

		# acctually do the build and build preparations
		for building in self.buildings:
			# remove fife instance from here, it's now owned by the acctual building or deleted
			fife_instance = self.buildings_fife_instances.pop(building)

			if building.buildable:
				built = True
				self._remove_listeners() # Remove changelisteners for update_preview
				self.renderer.removeColored(fife_instance)
				# create the command and execute it
				cmd = Build(session=self.session, building=self._class, \
				            x=building.position.origin.x, \
				            y=building.position.origin.y, \
				            rotation=building.rotation, \
				            instance=fife_instance, \
				            island=self.session.world.get_island(building.position.origin), \
				            settlement=self.session.world.get_settlement(building.position.origin), \
				            ship=self.ship)
				cmd.execute(self.session)
			else:
				fife_instance.getLocationRef().getLayer().deleteInstance(fife_instance)
				# check whether to issue a missing res notification
				if building in self.buildings_missing_resources:
					res_name = self.session.db.get_res_name( self.buildings_missing_resources[building] )
					self.session.ingame_gui.message_widget.add(building['x'], building['y'], \
					                                           'NEED_MORE_RES', {'resource' : res_name})

		if built:
			PlaySound("build").execute(self.session)
			if self.gui is not None:
				self.gui.hide()
		self.buildings = []
		return built

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
			if self.last_change_listener.has_change_listener(self.highlight_buildable):
				self.last_change_listener.remove_change_listener(self.highlight_buildable)

		self.last_change_listener = None

	def _add_listeners(self, instance):
		if self.last_change_listener != instance:
			self._remove_listeners()
			self.last_change_listener = instance
			if self.last_change_listener is not None:
				if self.last_change_listener is self.ship:
					self.last_change_listener.add_change_listener(self.highlight_buildable)
				self.last_change_listener.add_change_listener(self.update_preview)

	def update_preview(self):
		"""Used as callback method"""
		if self.startPoint is not None:
			self.preview_build(self.startPoint,
			                   self.startPoint if self.endPoint is None else self.endPoint)

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

	def _remove_building_instances(self):
		"""Deletes fife instances of buildings"""
		if hasattr(self._class, "deselect_building"):
			deselected_tiles = self._class.deselect_building(self.session)
			# redraw buildables (removal of selection might have tampered with it)
			self.highlight_buildable(deselected_tiles)
		for obj in self._modified_objects:
			if obj.fife_instance is not None:
				obj.fife_instance.get2dGfxVisual().setTransparency(0)
		self._modified_objects.clear()
		for fife_instance in self.buildings_fife_instances.itervalues():
			layer = fife_instance.getLocationRef().getLayer()
			# layer might not exist, happens for some reason after a build
			if layer is not None:
				layer.deleteInstance(fife_instance)

	def _remove_coloring(self):
		"""Removes coloring from tiles, that indicate that the tile is buildable"""
		removeColored = self.renderer.removeColored
		for tile in self._buildable_tiles:
			removeColored(tile._instance)
			if tile.object is not None:
				removeColored(tile.object._instance)
		self._buildable_tiles = []

	def _get_world_location_from_event(self, evt):
		"""Returns the coordinates of an event at the map.
		@return Point with int coordinates"""
		screenpoint = fife.ScreenPoint(evt.getX(), evt.getY())
		mapcoord = self.session.view.cam.toMapCoordinates(screenpoint, False)
		# undocumented legacy formula to correct coords, probably:
		return Point(int(round(math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25)), \
		             int(round(math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)))

