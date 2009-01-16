# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

from navigationtool import NavigationTool
from selectiontool import SelectionTool
from game.world.building.building import *
from game.world.building.path import Path
from game.command.building import Build

import fife
import game.main
import math
import pychan

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class BuildingTool(NavigationTool):
	"""
	@param building: selected building type"
	@param ship: If building from a ship, restrict to range of ship
	"""

	def begin(self, building, ship = None):
		import random

		super(BuildingTool, self).begin()
		self.ship = ship
		self._class = building
		self.buildings = []
		self.rotation = 45 + random.randint(0,3)*90
		self.startPoint, self.endPoint = None, None
		self.last_change_listener = None
		self.load_gui()
		if not self._class.class_package == 'path':
			self.gui.show()

		game.main.onEscape = self.onEscape

		if ship is None:
			for island in game.main.session.world.islands:
				for tile in island.grounds:
					if tile.settlement is not None and tile.settlement.owner == game.main.session.world.player and self._class.isGroundBuildRequirementSatisfied(tile.x, tile.y, island) is not None:
						game.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, 255, 255, 255)
						if tile.object is not None:
							game.main.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)
		else:
			found_free = False
			for island in game.main.session.world.islands:
				if True:#todo: check if radius in island rect
					for tile in island.grounds:
						if ((tile.x - self.ship.position.x) ** 2 + (tile.y - self.ship.position.y) ** 2) <= 25:
							free = (tile.settlement is None or tile.settlement.owner == game.main.session.world.player)
							game.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, *((255,255,255) if free else (0,0,0)))
							if free and tile.object is not None:
								game.main.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)
							found_free = found_free or free
			if not found_free:
				self.onEscape()

	def end(self):
		game.main.session.view.renderer['InstanceRenderer'].removeAllColored()
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		game.main.session.view.removeChangeListener(self.draw_gui)
		if self.last_change_listener is not None and self.last_change_listener.hasChangeListener(self.update_preview):
			self.last_change_listener.removeChangeListener(self.update_preview)
		self.gui.hide()
		super(BuildingTool, self).end()

	def load_gui(self):
		self.gui = game.main.fife.pychan.loadXML("content/gui/build_menu/hud_builddetail.xml")
		self.gui.mapEvents( { "rotate_left": self.rotate_left,
							  "rotate_right": self.rotate_right }
							)
		self.gui.position = (game.main.fife.settings.getScreenWidth()/2-self.gui.size[0]/2, game.main.fife.settings.getScreenHeight()/1 - game.main.session.ingame_gui.gui['minimap'].size[1]/1)
		self.gui.findChild(name='running_costs').text = str(self._class.running_costs)
		self.draw_gui()
		game.main.session.view.addChangeListener(self.draw_gui)

	def draw_gui(self):
		image = game.main.db("SELECT file FROM animation INNER JOIN action ON animation.animation_id=action.animation_id LEFT JOIN action_set ON action_set.action_set_id=action.action_set_id WHERE building_id=? AND action.action='default' AND action.rotation=?", self._class.id, (self.rotation+int(game.main.session.view.cam.getRotation())-45)%360)
		if len(image) > 0:
			self.gui.findChild(name='building').image = image[0][0]
		else:
			image = game.main.db("SELECT file FROM animation INNER JOIN action ON animation.animation_id=action.animation WHERE action.action_set_id=? AND action.action='default' AND action.rotation=?", self._class._action_set_id, 45)
			if len(image) > 0:
				print "WARNING: no rotation for building id:", self._class.id, "and rotation:", self.rotation
				self.gui.findChild(name='building').image = image[0][0]
			else:
				assert(False, "No image for building id:", self._class.id, "in the db!")
		self.gui.resizeToContent()

	def previewBuild(self, point1, point2):
		print "PREVIEW BUILD"
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		self.buildings = self._class.getBuildList(point1, point2, ship = self.ship, rotation = self.rotation)
		neededResources, usableResources = {}, {}
		settlement = None
		for building in self.buildings:
			settlement = building.get('settlement', None) if settlement is None else settlement
			building['instance'] = self._class.getInstance(**building)
			resources = self._class.getBuildCosts(**building)
			if not building.get('buildable', True):
				game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 0, 0)
			else:
				for resource in resources:
					neededResources[resource] = neededResources.get(resource, 0) + resources[resource]
				for resource in neededResources:
					if ( game.main.session.world.player.inventory[resource] if resource == 1 else 0 ) + (self.ship.inventory[resource] if self.ship is not None else building['settlement'].inventory[resource] if building['settlement'] is not None else 0) < neededResources[resource]:
						game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 0, 0)
						building['buildable'] = False
						break
				else:
					building['buildable'] = True
					for resource in resources:
						usableResources[resource] = usableResources.get(resource, 0) + resources[resource]
					game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 255, 255)
		game.main.session.ingame_gui.resourceinfo_set(self.ship if self.ship is not None else settlement, neededResources, usableResources)
		if self.last_change_listener != self.ship if self.ship is not None else settlement:
			if self.last_change_listener is not None:
				self.last_change_listener.removeChangeListener(self.update_preview)
			self.last_change_listener = self.ship if self.ship is not None else settlement
			if self.last_change_listener is not None:
				self.last_change_listener.addChangeListener(self.update_preview)

	def onEscape(self):
		game.main.session.ingame_gui.resourceinfo_set(None)
		if self.ship is None:
			game.main.session.ingame_gui.show_menu('build')
		else:
			game.main.session.selected_instances = set([self.ship])
			self.ship.select()
			self.ship.show_menu()
		self.gui.hide()
		game.main.session.cursor = SelectionTool()

	def mouseMoved(self, evt):
		super(BuildingTool, self).mouseMoved(evt)
		mapcoord = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
		if self.startPoint != point:
			self.startPoint = point
			self.previewBuild(point, point)
		evt.consume()

	def mousePressed(self, evt):
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mousePressed(evt)
			return
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.onEscape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			mapcoord = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
			if self.startPoint != point:
				self.startPoint = point
				self.previewBuild(point, point)
				self.startPoint = None
		else:
			super(BuildingTool, self).mousePressed(evt)
			return
		evt.consume()

	def mouseDragged(self, evt):
		super(BuildingTool, self).mouseDragged(evt)
		mapcoord = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
		if self.endPoint != point:
			self.endPoint = point
			assert self.startPoint is not None, "startPoint is None"
			self.previewBuild(self.startPoint, point)
		evt.consume()

	def mouseReleased(self, evt):
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mouseReleased(evt)
		elif fife.MouseEvent.LEFT == evt.getButton():
			mapcoord = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			point = (math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25, math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)
			if self.endPoint != point:
				self.endPoint = point
				self.previewBuild(self.startPoint, point)
				self.endPoint = None
			default_args = {'building' : self._class, 'ship' : self.ship}
			found_buildable = False
			if self.last_change_listener is not None:
				self.last_change_listener.removeChangeListener(self.update_preview)
			print "Building...."

			for building in self.buildings:
				if building['buildable']:
					found_buildable = True
					game.main.session.view.renderer['InstanceRenderer'].removeColored(building['instance'])
					args = default_args.copy()
					args.update(building)
					game.main.session.manager.execute(Build(**args))
					self.gui.hide()
				else:
					building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
			self.buildings = []
			if evt.isShiftPressed() or not found_buildable:
				self.startPoint = point
				self.previewBuild(point, point)
			else:
				self.onEscape()
			evt.consume()
		elif fife.MouseEvent.RIGHT != evt.getButton():
			super(BuildingTool, self).mouseReleased(evt)

	def update_preview(self):
		if self.startPoint is not None:
			self.previewBuild(self.startPoint, self.startPoint if self.endPoint is None else self.endPoint)

	def rotate_right(self):
		self.rotation = (self.rotation + 270) % 360
		self.update_preview()
		self.draw_gui()

	def rotate_left(self):
		self.rotation = (self.rotation + 90) % 360
		self.update_preview()
		self.draw_gui()
