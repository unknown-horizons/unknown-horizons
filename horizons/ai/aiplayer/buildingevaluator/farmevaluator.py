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

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.util import Point

class FarmEvaluator(BuildingEvaluator):
	moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	field_offsets = None

	def __init__(self, area_builder, builder, farm_plan, fields, field_purpose, existing_roads, alignment, extra_space, immediate_connections):
		super(FarmEvaluator, self).__init__(area_builder, builder)
		self.farm_plan = farm_plan
		self.fields = fields
		self.field_purpose = field_purpose
		self.existing_roads = existing_roads
		self.alignment = alignment
		self.extra_space = extra_space
		self.immediate_connections = immediate_connections

		personality = area_builder.owner.personality_manager.get('FarmEvaluator')
		self.value = fields + existing_roads * personality.existing_road_importance + \
			alignment * personality.alignment_importance - extra_space * personality.wasted_space_penalty + \
			immediate_connections * personality.immediate_connection_importance

	@classmethod
	def _make_field_offsets(cls):
		# right next to the farm
		first_class = [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]
		# offset by a road right next to the farm
		second_class = [(-4, -3), (-4, 0), (-4, 3), (-3, -4), (-3, 4), (0, -4), (0, 4), (3, -4), (3, 4), (4, -3), (4, 0), (4, 3)]
		# offset by crossing roads
		third_class = [(-4, -4), (-4, 4), (4, -4), (4, 4)]
		first_class.extend(second_class)
		first_class.extend(third_class)
		return first_class

	@classmethod
	def _suitable_for_road(self, area_builder, coords):
		return coords in area_builder.land_manager.roads or (coords in area_builder.plan and area_builder.plan[coords][0] == BUILDING_PURPOSE.NONE)

	@classmethod
	def _create(cls, area_builder, farm_x, farm_y, road_dx, road_dy, min_fields, field_purpose):
		builder = area_builder.make_builder(BUILDINGS.FARM_CLASS, farm_x, farm_y, True)
		if not builder:
			return None

		farm_plan = {}

		# place the farm area road
		existing_roads = 0
		for other_offset in xrange(-3, 6):
			coords = None
			if road_dx == 0:
				coords = (farm_x + other_offset, farm_y + road_dy)
			else:
				coords = (farm_x + road_dx, farm_y + other_offset)
			if not cls._suitable_for_road(area_builder, coords):
				return None

			if coords in area_builder.plan and area_builder.plan[coords][0] == BUILDING_PURPOSE.NONE:
				road = Builder.create(BUILDINGS.TRAIL_CLASS, area_builder.land_manager, Point(coords[0], coords[1]))
				if road:
					farm_plan[coords] = (BUILDING_PURPOSE.ROAD, road)
				else:
					farm_plan = None
					break
			else:
				existing_roads += 1
		if farm_plan is None:
			return None # impossible to build some part of the road

		# place the fields
		fields = 0
		for (dx, dy) in cls.field_offsets:
			if fields >= 8:
				break # unable to place more anyway
			coords = (farm_x + dx, farm_y + dy)
			field = area_builder.make_builder(BUILDINGS.POTATO_FIELD_CLASS, coords[0], coords[1], False)
			if not field:
				continue
			for coords2 in field.position.tuple_iter():
				if coords2 in farm_plan:
					field = None
					break
			if field is None:
				continue # some part of the area is reserved for something else
			fields += 1
			for coords2 in field.position.tuple_iter():
				farm_plan[coords2] = (BUILDING_PURPOSE.RESERVED, None)
			farm_plan[coords] = (field_purpose, None)
		if fields < min_fields:
			return None # go for the most fields possible

		# add the farm itself to the plan
		for coords in builder.position.tuple_iter():
			farm_plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
		farm_plan[(farm_x, farm_y)] = (BUILDING_PURPOSE.FARM, builder)

		# calculate the alignment value and the rectangle that contains the whole farm
		alignment = 0
		min_x, max_x, min_y, max_y = None, None, None, None
		for x, y in farm_plan:
			min_x = x if min_x is None or min_x > x else min_x
			max_x = x if max_x is None or max_x < x else max_x
			min_y = y if min_y is None or min_y > y else min_y
			max_y = y if max_y is None or max_y < y else max_y

			for dx, dy in cls.moves:
				coords = (x + dx, y + dy)
				if coords in farm_plan:
					continue
				if coords not in area_builder.plan or area_builder.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

		# calculate the value of the farm road end points (larger is better)
		personality = area_builder.owner.personality_manager.get('FarmEvaluator')
		immediate_connections = 0
		for other_offset in [-4, 6]:
			if road_dx == 0:
				coords = (farm_x + other_offset, farm_y + road_dy)
			else:
				coords = (farm_x + road_dx, farm_y + other_offset)
			if coords in area_builder.land_manager.roads:
				immediate_connections += personality.immediate_connection_road
			elif coords in area_builder.plan:
				if area_builder.plan[coords][0] == BUILDING_PURPOSE.NONE:
					immediate_connections += personality.immediate_connection_free

		extra_space = (max_x - min_x + 1) * (max_y - min_y + 1) - 9 * (fields + 2)
		return FarmEvaluator(area_builder, builder, farm_plan, fields, field_purpose, existing_roads, alignment, extra_space, immediate_connections)

	cache = {}
	cache_changes = (-1, -1)

	@classmethod
	def create(cls, area_builder, farm_x, farm_y, road_dx, road_dy, min_fields, field_purpose):
		new_cache_changes = (area_builder.island.last_change_id, area_builder.last_change_id)
		if new_cache_changes != cls.cache_changes:
			cls.cache_changes = new_cache_changes
			cls.cache.clear()
		key = (area_builder.owner, farm_x, farm_y, road_dx, road_dy)
		if key not in cls.cache:
			cls.cache[key] = cls._create(area_builder, farm_x, farm_y, road_dx, road_dy, min_fields, field_purpose)
		if cls.cache[key] is None:
			return None
		if cls.cache[key].field_purpose != field_purpose:
			return cls.cache[key]._get_copy(field_purpose)
		return cls.cache[key]

	def _get_copy(self, new_field_purpose):
		""" Returns a copy of the evaluator with a different field purpose """
		evaluator = copy.copy(self)
		evaluator.farm_plan = copy.copy(evaluator.farm_plan)
		for coords, (purpose, builder) in evaluator.farm_plan.iteritems():
			if purpose == evaluator.field_purpose:
				evaluator.farm_plan[coords] = (new_field_purpose, builder)
		evaluator.field_purpose = new_field_purpose
		return evaluator

	def execute(self):
		# cheap resource check first, then pre-reserve the tiles and check again
		if not self.builder.have_resources():
			return (BUILD_RESULT.NEED_RESOURCES, None)

		backup = copy.copy(self.area_builder.plan)
		for (x, y), (purpose, builder) in self.farm_plan.iteritems():
			self.area_builder.register_change(x, y, purpose, None)

		resource_check = self.have_resources()
		if resource_check is None:
			self.area_builder.plan = backup
			self.log.debug('%s, unable to reach by road', self)
			return (BUILD_RESULT.IMPOSSIBLE, None)
		elif not resource_check:
			self.area_builder.plan = backup
			return (BUILD_RESULT.NEED_RESOURCES, None)
		assert self.area_builder.build_road_connection(self.builder)

		building = self.builder.execute()
		if not building:
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)
		for coords, (purpose, builder) in self.farm_plan.iteritems():
			if purpose == self.field_purpose:
				self.area_builder.unused_fields[self.field_purpose].append(coords)
		self.area_builder.production_buildings.append(building)
		return (BUILD_RESULT.OK, building)

FarmEvaluator.field_offsets = FarmEvaluator._make_field_offsets()

decorators.bind_all(FarmEvaluator)
