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

import horizons.main

from horizons.world.building.building import *
from horizons.command.building import Build
from horizons.command.sounds import PlaySound
from navigationtool import NavigationTool
from selectiontool import SelectionTool
from horizons.i18n import load_xml_translated

class BuildingTool(NavigationTool):
	"""Represents a dangling tool after a building was selected from the list.
	Builder visualizes if and why a building can not be built under the cursor position.
	@param building: selected building type"
	@param ship: If building from a ship, restrict to range of ship
	"""

	def __init__(self, building, ship = None):
		import random

		super(BuildingTool, self).__init__()
		self.ship = ship
		self._class = building
		self.buildings = []
		self.rotation = 45 + random.randint(0, 3)*90
		self.startPoint, self.endPoint = None, None
		self.last_change_listener = None
		self.load_gui()
		if not self._class.class_package == 'path':
			self.gui.show()

		horizons.main.gui.on_escape = self.on_escape

		if ship is None:
			for island in horizons.main.session.world.islands:
				for tile in island.grounds:
					if tile.settlement is not None and tile.settlement.owner == horizons.main.session.world.player and self._class.is_ground_build_requirement_satisfied(tile.x, tile.y, island) is not None:
						horizons.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, 255, 255, 255)
						if tile.object is not None:
							horizons.main.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)
		else:
			found_free = False
			for island in horizons.main.session.world.islands:
				if True:#todo: check if radius in island rect
					for tile in island.grounds:
						if ((tile.x - self.ship.position.x) ** 2 + (tile.y - self.ship.position.y) ** 2) <= 25:
							free = (tile.settlement is None or tile.settlement.owner == horizons.main.session.world.player)
							horizons.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, *((255, 255, 255) if free else (0, 0, 0)))
							if free and tile.object is not None:
								horizons.main.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)
							found_free = found_free or free
			if not found_free:
				self.on_escape()

	def end(self):
		horizons.main.session.view.renderer['InstanceRenderer'].removeAllColored()
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		horizons.main.session.view.removeChangeListener(self.draw_gui)
		self.gui.hide()
		self.reset_listeners()
		super(BuildingTool, self).end()

	def load_gui(self):
		self.gui = load_xml_translated("build_menu/hud_builddetail.xml")
		self.gui.mapEvents( { "rotate_left": self.rotate_left,
							  "rotate_right": self.rotate_right }
							)
		self.gui.stylize('menu_black')
		self.gui.findChild(name='headline').stylize('headline') # style definition for headline
		self.gui.position = (
			horizons.main.fife.settings.getScreenWidth() - self.gui.size[0],
			160
		)	
		#self.gui.position = (horizons.main.fife.settings.getScreenWidth()/2-self.gui.size[0]/2, horizons.main.fife.settings.getScreenHeight()/1 - horizons.main.session.ingame_gui.gui['minimap'].size[1]/1)
		self.gui.findChild(name='running_costs').text = unicode(self._class.running_costs)
		top_bar = self.gui.findChild(name='top_bar')
		top_bar.position = (self.gui.size[0]/2 - top_bar.size[0]/2 -16, 50)
		self.draw_gui()
		horizons.main.session.view.addChangeListener(self.draw_gui)

	def draw_gui(self):
		queryresult = horizons.main.db("SELECT action_set_id,preview_action_set_id FROM action_set WHERE building_id=?", self._class.id)[0]
		action_set,preview_action_set = queryresult
		if preview_action_set in horizons.main.action_sets.keys():
			action_set = preview_action_set
		if 'idle' in horizons.main.action_sets[action_set].keys():
			self.action = 'idle'
		elif 'idle_full' in horizons.main.action_sets[action_set].keys():
			self.action = 'idle_full'
		else: # If no idle animation found, use the first you find
			self.action = horizons.main.action_sets[action_set].keys()[0]
		image = sorted(horizons.main.action_sets[action_set][self.action][(self.rotation+int(horizons.main.session.view.cam.getRotation())-45)%360].keys())[0]
		building_icon = self.gui.findChild(name='building')
		building_icon.image = image
		building_icon.position = (self.gui.size[0]/2 - building_icon.size[0]/2 -13, self.gui.size[1]/2 - building_icon.size[1]/2 - 50)
		self.gui._recursiveResizeToContent()

	def preview_build(self, point1, point2):
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		self.buildings = self._class.get_build_list(point1, point2, ship = self.ship, rotation = self.rotation)
		neededResources, usableResources = {}, {}
		settlement = None
		for building in self.buildings:
			settlement = building.get('settlement', None) if settlement is None else settlement
			building['instance'] = self._class.getInstance(**building)
			resources = self._class.get_build_costs(**building)
			if not building.get('buildable', True):
				horizons.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 0, 0)
			else:
				for resource in resources:
					neededResources[resource] = neededResources.get(resource, 0) + resources[resource]
				for resource in neededResources:
					if ( horizons.main.session.world.player.inventory[resource] if resource == 1 else 0 ) + (self.ship.inventory[resource] if self.ship is not None else building['settlement'].inventory[resource] if building['settlement'] is not None else 0) < neededResources[resource]:
						horizons.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 0, 0)
						building['buildable'] = False
						break
				else:
					building['buildable'] = True
					for resource in resources:
						usableResources[resource] = usableResources.get(resource, 0) + resources[resource]
					horizons.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 255, 255)
		horizons.main.session.ingame_gui.resourceinfo_set(self.ship if self.ship is not None else settlement, neededResources, usableResources)
		self.reset_listeners()
		if self.last_change_listener != self.ship if self.ship is not None else settlement:
			self.last_change_listener = self.ship if self.ship is not None else settlement
			if self.last_change_listener is not None:
				self.last_change_listener.addChangeListener(self.update_preview)

	def on_escape(self):
		horizons.main.session.ingame_gui.resourceinfo_set(None)
		if self.ship is None:
			horizons.main.session.ingame_gui.show_build_menu()
		else:
			horizons.main.session.selected_instances = set([self.ship])
			self.ship.select()
			self.ship.show_menu()
		self.gui.hide()
		horizons.main.session.cursor = SelectionTool()

	def mouseMoved(self, evt):
		if horizons.main.debug:
			print "BuildingTool mouseMoved"
		super(BuildingTool, self).mouseMoved(evt)
		mapcoord = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
		if self.startPoint != point:
			self.startPoint = point
			self.preview_build(point, point)
		evt.consume()

	def mousePressed(self, evt):
		if horizons.main.debug:
			print "BuildingTool mousePressed"
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mousePressed(evt)
			return
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.on_escape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			pass
			#mapcoord = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			#point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
			#if self.startPoint != point:
			#	self.startPoint = point
			#	self.preview_build(point, point)
			#	self.startPoint = None
		else:
			super(BuildingTool, self).mousePressed(evt)
			return
		evt.consume()

	def mouseDragged(self, evt):
		if horizons.main.debug:
			print "BuildingTool mouseDragged"
		super(BuildingTool, self).mouseDragged(evt)
		mapcoord = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
		if self.endPoint != point and self.startPoint is not None:
			# Check if startPoint is set because it might be null if the user started dragging on a pychan widget
			self.endPoint = point
			self.preview_build(self.startPoint, point)
		evt.consume()

	def mouseReleased(self, evt):
		if horizons.main.debug:
			print "BuildingTool mouseReleased"
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mouseReleased(evt)
		elif fife.MouseEvent.LEFT == evt.getButton():
			mapcoord = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
			if self.endPoint != point:
				self.endPoint = point
				self.preview_build(self.startPoint, point)
				self.endPoint = None
			default_args = {'building' : self._class, 'ship' : self.ship}
			found_buildable = False
			print "Building...."
			# used to check if a building was built with this click
			# Later used to play a sound
			built = False
			for building in self.buildings:
				if building['buildable']:
					built = True
					self.reset_listeners() # Remove changelisteners for update_preview
					found_buildable = True
					horizons.main.session.view.renderer['InstanceRenderer'].removeColored(building['instance'])
					args = default_args.copy()
					args.update(building)
					horizons.main.session.manager.execute(Build(**args))
					self.gui.hide()
				else:
					building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
			if built:
				horizons.main.session.manager.execute(PlaySound("build"))
			self.buildings = []
			if evt.isShiftPressed() or not found_buildable:
				self.startPoint = point
				self.preview_build(point, point)
			else:
				self.on_escape()
			evt.consume()
		elif fife.MouseEvent.RIGHT != evt.getButton():
			super(BuildingTool, self).mouseReleased(evt)

	def reset_listeners(self):
		"""Resets the ChangeListener for update_preview."""
		if self.last_change_listener is not None and \
		   self.last_change_listener.hasChangeListener(self.update_preview):
			self.last_change_listener.removeChangeListener(self.update_preview)
		self.last_change_listener = None

	def update_preview(self):
		if self.startPoint is not None:
			self.preview_build(self.startPoint, self.startPoint if self.endPoint is None else self.endPoint)

	def rotate_right(self):
		self.rotation = (self.rotation + 270) % 360
		if horizons.main.debug:
			print "BuildingTool: Building rotation now:", self.rotation
		self.update_preview()
		self.draw_gui()

	def rotate_left(self):
		self.rotation = (self.rotation + 90) % 360
		if horizons.main.debug:
			print "BuildingTool: Building rotation now:", self.rotation
		self.update_preview()
		self.draw_gui()
