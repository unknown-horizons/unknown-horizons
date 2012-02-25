# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.constants import BUILDINGS, RES
from horizons.util.python import decorators
from horizons.world.component.storagecomponent import StorageComponent

class AbstractIronMine(AbstractBuilding):
	def iter_potential_locations(self, settlement_manager):
		for building in settlement_manager.land_manager.settlement.buildings_by_id.get(BUILDINGS.MOUNTAIN_CLASS, []):
			if building.get_component(StorageComponent).inventory[RES.RAW_IRON_ID]:
				(x, y) = building.position.origin.to_tuple()
				for rotation in xrange(4):
					yield (x, y, rotation)

	@property
	def evaluator_class(self):
		return IronMineEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.IRON_MINE_CLASS] = cls

class IronMineEvaluator(BuildingEvaluator):
	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.IRON_MINE_CLASS, x, y, True, orientation)
		if not builder:
			return None
		return IronMineEvaluator(area_builder, builder, 0)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.IRON_MINE

AbstractIronMine.register_buildings()

decorators.bind_all(AbstractIronMine)
decorators.bind_all(IronMineEvaluator)
