# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.ai.aiplayer.buildingevaluator.farmevaluator import FarmEvaluator
from horizons.constants import RES, BUILDINGS
from horizons.util.python import decorators

class AbstractFarm(AbstractBuilding):
	def get_expected_production_level(self, resource_id):
		return None

	@classmethod
	def get_purpose(cls, resource_id):
		if resource_id == RES.FOOD_ID:
			return PRODUCTION_PURPOSE.POTATO_FIELD
		elif resource_id == RES.WOOL_ID:
			return PRODUCTION_PURPOSE.PASTURE
		elif resource_id == RES.SUGAR_ID:
			return PRODUCTION_PURPOSE.SUGARCANE_FIELD
		return None

	def build(self, settlement_manager, resource_id):
		if not self.have_resources(settlement_manager):
			return BUILD_RESULT.NEED_RESOURCES

		unused_field_purpose = PRODUCTION_PURPOSE.get_unused_purpose(self.get_purpose(resource_id))
		road_side = [(-1, 0), (0, -1), (0, 3), (3, 0)]
		options = []

		most_fields = 1
		for x, y, orientation in self.iter_potential_locations(settlement_manager):
			# try the 4 road configurations (road through the farm area on any of the farm's sides)
			for road_dx, road_dy in road_side:
				evaluator = FarmEvaluator.create(settlement_manager.production_builder, x, y, road_dx, road_dy, most_fields, unused_field_purpose)
				if evaluator is not None:
					options.append(evaluator)
					most_fields = max(most_fields, evaluator.fields)

		for evaluator in sorted(options):
			return evaluator.execute()
		return BUILD_RESULT.IMPOSSIBLE

	@classmethod
	def register_buildings(cls):
		cls.available_buildings[BUILDINGS.FARM_CLASS] = cls

AbstractFarm.register_buildings()

decorators.bind_all(AbstractFarm)
