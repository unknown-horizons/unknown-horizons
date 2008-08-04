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

from building import Building, Selectable
from buildable import BuildableSingle
from game.world.consumer import Consumer
from game.world.provider import Provider
from game.gui.tabwidget import TabWidget
from game.util import Point
import game.main

class StorageBuilding(Selectable, BuildableSingle, Consumer, Provider, Building):
	"""Building that gets pickups and provides them for anyone
	Inherited eg. by branch office, storage tent
	"""
	def __init__(self, x, y, owner, instance = None, **kwargs):
		print self.__class__.__mro__
		super(StorageBuilding, self).__init__(x = x, y = y, owner = owner, instance = instance, **kwargs)
		self.inventory = self.settlement.inventory
		self.inventory.addChangeListener(self._changed)

	def create_carriage(self):
		# reset to unit 8, as soon as pathfinding over streets is implemented
		#self._Consumer__local_carriages.append(game.main.session.entities.units[8](self))
		self._Consumer__local_carriages.append(game.main.session.entities.units[2](self))

	def select(self):
		"""Runs neccesary steps to select the unit."""
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		for tile in self.island.grounds:
			if tile.settlement == self.settlement and any(x in tile.__class__.classes for x in ('constructible', 'coastline')):
				game.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, 255, 255, 255)
				if tile.object is not None:
					game.main.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)

	def show_menu(self):
		game.main.session.ingame_gui.show_menu(TabWidget(2, self))

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		game.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		game.main.session.view.renderer['InstanceRenderer'].removeAllColored()

class BranchOffice(StorageBuilding):
	@classmethod
	def isSettlementBuildRequirementSatisfied(cls, x, y, island, ship, **state):
		settlements = island.get_settlements(x, y, x + cls.size[0] - 1, y + cls.size[1] - 1)
		#if multi branch office allowed:
		#if len(settlements) == 1:
		#	return settlements.pop()
		if len(settlements) != 0:
			return None
		#ship check
		if (max(x - ship.position.x, 0, ship.position.x - x - cls.size[0] + 1) ** 2) + (max(y - ship.position.y, 0, ship.position.y - y - cls.size[1] + 1) ** 2) > 25:
			return None
		return {'settlement' : None}

	@classmethod
	def isGroundBuildRequirementSatisfied(cls, x, y, island, **state):
		#todo: check cost line
		coast_tile_found = False
		for xx,yy in [ (xx,yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1]) ]:
			tile = island.get_tile(Point(xx,yy))
			classes = tile.__class__.classes
			if 'coastline' in classes:
				coast_tile_found = True
			elif 'constructible' not in classes:
				return None

		return {} if coast_tile_found else None
