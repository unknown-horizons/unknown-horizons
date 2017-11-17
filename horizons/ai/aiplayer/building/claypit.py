# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, RES
from horizons.entities import Entities


class AbstractClayPit(AbstractBuilding):
	def iter_potential_locations(self, settlement_manager):
		building_class = Entities.buildings[BUILDINGS.CLAY_PIT]
		for building in settlement_manager.settlement.buildings_by_id.get(BUILDINGS.CLAY_DEPOSIT, []):
			if building.get_component(StorageComponent).inventory[RES.RAW_CLAY]:
				coords = building.position.origin.to_tuple()
				if coords in settlement_manager.production_builder.simple_collector_area_cache.cache[building_class.size]:
					yield (coords[0], coords[1], 0)

	@property
	def evaluator_class(self):
		return ClayPitEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.CLAY_PIT] = cls


class ClayPitEvaluator(BuildingEvaluator):
	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = BasicBuilder.create(BUILDINGS.CLAY_PIT, (x, y), orientation)
		distance_to_collector = cls._distance_to_nearest_collector(area_builder, builder, False)
		value = 1.0 / (distance_to_collector + 1)
		return ClayPitEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.CLAY_PIT


AbstractClayPit.register_buildings()
