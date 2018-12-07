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

from collections import defaultdict
from typing import Dict, List, Tuple

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import BUILDINGS, RES
from horizons.world.buildability.terraincache import TerrainRequirement


class FarmOptionCache:
	def __init__(self, settlement_manager):
		self.settlement_manager = settlement_manager
		abstract_farm = AbstractBuilding.buildings[BUILDINGS.FARM]
		self.field_spots_set = abstract_farm._get_buildability_intersection(settlement_manager, (3, 3), TerrainRequirement.LAND, False)
		self.farm_spots_set = self.field_spots_set.intersection(settlement_manager.production_builder.simple_collector_area_cache.cache[(3, 3)])
		self.road_spots_set = abstract_farm._get_buildability_intersection(settlement_manager, (1, 1), TerrainRequirement.LAND, False).union(settlement_manager.land_manager.roads)
		self.raw_options = self._get_raw_options(self.farm_spots_set, self.field_spots_set, self.road_spots_set)
		self.max_fields = self._get_max_fields()
		self._positive_alignment = None

	def _get_raw_options(self, farm_spots_set, field_spots_set, road_spots_set):
		field_row3 = {}
		field_col3 = {}

		for coords in farm_spots_set:
			x, y = coords
			row_score = 1
			if (x - 3, y) in field_spots_set:
				row_score += 1
			if (x + 3, y) in field_spots_set:
				row_score += 1
			field_row3[coords] = row_score

			col_score = 1
			if (x, y - 3) in field_spots_set:
				col_score += 1
			if (x, y + 3) in field_spots_set:
				col_score += 1
			field_col3[coords] = col_score

		road_row3 = set()
		road_col3 = set()
		for (x, y) in road_spots_set:
			if (x + 2, y) in road_spots_set and (x + 1, y) in road_spots_set:
				road_row3.add((x, y))
			if (x, y + 2) in road_spots_set and (x, y + 1) in road_spots_set:
				road_col3.add((x, y))

		road_row9 = set()
		for (x, y) in road_row3:
			if (x - 3, y) in road_row3 and (x + 3, y) in road_row3:
				road_row9.add((x, y))

		road_col9 = set()
		for (x, y) in road_col3:
			if (x, y - 3) in road_col3 and (x, y + 3) in road_col3:
				road_col9.add((x, y))

		raw_options = []
		for coords in sorted(farm_spots_set):
			x, y = coords

			row_score = field_row3[coords] - 1
			if (x, y - 1) in road_row9:
				score = row_score
				if (x, y - 4) in field_row3:
					score += field_row3[(x, y - 4)]
				if (x, y + 3) in field_row3:
					score += field_row3[(x, y + 3)]
				if score > 0:
					raw_options.append((score, coords, 0))
			if (x, y + 3) in road_row9:
				score = row_score
				if (x, y - 3) in field_row3:
					score += field_row3[(x, y - 3)]
				if (x, y + 4) in field_row3:
					score += field_row3[(x, y + 4)]
				if score > 0:
					raw_options.append((score, coords, 1))

			col_score = field_col3[coords] - 1
			if (x - 1, y) in road_col9:
				score = col_score
				if (x - 4, y) in field_col3:
					score += field_col3[(x - 4, y)]
				if (x + 3, y) in field_col3:
					score += field_col3[(x + 3, y)]
				if score > 0:
					raw_options.append((score, coords, 2))
			if (x + 3, y) in road_col9:
				score = col_score
				if (x - 3, y) in field_col3:
					score += field_col3[(x - 3, y)]
				if (x + 4, y) in field_col3:
					score += field_col3[(x + 4, y)]
				if score > 0:
					raw_options.append((score, coords, 3))

		return raw_options

	def _get_max_fields(self):
		max_fields = 0
		for (num_fields, _, _) in self.raw_options:
			if num_fields > max_fields:
				max_fields = num_fields
		return max_fields

	def get_positive_alignment(self):
		if self._positive_alignment is None:
			land_manager = self.settlement_manager.land_manager
			village_builder = self.settlement_manager.village_builder
			positive_alignment = land_manager.coastline.union(land_manager.roads, iter(village_builder.plan.keys()))
			production_builder_plan = self.settlement_manager.production_builder.plan
			for (coords, purpose) in production_builder_plan:
				if purpose != BUILDING_PURPOSE.NONE:
					positive_alignment.add(coords)
			self._positive_alignment = positive_alignment
		return self._positive_alignment


class AbstractFarm(AbstractBuilding):
	@property
	def directly_buildable(self):
		""" farms have to be triggered by fields """
		return False

	@property
	def evaluator_class(self):
		return FarmEvaluator

	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		""" the fields have to take into account the farm cost """
		return 0

	@classmethod
	def get_purpose(cls, resource_id):
		return {
			RES.FOOD:           BUILDING_PURPOSE.POTATO_FIELD,
			RES.WOOL:           BUILDING_PURPOSE.PASTURE,
			RES.SUGAR:          BUILDING_PURPOSE.SUGARCANE_FIELD,
			RES.TOBACCO_LEAVES: BUILDING_PURPOSE.TOBACCO_FIELD,
			RES.HERBS:          BUILDING_PURPOSE.HERBARY,
		}.get(resource_id)

	def get_evaluators(self, settlement_manager, resource_id):
		options_cache = self._get_option_cache(settlement_manager)
		raw_options = options_cache.raw_options
		if not raw_options:
			return []

		farm_field_buckets = []
		for _ in range(9):
			farm_field_buckets.append([])

		for option in raw_options:
			farm_field_buckets[option[0]].append(option)

		personality = settlement_manager.owner.personality_manager.get('FarmEvaluator')
		options_left = personality.max_options
		chosen_raw_options = []
		for i in range(8, 0, -1):
			if len(farm_field_buckets[i]) > options_left:
				chosen_raw_options.extend(settlement_manager.session.random.sample(farm_field_buckets[i], options_left))
				options_left = 0
			else:
				chosen_raw_options.extend(farm_field_buckets[i])
				options_left -= len(farm_field_buckets[i])
			if options_left == 0:
				break

		max_fields = options_cache.max_fields
		field_spots_set = options_cache.field_spots_set
		road_spots_set = options_cache.road_spots_set
		positive_alignment = options_cache.get_positive_alignment()
		production_builder = settlement_manager.production_builder
		field_purpose = self.get_purpose(resource_id)
		road_configs = [(0, -1), (0, 3), (-1, 0), (3, 0)]
		options = []

		# create evaluators for completely new farms
		for (_, (x, y), road_config) in chosen_raw_options:
			road_dx, road_dy = road_configs[road_config]
			evaluator = FarmEvaluator.create(production_builder, x, y, road_dx, road_dy, max_fields, field_purpose, field_spots_set, road_spots_set, positive_alignment)
			if evaluator is not None:
				options.append(evaluator)

		# create evaluators for modified farms (change unused field type)
		for coords_list in production_builder.unused_fields.values():
			for x, y in coords_list:
				evaluator = ModifiedFieldEvaluator.create(production_builder, x, y, field_purpose)
				if evaluator is not None:
					options.append(evaluator)
		return options

	__cache = {} # type: Dict[int, Tuple[Tuple[int, int], FarmOptionCache]]

	def _get_option_cache(self, settlement_manager):
		production_builder = settlement_manager.production_builder
		current_cache_changes = (production_builder.island.last_change_id, production_builder.last_change_id)

		worldid = settlement_manager.worldid
		if worldid in self.__cache and self.__cache[worldid][0] != current_cache_changes:
			del self.__cache[worldid]

		if worldid not in self.__cache:
			self.__cache[worldid] = (current_cache_changes, FarmOptionCache(settlement_manager))
		return self.__cache[worldid][1]

	@classmethod
	def clear_cache(cls):
		cls.__cache.clear()

	def get_max_fields(self, settlement_manager):
		return self._get_option_cache(settlement_manager).max_fields

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.FARM] = cls


class FarmEvaluator(BuildingEvaluator):
	__field_pos_offsets = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
	__moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	__field_offsets = None # type: List[Tuple[int, int]]

	__slots__ = ('farm_plan', 'field_purpose')

	def __init__(self, area_builder, builder, value, farm_plan, fields, field_purpose):
		super().__init__(area_builder, builder, value)
		self.farm_plan = farm_plan
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
	def _suitable_for_road(cls, production_builder, coords):
		"""check coordinates"""
		return coords in production_builder.land_manager.roads or (
			coords in production_builder.plan and
			production_builder.plan[coords][0] == BUILDING_PURPOSE.NONE)

	@classmethod
	def create(cls, area_builder, farm_x, farm_y, road_dx, road_dy, min_fields, field_purpose, field_spots_set, road_spots_set, positive_alignment):
		farm_plan = {}

		# place the farm area road
		existing_roads = 0
		for other_offset in range(-3, 6):
			coords = None
			if road_dx == 0:
				coords = (farm_x + other_offset, farm_y + road_dy)
			else:
				coords = (farm_x + road_dx, farm_y + other_offset)
			assert coords in road_spots_set

			farm_plan[coords] = BUILDING_PURPOSE.ROAD
			if coords in area_builder.land_manager.roads:
				existing_roads += 1

		# place the fields
		fields = 0
		for (dx, dy) in cls.__field_offsets:
			if fields >= 8:
				break # unable to place more anyway
			coords = (farm_x + dx, farm_y + dy)
			if coords not in field_spots_set:
				continue

			field_fits = True
			for (fdx, fdy) in cls.__field_pos_offsets:
				coords2 = (coords[0] + fdx, coords[1] + fdy)
				if coords2 in farm_plan:
					field_fits = False
					break
			if not field_fits:
				continue # some part of the area is reserved for something else

			fields += 1
			for (fdx, fdy) in cls.__field_pos_offsets:
				coords2 = (coords[0] + fdx, coords[1] + fdy)
				farm_plan[coords2] = BUILDING_PURPOSE.RESERVED
			farm_plan[coords] = field_purpose
		if fields < min_fields:
			return None # go for the most fields possible

		# add the farm itself to the plan
		builder = BasicBuilder.create(BUILDINGS.FARM, (farm_x, farm_y), 0)
		for coords in builder.position.tuple_iter():
			farm_plan[coords] = BUILDING_PURPOSE.RESERVED
		farm_plan[(farm_x, farm_y)] = BUILDING_PURPOSE.FARM

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
				if coords not in farm_plan and coords in positive_alignment:
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

	def _register_changes(self, changes, just_roads):
		for (purpose, data), coords_list in changes.items():
			if just_roads == (purpose == BUILDING_PURPOSE.ROAD):
				self.area_builder.register_change_list(coords_list, purpose, data)

	def execute(self):
		# cheap resource check first, then pre-reserve the tiles and check again
		if not self.builder.have_resources(self.area_builder.land_manager):
			return (BUILD_RESULT.NEED_RESOURCES, None)

		changes = defaultdict(list)
		reverse_changes = defaultdict(list)
		for coords, purpose in self.farm_plan.items():
			# completely ignore the road in the plan for now
			if purpose == BUILDING_PURPOSE.ROAD:
				continue
			assert coords not in self.area_builder.land_manager.roads

			changes[(purpose, None)].append(coords)
			reverse_changes[self.area_builder.plan[coords]].append(coords)
		self._register_changes(changes, False)

		resource_check = self.have_resources()
		if resource_check is None:
			self._register_changes(reverse_changes, False)
			self.log.debug('%s, unable to reach by road', self)
			return (BUILD_RESULT.IMPOSSIBLE, None)
		elif not resource_check:
			self._register_changes(reverse_changes, False)
			return (BUILD_RESULT.NEED_RESOURCES, None)
		assert self.area_builder.build_road_connection(self.builder)

		building = self.builder.execute(self.area_builder.land_manager)
		if not building:
			# TODO: make sure the plan and the reality stay in a reasonable state
			# the current code makes the plan look as if everything was built but in reality
			# a farm may be missing if there was not enough money after building the road.
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)

		for coords, purpose in self.farm_plan.items():
			if purpose == self.field_purpose:
				self.area_builder.unused_fields[self.field_purpose].append(coords)
		self._register_changes(changes, True)
		return (BUILD_RESULT.OK, building)


class ModifiedFieldEvaluator(BuildingEvaluator):
	"""This evaluator evaluates the cost of changing the type of an unused field."""

	__slots__ = ('_old_field_purpose')

	def __init__(self, area_builder, builder, value, old_field_purpose):
		super().__init__(area_builder, builder, value)
		self._old_field_purpose = old_field_purpose

	@classmethod
	def create(cls, area_builder, x, y, new_field_purpose):
		building_id = {
			BUILDING_PURPOSE.POTATO_FIELD:    BUILDINGS.POTATO_FIELD,
			BUILDING_PURPOSE.PASTURE:         BUILDINGS.PASTURE,
			BUILDING_PURPOSE.SUGARCANE_FIELD: BUILDINGS.SUGARCANE_FIELD,
			BUILDING_PURPOSE.TOBACCO_FIELD:   BUILDINGS.TOBACCO_FIELD,
			BUILDING_PURPOSE.HERBARY:         BUILDINGS.HERBARY,
		}.get(new_field_purpose)

		personality = area_builder.owner.personality_manager.get('ModifiedFieldEvaluator')
		value = {
			BUILDING_PURPOSE.POTATO_FIELD:    personality.add_potato_field_value,
			BUILDING_PURPOSE.PASTURE:         personality.add_pasture_value,
			BUILDING_PURPOSE.SUGARCANE_FIELD: personality.add_sugarcane_field_value,
			BUILDING_PURPOSE.TOBACCO_FIELD:   personality.add_tobacco_field_value,
			BUILDING_PURPOSE.HERBARY:         personality.add_herbary_field_value,
		}.get(new_field_purpose, 0)

		old_field_purpose = area_builder.plan[(x, y)][0]
		value -= {
			BUILDING_PURPOSE.POTATO_FIELD:    personality.remove_unused_potato_field_penalty,
			BUILDING_PURPOSE.PASTURE:         personality.remove_unused_pasture_penalty,
			BUILDING_PURPOSE.SUGARCANE_FIELD: personality.remove_unused_sugarcane_field_penalty,
			BUILDING_PURPOSE.TOBACCO_FIELD:   personality.remove_unused_tobacco_field_penalty,
			BUILDING_PURPOSE.HERBARY:         personality.remove_unused_herbary_field_penalty,
		}.get(old_field_purpose, 0)

		builder = BasicBuilder.create(building_id, (x, y), 0)
		return ModifiedFieldEvaluator(area_builder, builder, value, old_field_purpose)

	def execute(self):
		if not self.builder.have_resources(self.area_builder.land_manager):
			return (BUILD_RESULT.NEED_RESOURCES, None)

		building = self.builder.execute(self.area_builder.land_manager)
		if not building:
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)

		# remove the old designation
		self.area_builder.unused_fields[self._old_field_purpose].remove(self.builder.position.origin.to_tuple())

		return (BUILD_RESULT.OK, building)


AbstractFarm.register_buildings()
FarmEvaluator.init_field_offsets()
