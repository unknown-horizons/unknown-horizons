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

import copy

from horizons.util.python import decorators
from horizons.entities import Entities
from horizons.util import WorldObject
from horizons.constants import RES

class BuildingEvaluator(WorldObject):
	def __init__(self, production_builder, builder, worldid=None):
		super(BuildingEvaluator, self).__init__(worldid)
		self.production_builder = production_builder
		self.builder = builder

	def _get_costs(self):
		return copy.copy(Entities.buildings[self.builder.building_id].costs)

	def _get_running_costs(self):
		return copy.copy(Entities.buildings[self.builder.building_id].running_costs)

	def _get_land_area(self):
		""" Returns the amount of useful land used. """
		area = 0
		for coords in self.builder.position.tuple_iter():
			if coords in self.production_builder.plan:
				area += 1
		return area

	@property
	def preference_multiplier(self):
		return 1.0

	land_cost = 2
	running_cost = 50
	resource_cost = {RES.GOLD_ID: 1, RES.BOARDS_ID: 20, RES.TOOLS_ID: 50}

	def get_combined_cost(self, resource_limits):
		total = 0
		costs = self._get_costs()
		for resource_id, amount in costs.iteritems():
			total += self.resource_cost[resource_id] * amount
			if resource_id in resource_limits and amount > resource_limits[resource_id]:
				return None
		total += self.land_cost * self._get_land_area()
		total += self.running_cost * self._get_running_costs()
		return total

	def get_unit_cost(self, resource_id, resource_limits):
		expected_production_level = self.get_expected_production_level(resource_id)
		if abs(expected_production_level) < 1e-9:
			return None
		expected_production_level *= self.preference_multiplier
		return float(self.get_combined_cost(resource_limits)) / expected_production_level

	def __cmp__(self, other):
		if abs(self.value - other.value) > 1e-9:
			return 1 if self.value < other.value else -1
		return self.builder.worldid - other.builder.worldid

decorators.bind_all(BuildingEvaluator)
