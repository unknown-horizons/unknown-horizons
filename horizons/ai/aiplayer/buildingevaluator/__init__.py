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

from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.entities import Entities
from horizons.util import WorldObject
from horizons.constants import BUILDINGS

class BuildingEvaluator(WorldObject):
	def __init__(self, area_builder, builder, worldid=None):
		super(BuildingEvaluator, self).__init__(worldid)
		self.area_builder = area_builder
		self.builder = builder

	@classmethod
	def _weighted_sum(cls, main_component, other_components):
		"""
		Returns the weights sum of the components where the specified amount is given to an element of other_components unless it is None
		@param main_component: float
		@param other_components: list[(weight, value)] where weight is a float and value is either None or a float
		"""
		others = 0.0
		for weight, value in other_components:
			if value is not None:
				others += weight
		result = (1 - others) * main_component
		for weight, value in other_components:
			if value is not None:
				result += weight * value
		return result

	@classmethod
	def distance_to_nearest_building(cls, area_builder, builder, building_id):
		"""
		Returns the shortest distance to a building of type building_id that is in range of the builder
		@param area_builder: AreaBuilder
		@param builder: Builder
		@param building_id: int, the id of the building to which the distance should be measured
		"""

		shortest_distance = None
		for building in area_builder.settlement.get_buildings_by_id(building_id):
			distance = builder.position.distance(building.position)
			if distance <= Entities.buildings[builder.building_id].radius:
				shortest_distance = distance if shortest_distance is None or distance < shortest_distance else shortest_distance
		return shortest_distance

	@classmethod
	def distance_to_nearest_collector(cls, production_builder, builder):
		"""
		Returns the shortest distance to a collector that is in range of the builder
		@param production_builder: ProductionBuilder
		@param builder: Builder
		"""

		shortest_distance = None
		for building in production_builder.collector_buildings:
			distance = builder.position.distance(building.position)
			if distance <= Entities.buildings[builder.building_id].radius:
				shortest_distance = distance if shortest_distance is None or distance < shortest_distance else shortest_distance
		return shortest_distance

	@classmethod
	def _get_outline_coords(cls, coords_list):
		"""
		returns the coordinates that surround the given coordinates (no corners)
		"""
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		if not isinstance(coords_list, set):
			coords_list = set(coords_list)

		result = set()
		for x, y in coords_list:
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords not in coords_list:
					result.add(coords)
		return result

	@classmethod
	def get_alignment(cls, area_builder, coords_list):
		alignment = 0
		for coords in cls._get_outline_coords(coords_list):
			if coords in area_builder.plan:
				purpose = area_builder.plan[coords]
				if purpose == BUILDING_PURPOSE.NONE:
					continue
				elif purpose == BUILDING_PURPOSE.ROAD:
					alignment += 3
				else:
					alignment += 1
			elif coords in area_builder.settlement.ground_map:
				object = area_builder.settlement.ground_map[coords].object
				if object is not None and object.id == BUILDINGS.TRAIL_CLASS:
					alignment += 3
				else:
					alignment += 1
			else:
				alignment += 1
		return alignment

	def __cmp__(self, other):
		if abs(self.value - other.value) > 1e-9:
			return 1 if self.value < other.value else -1
		return self.builder.worldid - other.builder.worldid

	@property
	def purpose(self):
		raise NotImplementedError, 'This function has to be overridden.'

	def execute(self):
		if not self.builder.have_resources():
			return (BUILD_RESULT.NEED_RESOURCES, None)
		if not self.area_builder._build_road_connection(self.builder):
			return (BUILD_RESULT.IMPOSSIBLE, None)
		building = self.builder.execute()
		if not building:
			return (BUILD_RESULT.UNKNOWN_ERROR, None)
		for coords in self.builder.position.tuple_iter():
			self.area_builder.plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
		self.area_builder.plan[sorted(self.builder.position.tuple_iter())[0]] = (self.purpose, self.builder)
		self.area_builder.production_buildings.append(building)
		return (BUILD_RESULT.OK, building)

decorators.bind_all(BuildingEvaluator)
