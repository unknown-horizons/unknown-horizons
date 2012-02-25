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

import logging

from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.entities import Entities
from horizons.util import WorldObject

class BuildingEvaluator(WorldObject):
	"""Class representing a set of instructions for building a building complex along with its value."""

	log = logging.getLogger("ai.aiplayer.buildingevaluator")
	need_collector_connection = True

	def __init__(self, area_builder, builder, value):
		"""
		@param area_builder: the relevant AreaBuilder instance
		@param builder: Builder instance
		@param value: the value of the evaluator (bigger is better)
		"""

		super(BuildingEvaluator, self).__init__()
		self.area_builder = area_builder
		self.builder = builder
		self.value = value

	@classmethod
	def _weighted_distance(cls, main_component, other_components, none_value):
		"""
		Return the weights sum of the component distances with the specified weights.

		@param main_component: value of the main component
		@param other_components: list[(weight, value), ...] where weight is a float and value is either None or a float
		@param none_value: the penalty for None in place of a component value
		"""

		others = 0.0
		for weight, value in other_components:
			others += weight
		result = (1 - others) * (main_component if main_component is not None else none_value)
		for weight, value in other_components:
			if value is None:
				result += weight * none_value
			else:
				result += weight * value
		return result

	@classmethod
	def _distance_to_nearest_building(cls, area_builder, builder, building_id):
		"""
		Return the shortest distance to a building of type building_id that is in range of the builder.

		@param area_builder: AreaBuilder instance
		@param builder: Builder instance
		@param building_id: the building type id of the building to which the distance should be measured
		"""

		shortest_distance = None
		for building in area_builder.settlement.buildings_by_id.get(building_id, []):
			distance = builder.position.distance(building.position)
			if distance <= Entities.buildings[builder.building_id].radius:
				shortest_distance = distance if shortest_distance is None or distance < shortest_distance else shortest_distance
		return shortest_distance

	@classmethod
	def _distance_to_nearest_collector(cls, production_builder, builder, must_be_in_range = True):
		"""
		Return the shortest distance to a collector that (usually) has to be in range of the builder.

		@param production_builder: ProductionBuilder instance
		@param builder: Builder instance
		@param must_be_in_range: whether the building has to be in range of the builder
		"""

		shortest_distance = None
		for building in production_builder.collector_buildings:
			distance = builder.position.distance(building.position)
			if not must_be_in_range or distance <= Entities.buildings[builder.building_id].radius:
				shortest_distance = distance if shortest_distance is None or distance < shortest_distance else shortest_distance
		return shortest_distance

	@classmethod
	def _get_outline_coords_list(cls, coords_list):
		"""Return the list of coordinates that share sides the given coordinates list."""
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
	def _get_alignment_from_outline(cls, area_builder, outline_coords_list):
		"""Return an alignment value given the list of coordinates that form the outline of a shape."""
		personality = area_builder.owner.personality_manager.get('BuildingEvaluator')
		alignment = 0
		for coords in outline_coords_list:
			if coords in area_builder.land_manager.roads:
				alignment += personality.alignment_road
			elif coords in area_builder.plan:
				purpose = area_builder.plan[coords][0]
				if purpose != BUILDING_PURPOSE.NONE:
					alignment += personality.alignment_production_building
			elif coords in area_builder.settlement.ground_map:
				object = area_builder.settlement.ground_map[coords].object
				if object is not None and not object.buildable_upon:
					alignment += personality.alignment_other_building
			else:
				alignment += personality.alignment_edge
		return alignment

	@classmethod
	def _get_alignment(cls, area_builder, coords_list):
		"""Return an alignment value based on the outline of the given coordinates list."""
		return cls._get_alignment_from_outline(area_builder, cls._get_outline_coords_list(coords_list))

	def __lt__(self, other):
		if abs(self.value - other.value) > 1e-9:
			return self.value > other.value
		return self.worldid - other.worldid

	@property
	def purpose(self):
		"""Return the BUILDING_PURPOSE constant relevant to the builder."""
		raise NotImplementedError('This function has to be overridden.')

	def have_resources(self):
		"""Return None if the builder is unreachable by road, False if there are not enough resources, and True otherwise."""
		# check without road first because the road is unlikely to be the problem and pathfinding isn't cheap
		if not self.builder.have_resources():
			return False
		road_cost = self.area_builder.get_road_connection_cost(self.builder)
		if road_cost is None:
			return None
		return self.builder.have_resources(road_cost)

	def execute(self):
		"""Build the specified building complex. Return (BUILD_RESULT constant, building object)."""
		resource_check = self.have_resources()
		if resource_check is None:
			self.log.debug('%s, unable to reach by road', self)
			return (BUILD_RESULT.IMPOSSIBLE, None)
		elif not resource_check:
			return (BUILD_RESULT.NEED_RESOURCES, None)
		if self.need_collector_connection:
			assert self.area_builder.build_road_connection(self.builder)
		building = self.builder.execute()
		if not building:
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)
		for x, y in self.builder.position.tuple_iter():
			self.area_builder.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
		self.area_builder.register_change(self.builder.position.origin.x, self.builder.position.origin.y, self.purpose, None)
		return (BUILD_RESULT.OK, building)

	def __str__(self):
		return '%s at %d, %d with value %f' % (self.__class__.__name__, self.builder.point.x, self.builder.point.y, self.value)

decorators.bind_all(BuildingEvaluator)
