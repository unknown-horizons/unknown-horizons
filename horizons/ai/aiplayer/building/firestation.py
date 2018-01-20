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
from horizons.constants import BUILDINGS


class AbstractFireStation(AbstractBuilding):
	def iter_potential_locations(self, settlement_manager):
		spots_in_settlement = settlement_manager.settlement.buildability_cache.cache[(2, 2)]
		village_builder = settlement_manager.village_builder
		for coords in village_builder.special_building_assignments[BUILDING_PURPOSE.FIRE_STATION].keys():
			if coords not in spots_in_settlement or village_builder.plan[coords][1][0] > village_builder.current_section:
				continue
			object = settlement_manager.settlement.ground_map[coords].object
			if object is None or object.buildable_upon:
				yield (coords[0], coords[1], 0)

	@property
	def producer_building(self):
		"""Fire stations don't produce any resources."""
		return False

	@property
	def evaluator_class(self):
		return FireStationEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.FIRE_STATION] = cls


class FireStationEvaluator(BuildingEvaluator):
	need_collector_connection = False
	record_plan_change = False

	@classmethod
	def create(cls, production_builder, x, y, orientation):
		settlement_manager = production_builder.settlement_manager
		village_builder = settlement_manager.village_builder
		builder = BasicBuilder.create(BUILDINGS.FIRE_STATION, (x, y), orientation)

		assigned_residences = village_builder.special_building_assignments[BUILDING_PURPOSE.FIRE_STATION][(x, y)]
		total = len(assigned_residences)
		not_serviced = 0
		for residence_coords in assigned_residences:
			if village_builder.plan[residence_coords][0] == BUILDING_PURPOSE.RESIDENCE:
				not_serviced += 1

		if not_serviced <= 0 or not_serviced < total * settlement_manager.owner.personality_manager.get('AbstractFireStation').fraction_of_assigned_residences_built:
			return None

		return FireStationEvaluator(village_builder, builder, not_serviced)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.FIRE_STATION


AbstractFireStation.register_buildings()
