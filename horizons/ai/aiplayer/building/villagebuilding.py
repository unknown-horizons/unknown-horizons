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
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import RES, BUILDINGS
from horizons.util.python import decorators
from horizons.entities import Entities

class AbstractVillageBuilding(AbstractBuilding):
	@classmethod
	def get_purpose(cls, resource_id):
		if resource_id == RES.FAITH_ID:
			return BUILDING_PURPOSE.PAVILION
		elif resource_id == RES.EDUCATION_ID:
			return BUILDING_PURPOSE.VILLAGE_SCHOOL
		elif resource_id == RES.GET_TOGETHER_ID:
			return BUILDING_PURPOSE.TAVERN
		elif resource_id == RES.COMMUNITY_ID:
			return BUILDING_PURPOSE.MAIN_SQUARE
		return None

	def in_settlement(self, settlement_manager, position):
		for coords in position.tuple_iter():
			if coords not in settlement_manager.settlement.ground_map:
				return False
		return True

	def _need_producer(self, settlement_manager, coords, resource_id):
		if not settlement_manager.settlement.count_buildings(BUILDING_PURPOSE.get_building(self.get_purpose(resource_id))):
			return True # if none exist and we need the resource then build it
		assigned_residences = settlement_manager.village_builder.special_building_assignments[self.get_purpose(resource_id)][coords]
		total = len(assigned_residences)
		not_serviced = 0
		for residence_coords in assigned_residences:
			if settlement_manager.village_builder.plan[residence_coords][0] != BUILDING_PURPOSE.RESIDENCE:
				continue
			not_serviced += 1

		if not_serviced > 0 and not_serviced >= total * settlement_manager.owner.personality_manager.get('AbstractVillageBuilding').fraction_of_assigned_residences_built:
			return True
		return False

	def build(self, settlement_manager, resource_id):
		village_builder = settlement_manager.village_builder
		building_purpose = self.get_purpose(resource_id)

		for coords, (purpose, (section, _)) in village_builder.plan.iteritems():
			if section > village_builder.current_section or purpose != building_purpose:
				continue

			object = village_builder.land_manager.island.ground_map[coords].object
			if object is not None and object.id == self.id:
				continue

			if building_purpose != BUILDING_PURPOSE.MAIN_SQUARE:
				if not self._need_producer(settlement_manager, coords, resource_id):
					continue

			builder = village_builder.make_builder(BUILDING_PURPOSE.get_building(purpose), coords[0], coords[1], False)
			if not builder.have_resources():
				return (BUILD_RESULT.NEED_RESOURCES, None)
			if not self.in_settlement(settlement_manager, builder.position):
				return (BUILD_RESULT.OUT_OF_SETTLEMENT, builder.position)

			building = builder.execute()
			if not building:
				return (BUILD_RESULT.UNKNOWN_ERROR, None)
			if self.get_purpose(resource_id) == BUILDING_PURPOSE.MAIN_SQUARE and not village_builder.roads_built:
				village_builder.build_roads()
			return (BUILD_RESULT.OK, building)
		return (BUILD_RESULT.SKIP, None)

	def need_to_build_more_buildings(self, settlement_manager, resource_id):
		village_builder = settlement_manager.village_builder
		building_purpose = self.get_purpose(resource_id)

		for coords, (purpose, (section, _)) in village_builder.plan.iteritems():
			if section > village_builder.current_section:
				continue
			if purpose == building_purpose:
				object = village_builder.land_manager.island.ground_map[coords].object
				if object is None or object.id != self.id:
					if building_purpose != BUILDING_PURPOSE.MAIN_SQUARE:
						if not self._need_producer(settlement_manager, coords, resource_id):
							continue
					return True
		return False

	@property
	def coverage_building(self):
		""" main squares, pavilions, schools, and taverns are buildings that need to be built even if the total production is enough """
		return True

	def _get_producer_building(self):
		# TODO: remove this hack; introduced to battle the community Production moving from main squares to the warehouse
		if self.id == BUILDINGS.MAIN_SQUARE_CLASS:
			return Entities.buildings[BUILDINGS.WAREHOUSE_CLASS]
		return super(AbstractVillageBuilding, self)._get_producer_building()

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.MAIN_SQUARE_CLASS] = cls
		cls._available_buildings[BUILDINGS.PAVILION_CLASS] = cls
		cls._available_buildings[BUILDINGS.VILLAGE_SCHOOL_CLASS] = cls
		cls._available_buildings[BUILDINGS.TAVERN_CLASS] = cls

AbstractVillageBuilding.register_buildings()

decorators.bind_all(AbstractVillageBuilding)
