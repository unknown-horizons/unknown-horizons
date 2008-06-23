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

		self.previewInstance = self._class.createInstance(-100, -100)

		game.main.onEscape = self.onEscape

		if ship == None:
			for island in game.main.session.world.islands:
				for tile in island.grounds:
					if tile.settlement != None and tile.settlement.owner == game.main.session.world.player:
						game.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, 255, 255, 255)

	def end(self):
		game.main.session.view.renderer['InstanceRenderer'].removeAllColored()
		if self.previewInstance is not None:
			game.main.session.view.layers[1].deleteInstance(self.previewInstance)
		super(BuildingTool, self).end()


	def _buildCheck(self,  x, y):
		"""@param x,y: int position that is to be checked."""
		# TODO: Return more detailed error descriptions than a boolean
		try:
			cost = self._class.calcBuildingCost()
		except BlockedError:
			print 'blocked error'
			return False

		if self.ship:
			if (max(x - self.ship.position[0], 0, self.ship.position[0] - x - self._class.size[0] + 1) ** 2) + (max(y - self.ship.position[1], 0, self.ship.position[1] - (y + self._class.size[1]-1)) ** 2) >= 100:
				return False

		island = game.main.session.world.get_island(x, y)
		if island:
			settlement = island.get_settlement_at_position(x, y)
			if settlement and self.ship:
				return False
			elif settlement or self.ship:
				for (key, value) in cost.iteritems(): # Cost checking
					if game.main.session.world.player.inventory.get_value(key) + (settlement.inventory.get_value(key) if settlement else self.ship.inventory.get_value(key)) < value:
						print "Warning: more ressources of #%i needed for building id '%i'. Storage %i < %i" % (key, self._class.id, game.main.session.world.player.inventory.get_value(key) + (settlement.inventory.get_value(key) if settlement else self.ship.inventory.get_value(key)), value)
						return False
				for xx in xrange(x, x + self._class.size[0]): # Blocked checking
					for yy in xrange(y, y + self._class.size[1]):
						tile = island.get_tile(xx, yy)
						if not tile or tile.blocked:
							return False
			else:
				print 'no settlement'
				return False
		else:
			print 'no island'
			return False

		return self.ship or island.get_settlement_at_position(x, y)

	def mouseMoved(self, evt):
		super(BuildingTool, self).mouseMoved(evt)
		pt = fife.ScreenPoint(evt.getX(), evt.getY())
		target_mapcoord = game.main.session.view.cam.toMapCoordinates(pt, False)
		target_mapcoord.x = int(target_mapcoord.x + 0.5)
		target_mapcoord.y = int(target_mapcoord.y + 0.5)
		target_mapcoord.z = 0
		l = fife.Location(game.main.session.view.layers[1])
		l.setMapCoordinates(target_mapcoord)
		self.previewInstance.setLocation(l)
		target_mapcoord.x = target_mapcoord.x + 1
		l.setMapCoordinates(target_mapcoord)
		self.previewInstance.setFacingLocation(l)
		target_mapcoord.x = target_mapcoord.x - 1

		can_build = self._buildCheck(target_mapcoord.x, target_mapcoord.y)
		color = (255, 255, 255) if can_build else (255, 0, 0)
		game.main.session.view.renderer['InstanceRenderer'].addColored(self.previewInstance, *color)

		evt.consume()

	def onEscape(self):
		game.main.session.cursor = SelectionTool()

	def mousePressed(self, evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.onEscape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			pt = fife.ScreenPoint(evt.getX(), evt.getY())
			mapcoord = game.main.session.view.cam.toMapCoordinates(pt, False)
			mapcoord.x = int(mapcoord.x + 0.5)
			mapcoord.y = int(mapcoord.y + 0.5)
			mapcoord.z = 0
			if self._buildCheck(mapcoord.x, mapcoord.y):
				game.main.session.view.renderer['InstanceRenderer'].removeColored(self.previewInstance)
				game.main.session.manager.execute(Build(self._class, mapcoord.x, mapcoord.y, self.previewInstance, self.ship))
				self.previewInstance = None
				game.main.session.cursor = SelectionTool()
		evt.consume()
