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
from game.command.building import Build

import fife
import game.main
import math

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
		super(BuildingTool, self).begin()
		self.ship = ship
		self._class = building
		self.buildings = []
		self.startPoint, self.endPoint = None, None

		game.main.onEscape = self.onEscape

		if ship is None:
			for island in game.main.session.world.islands:
				for tile in island.grounds:
					if tile.settlement is not None and tile.settlement.owner == game.main.session.world.player:
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
		super(BuildingTool, self).end()

	def previewBuild(self, point1, point2):
		for building in self.buildings:
			building['instance'].getLocationRef().getLayer().deleteInstance(building['instance'])
		self.buildings = self._class.getBuildList(point1, point2, ship = self.ship)
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
					if ( game.main.session.world.player.inventory.get_value(resource) if resource == 1 else 0 ) + (self.ship.inventory.get_value(resource) if self.ship is not None else building['settlement'].inventory.get_value(resource) if building['settlement'] is not None else 0) < neededResources[resource]:
						game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 0, 0)
						building['buildable'] = False
						break
				else:
					building['buildable'] = True
					for resource in resources:
						usableResources[resource] = usableResources.get(resource, 0) + resources[resource]
					game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 255, 255)
		game.main.session.ingame_gui.resourceinfo_set(self.ship if self.ship is not None else settlement, neededResources, usableResources)

	def onEscape(self):
		game.main.session.ingame_gui.resourceinfo_set(None)
		if self.ship is None:
			game.main.session.ingame_gui.show_menu('build')
		else:
			game.main.session.selected_instances = set([self.ship])
			self.ship.select()
			self.ship.show_menu()
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
			default_args = {'building' : self._class, 'ship':self.ship}
			found_buildable = False
			for building in self.buildings:
				if building['buildable']:
					found_buildable = True
					game.main.session.view.renderer['InstanceRenderer'].removeColored(building['instance'])
					args = default_args.copy()
					args.update(building)
					game.main.session.manager.execute(Build(**args))
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
