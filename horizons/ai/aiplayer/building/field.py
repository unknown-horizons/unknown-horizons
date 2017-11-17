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

import math

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import BUILDINGS, RES


class AbstractField(AbstractBuilding):
	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		total_cost = 0
		extra_fields_needed = int(math.ceil(max(0.0, production_needed / self.get_expected_production_level(resource_id))))
		field_spots_available = len(settlement_manager.production_builder.unused_fields[self.get_purpose(resource_id)])
		if field_spots_available >= extra_fields_needed:
			return extra_fields_needed * self.get_expected_building_cost()
		else:
			total_cost += field_spots_available * self.get_expected_building_cost()
			extra_fields_needed -= field_spots_available

		fields_per_farm = AbstractBuilding.buildings[BUILDINGS.FARM].get_max_fields(settlement_manager)
		if fields_per_farm == 0:
			return 1e100

		# TODO: fix the resource gathering code to request resources in larger chunks so this hack doesn't have to be used
		# use fractional farm costs to give farms a chance to picked
		extra_farms_needed = float(extra_fields_needed) / fields_per_farm
		#extra_farms_needed = int(math.ceil(float(extra_fields_needed) / fields_per_farm))

		total_cost += self.get_expected_building_cost() * extra_fields_needed
		total_cost += AbstractBuilding.buildings[BUILDINGS.FARM].get_expected_building_cost() * extra_farms_needed
		return total_cost

	@classmethod
	def get_purpose(cls, resource_id):
		return {
			RES.POTATOES:       BUILDING_PURPOSE.POTATO_FIELD,
			RES.LAMB_WOOL:      BUILDING_PURPOSE.PASTURE,
			RES.RAW_SUGAR:      BUILDING_PURPOSE.SUGARCANE_FIELD,
			RES.TOBACCO_PLANTS: BUILDING_PURPOSE.TOBACCO_FIELD,
			RES.HERBS:          BUILDING_PURPOSE.HERBARY,
		}.get(resource_id)

	@classmethod
	def get_higher_level_resource(cls, resource_id):
		return {
			RES.POTATOES:       RES.FOOD,
			RES.LAMB_WOOL:      RES.WOOL,
			RES.RAW_SUGAR:      RES.SUGAR,
			RES.TOBACCO_PLANTS: RES.TOBACCO_LEAVES,
			RES.HERBS:          RES.MEDICAL_HERBS,
		}.get(resource_id)

	def build(self, settlement_manager, resource_id):
		production_builder = settlement_manager.production_builder
		purpose = self.get_purpose(resource_id)
		if not production_builder.unused_fields[purpose]:
			return (BUILD_RESULT.NEED_PARENT_FIRST, None)
		if not self.have_resources(settlement_manager):
			return (BUILD_RESULT.NEED_RESOURCES, None)

		assert production_builder.unused_fields[purpose], 'expected field spot to be available'
		coords = production_builder.unused_fields[purpose][0]
		building = BasicBuilder(self.id, coords, 0).execute(settlement_manager.land_manager)
		assert building

		production_builder.unused_fields[purpose].popleft()
		production_builder.register_change_list([coords], purpose, None)
		return (BUILD_RESULT.OK, building)

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.POTATO_FIELD] = cls
		cls._available_buildings[BUILDINGS.PASTURE] = cls
		cls._available_buildings[BUILDINGS.SUGARCANE_FIELD] = cls
		cls._available_buildings[BUILDINGS.TOBACCO_FIELD] = cls
		cls._available_buildings[BUILDINGS.HERBARY] = cls


AbstractField.register_buildings()
