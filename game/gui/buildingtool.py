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
from game.command.building import Build, Settle

import fife
import game.main

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class BuildingTool(NavigationTool):
	"""@param building_id: rowid of the selected building type"
	@param player_id: player id of the player that builds the building
	@param ship: If building from a ship, restrict to range of ship
	@param settle: bool Tells the building tool if a new settlement is created. Default: False
	"""

	def __init__(self, building_id, player_id, ship = None):
		print "Created buildingtool."
		super(BuildingTool, self).__init__()

		self.player_id = player_id
		self.ship = ship
		self.building_id = building_id

		self._class = game.main.session.entities.buildings[building_id]

		self.previewInstance = self._class.createInstance(-100, -100)

		game.main.onEscape = self.onEscape

	def __del__(self):
		super(BuildingTool, self).__del__()
		print 'deconstruct',self

	def _buildCheck(self,  position):
		# TODO: Return more detailed error descriptions than a boolean
		try:
			cost = self._class.calcBuildingCost(game.main.session.view.layers[0],  game.main.session.view.layers[1],  position)
			# TODO: implement cost checking
			# if cost < depot(nearest_island or ship):BlockedError
		except BlockedError:
			return False

		if self.ship:
			shippos = self.ship._instance.getLocation().getMapCoordinates()
			distance = (shippos - position).length()
			if distance > 10:
				return False

		island = game.main.session.world.get_island(position.x, position.y)
		if island:
			for i in range(0, self._class.size[0]):
				startx = position.x - self._class.size[0]/2 + i
				for b in range(0, self._class.size[1]):
					starty = position.y - self._class.size[1]/2 + b
					tile = island.get_tile(startx, starty)
					if not tile or tile.blocked:
						return False
		else:
			return False

		return self.ship or island.get_settlement_at_position(position.x, position.y)

	def mouseMoved(self,  evt):
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

		can_build = self._buildCheck(target_mapcoord)
		color = (255, 255, 255) if can_build else (255, 0, 0)
		game.main.session.view.renderer['InstanceRenderer'].addColored(self.previewInstance, *color)

		evt.consume()

	def onEscape(self):
		game.main.session.cursor = SelectionTool()
		game.main.session.view.layers[1].deleteInstance(self.previewInstance)

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.onEscape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			pt = fife.ScreenPoint(evt.getX(), evt.getY())
			mapcoord = game.main.session.view.cam.toMapCoordinates(pt, False)
			mapcoord.x = int(mapcoord.x + 0.5)
			mapcoord.y = int(mapcoord.y + 0.5)
			mapcoord.z = 0
			if self._buildCheck(mapcoord):
				island = game.main.session.world.get_island(mapcoord.x, mapcoord.y)
				game.main.session.view.renderer['InstanceRenderer'].removeColored(self.previewInstance)
				if self.ship:
					game.main.session.manager.execute(Settle(self._class, mapcoord.x, mapcoord.y, island.id, self.player_id, self.previewInstance))
				else:
					game.main.session.manager.execute(Build(self._class, mapcoord.x, mapcoord.y, island.id, self.player_id, self.previewInstance))
				game.main.session.cursor = SelectionTool()
		evt.consume()
