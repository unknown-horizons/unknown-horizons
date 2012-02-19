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

import copy

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.constants import RES, BUILDINGS
from horizons.util.python import decorators
from horizons.util import Point

class AbstractFarm(AbstractBuilding):
	@property
	def directly_buildable(self):
		""" farms have to be triggered by fields """
		return False

	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		""" the fields have to take into account the farm cost """
		return 0

	@classmethod
	def get_purpose(cls, resource_id):
		if resource_id == RES.FOOD_ID:
			return BUILDING_PURPOSE.POTATO_FIELD
		elif resource_id == RES.WOOL_ID:
			return BUILDING_PURPOSE.PASTURE
		elif resource_id == RES.SUGAR_ID:
			return BUILDING_PURPOSE.SUGARCANE_FIELD
		elif resource_id == RES.TOBACCO_LEAVES_ID:
			return BUILDING_PURPOSE.TOBACCO_FIELD
		return None

	def get_evaluators(self, settlement_manager, resource_id):
		field_purpose = self.get_purpose(resource_id)
		road_side = [(-1, 0), (0, -1), (0, 3), (3, 0)]
		options = []

		# create evaluators for completely new farms
		most_fields = 1
		for x, y, orientation in self.iter_potential_locations(settlement_manager):
			# try the 4 road configurations (road through the farm area on any of the farm's sides)
			for road_dx, road_dy in road_side:
				evaluator = FarmEvaluator.create(settlement_manager.production_builder, x, y, road_dx, road_dy, most_fields, field_purpose)
				if evaluator is not None:
					options.append(evaluator)
					most_fields = max(most_fields, evaluator.fields)

		# create evaluators for modified farms (change unused field type)
		for coords_list in settlement_manager.production_builder.unused_fields.itervalues():
			for x, y in coords_list:
				evaluator = ModifiedFieldEvaluator.create(settlement_manager.production_builder, x, y, field_purpose)
				if evaluator is not None:
					options.append(evaluator)
		return options

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.FARM_CLASS] = cls

class FarmEvaluator(BuildingEvaluator):
	__moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	__field_offsets = None

	def __init__(self, area_builder, builder, value, farm_plan, fields, field_purpose):
		super(FarmEvaluator, self).__init__(area_builder, builder, value)
		self.farm_plan = farm_plan
		self.fields = fields
		self.field_purpose = field_purpose

	@classmethod
	def init_field_offsets(cls):
		# right next to the farm
		first_class = [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]
		# offset by a road right next to the farm
		second_class = [(-4, -3), (-4, 0), (-4, 3), (-3, -4), (-3, 4), (0, -4), (0, 4), (3, -4), (3, 4), (4, -3), (4, 0), (4, 3)]
		# offset by crossing roads
		third_class = [(-4, -4), (-4, 4), (4, -4), (4, 4)]
		cls.__field_offsets = first_class + second_class + third_class

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
		for (dx, dy) in cls.__field_offsets:
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

			for dx, dy in cls.__moves:
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
		value = fields + existing_roads * personality.existing_road_importance + \
			alignment * personality.alignment_importance - extra_space * personality.wasted_space_penalty + \
			immediate_connections * personality.immediate_connection_importance
		return FarmEvaluator(area_builder, builder, value, farm_plan, fields, field_purpose)

	__cache = {}
	__cache_changes = (-1, -1)

	@classmethod
	def create(cls, area_builder, farm_x, farm_y, road_dx, road_dy, min_fields, field_purpose):
		new_cache_changes = (area_builder.island.last_change_id, area_builder.last_change_id)
		if new_cache_changes != cls.__cache_changes:
			cls.__cache_changes = new_cache_changes
			cls.__cache.clear()
		key = (area_builder.owner, farm_x, farm_y, road_dx, road_dy)
		if key not in cls.__cache:
			cls.__cache[key] = cls._create(area_builder, farm_x, farm_y, road_dx, road_dy, min_fields, field_purpose)
		if cls.__cache[key] is None:
			return None
		if cls.__cache[key].field_purpose != field_purpose:
			return cls.__cache[key].__get_copy(field_purpose)
		return cls.__cache[key]

	def __get_copy(self, new_field_purpose):
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
		return (BUILD_RESULT.OK, building)

	@classmethod
	def clear_cache(cls):
		cls.__cache.clear()
		cls.__cache_changes = (-1, -1)

class ModifiedFieldEvaluator(BuildingEvaluator):
	"""This evaluator evaluates the cost of changing the type of an unused field."""

	def __init__(self, area_builder, builder, value, old_field_purpose):
		super(ModifiedFieldEvaluator, self).__init__(area_builder, builder, value)
		self._old_field_purpose = old_field_purpose
		self.fields = 1 # required for comparison with FarmEvalutor-s

	@classmethod
	def create(cls, area_builder, x, y, new_field_purpose):
		building_id = None
		if new_field_purpose == BUILDING_PURPOSE.POTATO_FIELD:
			building_id = BUILDINGS.POTATO_FIELD_CLASS
		elif new_field_purpose == BUILDING_PURPOSE.PASTURE:
			building_id = BUILDINGS.PASTURE_CLASS
		elif new_field_purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
			building_id = BUILDINGS.SUGARCANE_FIELD_CLASS
		elif new_field_purpose == BUILDING_PURPOSE.TOBACCO_FIELD:
			building_id = BUILDINGS.TOBACCO_FIELD_CLASS
		builder = Builder.create(building_id, area_builder.land_manager, Point(x, y))
		if not builder:
			return None

		value = 0
		personality = area_builder.owner.personality_manager.get('ModifiedFieldEvaluator')
		if new_field_purpose == BUILDING_PURPOSE.POTATO_FIELD:
			value += personality.add_potato_field_value
		elif new_field_purpose == BUILDING_PURPOSE.PASTURE:
			value += personality.add_pasture_value
		elif new_field_purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
			value += personality.add_sugarcane_field_value
		elif new_field_purpose == BUILDING_PURPOSE.TOBACCO_FIELD:
			value += personality.add_tobacco_field_value

		old_field_purpose = area_builder.plan[(x, y)][0]
		if old_field_purpose == BUILDING_PURPOSE.POTATO_FIELD:
			value -= personality.remove_unused_potato_field_penalty
		elif old_field_purpose == BUILDING_PURPOSE.PASTURE:
			value -= personality.remove_unused_pasture_penalty
		elif old_field_purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
			value -= personality.remove_unused_sugarcane_field_penalty
		elif old_field_purpose == BUILDING_PURPOSE.TOBACCO_FIELD:
			value -= personality.remove_unused_tobacco_field_penalty
		return ModifiedFieldEvaluator(area_builder, builder, value, old_field_purpose)

	def execute(self):
		if not self.builder.have_resources():
			return (BUILD_RESULT.NEED_RESOURCES, None)

		building = self.builder.execute()
		if not building:
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)

		# remove the old designation
		self.area_builder.unused_fields[self._old_field_purpose].remove(self.builder.point.to_tuple())

		return (BUILD_RESULT.OK, building)

AbstractFarm.register_buildings()
FarmEvaluator.init_field_offsets()

decorators.bind_all(AbstractFarm)
decorators.bind_all(FarmEvaluator)
decorators.bind_all(ModifiedFieldEvaluator)
