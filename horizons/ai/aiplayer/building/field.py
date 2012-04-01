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

import math

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import RES, BUILDINGS
from horizons.util import Point
from horizons.util.python import decorators

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

		evaluators = AbstractBuilding.buildings[BUILDINGS.FARM].get_evaluators(settlement_manager, self.get_higher_level_resource(resource_id))
		if not evaluators:
			return None

		evaluator = sorted(evaluators)[0]
		fields_per_farm = evaluator.fields
		# TODO: fix the resource gathering code to request resources in larger chunks so this hack doesn't have to be used
		# use fractional farm costs to give farms a chance to picked
		extra_farms_needed = float(extra_fields_needed) / fields_per_farm
		#extra_farms_needed = int(math.ceil(float(extra_fields_needed) / fields_per_farm))

		total_cost += self.get_expected_building_cost() * extra_fields_needed
		total_cost += AbstractBuilding.buildings[BUILDINGS.FARM].get_expected_building_cost() * extra_farms_needed
		return total_cost

	@classmethod
	def get_purpose(cls, resource_id):
		if resource_id == RES.POTATOES:
			return BUILDING_PURPOSE.POTATO_FIELD
		elif resource_id == RES.LAMB_WOOL:
			return BUILDING_PURPOSE.PASTURE
		elif resource_id == RES.RAW_SUGAR:
			return BUILDING_PURPOSE.SUGARCANE_FIELD
		elif resource_id == RES.TOBACCO_PLANTS:
			return BUILDING_PURPOSE.TOBACCO_FIELD
		return None

	@classmethod
	def get_higher_level_resource(cls, resource_id):
		if resource_id == RES.POTATOES:
			return RES.FOOD
		elif resource_id == RES.LAMB_WOOL:
			return RES.WOOL
		elif resource_id == RES.RAW_SUGAR:
			return RES.SUGAR
		elif resource_id == RES.TOBACCO_PLANTS:
			return RES.TOBACCO_LEAVES
		return None

	def build(self, settlement_manager, resource_id):
		production_builder = settlement_manager.production_builder
		purpose = self.get_purpose(resource_id)
		if not production_builder.unused_fields[purpose]:
			return (BUILD_RESULT.NEED_PARENT_FIRST, None)
		if not self.have_resources(settlement_manager):
			return (BUILD_RESULT.NEED_RESOURCES, None)

		assert len(production_builder.unused_fields[purpose]) > 0, 'expected field spot to be available'
		coords = production_builder.unused_fields[purpose][0]
		builder = Builder.create(self.id, settlement_manager.land_manager, Point(coords[0], coords[1]))
		building = builder.execute()
		if not building:
			return (BUILD_RESULT.UNKNOWN_ERROR, None)
		production_builder.unused_fields[purpose].popleft()
		production_builder.register_change(coords[0], coords[1], purpose, None)
		return (BUILD_RESULT.OK, building)

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.POTATO_FIELD] = cls
		cls._available_buildings[BUILDINGS.PASTURE] = cls
		cls._available_buildings[BUILDINGS.SUGARCANE_FIELD] = cls
		cls._available_buildings[BUILDINGS.TOBACCO_FIELD] = cls

AbstractField.register_buildings()

decorators.bind_all(AbstractField)
