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

	def end(self):
		game.main.session.view.renderer['InstanceRenderer'].removeAllColored()
		for building in self.buildings:
			game.main.session.view.layers[1].deleteInstance(building['instance'])
		super(BuildingTool, self).end()

	#def _buildCheck(self,  x, y):
		#"""@param x,y: int position that is to be checked."""
		## TODO: Return more detailed error descriptions than a boolean
		#try:
			#cost = self._class.calcBuildingCost()
		#except BlockedError:
			#print 'blocked error'
			#return False

		#if self.ship:
			#if (max(x - self.ship.position[0], 0, self.ship.position[0] - x - self._class.size[0] + 1) ** 2) + (max(y - self.ship.position[1], 0, self.ship.position[1] - (y + self._class.size[1]-1)) ** 2) >= 100:
				#return False

		#island = game.main.session.world.get_island(x, y)
		#if island:
			#settlements = island.get_settlements(x, y, x + self._class.size[0] - 1, y + self._class.size[1] - 1)
			#if len(settlements) > 0 and self.ship and not False: #False -> game setting "allow_multi_settlements_pre_island"
				#return False
			#elif len(settlements) > 0 or self.ship:
				#settlement = settlements.pop() if len(settlements) > 0 else None
				#for (key, value) in cost.iteritems(): # Cost checking
					#if game.main.session.world.player.inventory.get_value(key) + (settlement.inventory.get_value(key) if settlement else self.ship.inventory.get_value(key)) < value:
						#print "Warning: more ressources of #%i needed for building id '%i'. Storage %i < %i" % (key, self._class.id, game.main.session.world.player.inventory.get_value(key) + (settlement.inventory.get_value(key) if settlement else self.ship.inventory.get_value(key)), value)
						#return False
				#for xx in xrange(x, x + self._class.size[0]): # Blocked checking
					#for yy in xrange(y, y + self._class.size[1]):
						#tile = island.get_tile(xx, yy)
						#if not tile or tile.blocked:
							#return False
				#return True
			#else:
				#return False
		#else:
			#return False

	def previewBuild(self, point1, point2):
		for building in self.buildings:
			game.main.session.view.layers[1].deleteInstance(building['instance'])
		self.buildings = []
		buildList = self._class.getBuildList(point1, point2)
		if buildList is None:
			return
		self.buildings_island = buildList['island']
		self.buildings_settlement = buildList['settlement']
		self.buildings = buildList['buildings']
		neededRessources, usableRessources = {}, {}
		for building in self.buildings:
			building['instance'] = self._class.getInstance(**building)
			ressources = self._class.getBuildCosts(**building)
			for ressource in ressources:
				neededRessources[ressource] = neededRessources.get(ressource, 0) + ressources[ressource]
			for ressource in neededRessources:
				available = ( game.main.session.world.player.inventory.get_value(ressource) if ressource == 1 else 0 ) + (self.ship.inventory.get_value(ressource) if self.ship is not None else self.buildings_settlement.inventory.get_value(ressource) if self.buildings_settlement is not None else 0)
				building['buildable'] = available >= neededRessources[ressource]
				if building['buildable'] == False:
					game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 0, 0)
					break
			else:
				building['buildable'] = True
				for ressource in ressources:
					usableRessources[ressource] = neededRessources.get(ressource, 0) + ressources[ressource]
				game.main.session.view.renderer['InstanceRenderer'].addColored(building['instance'], 255, 255, 255)

	def onEscape(self):
		if self.ship is None:
			game.main.session.ingame_gui.show_menu('build')
		else:
			game.main.session.selected_instances = [self.ship]
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
			default_args = {'building' : self._class, 'ship':self.ship, 'island' : self.buildings_island, 'settlement' : self.buildings_settlement}
			for building in self.buildings:
				if building['buildable']:
					game.main.session.view.renderer['InstanceRenderer'].removeColored(building['instance'])
					args = default_args.copy()
					args.update(building)
					game.main.session.manager.execute(Build(**args))
				else:
					game.main.session.view.layers[1].deleteInstance(building['instance'])
			self.buildings = []
			self.onEscape()
			evt.consume()
		elif fife.MouseEvent.RIGHT != evt.getButton():
			super(BuildingTool, self).mouseReleased(evt)
