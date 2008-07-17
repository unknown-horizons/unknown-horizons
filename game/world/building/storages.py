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
from game.world.building.producer import Producer
from game.world.building.consumer import Consumer
from game.world.storage import Storage
from game.world.units.carriage import BuildingCarriage
from game.gui.tabwidget import TabWidget
import game.main

class StorageBuilding(Building, Selectable, BuildableSingle, Producer, Consumer):
	"""Building that gets pickups and provides them for anyone
	Inherited eg. by branch office, storage tent
	"""
	def __init__(self, x, y, owner, instance = None):
		self.local_carriages = []
		Building.__init__(self, x, y, owner, instance)
		self.inventory = self.settlement.inventory
		#self.inventory  = Storage()
		Producer.__init__(self)
		Consumer.__init__(self)

		# add extra carriage
		self.local_carriages.append(game.main.session.entities.units[2](self))

	def select(self):
		"""Runs neccesary steps to select the unit."""
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		for tile in self.island.grounds:
			if tile.settlement == self.settlement:
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
	def isSettlementBuildRequirementSatisfied(cls, x, y, island, **state):
		settlements = island.get_settlements(x, y, x + cls.size[0] - 1, y + cls.size[1] - 1)
		#if multi branch office allowed:
		#if len(settlements) == 1:
		#	return settlements.pop()
		if len(settlements) != 0:
			return None
		#todo: add ship check
		return {'settlement' : None}

	@classmethod
	def isGroundBuildRequirementSatisfied(cls, x, y, island, **state):
		#todo: check cost line
		return {}
