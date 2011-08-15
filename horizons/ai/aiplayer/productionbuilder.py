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

import math
import copy
import itertools

from collections import deque, defaultdict

from areabuilder import AreaBuilder
from builder import Builder
from constants import BUILD_RESULT, BUILDING_PURPOSE
from building import AbstractBuilding

from horizons.constants import AI, BUILDINGS, RES, PRODUCTION
from horizons.scheduler import Scheduler
from horizons.util import Point, Rect
from horizons.util.python import decorators
from horizons.entities import Entities

class ProductionBuilder(AreaBuilder):
	def __init__(self, settlement_manager):
		super(ProductionBuilder, self).__init__(settlement_manager)
		self.plan = dict.fromkeys(self.land_manager.production, (BUILDING_PURPOSE.NONE, None))
		self.__init(settlement_manager, Scheduler().cur_tick, Scheduler().cur_tick)
		for x, y in settlement_manager.branch_office.position.tuple_iter():
			self.register_change(x, y, BUILDING_PURPOSE.BRANCH_OFFICE, None)

	def __init(self, settlement_manager, last_collector_improvement_storage, last_collector_improvement_road):
		self._init_cache()
		self.collector_buildings = [] # [building, ...]
		self.production_buildings = [] # [building, ...]
		self.unused_fields = self._make_empty_unused_fields()
		self.personality = self.owner.personality_manager.get('ProductionBuilder')
		self._last_collector_improvement_storage = last_collector_improvement_storage
		self._last_collector_improvement_road = last_collector_improvement_road

	@classmethod
	def _make_empty_unused_fields(self):
		return {
			BUILDING_PURPOSE.POTATO_FIELD: deque(),
			BUILDING_PURPOSE.PASTURE: deque(),
			BUILDING_PURPOSE.SUGARCANE_FIELD: deque(),
		}

	def save(self, db):
		super(ProductionBuilder, self).save(db)
		translated_last_collector_improvement_storage = self._last_collector_improvement_storage - Scheduler().cur_tick # pre-translate for the loading process
		translated_last_collector_improvement_road = self._last_collector_improvement_road - Scheduler().cur_tick # pre-translate for the loading process
		db("INSERT INTO ai_production_builder(rowid, settlement_manager, last_collector_improvement_storage, last_collector_improvement_road) VALUES(?, ?, ?, ?)", \
			self.worldid, self.settlement_manager.worldid, translated_last_collector_improvement_storage, translated_last_collector_improvement_road)

	def _load(self, db, settlement_manager):
		worldid, last_storage, last_road = \
			db("SELECT rowid, last_collector_improvement_storage, last_collector_improvement_road FROM ai_production_builder WHERE settlement_manager = ?", \
			settlement_manager.worldid)[0]
		super(ProductionBuilder, self)._load(db, settlement_manager, worldid)
		self.__init(settlement_manager, last_storage, last_road)

		db_result = db("SELECT x, y, purpose, builder FROM ai_area_builder_plan WHERE area_builder = ?", worldid)
		for x, y, purpose, builder_id in db_result:
			builder = Builder.load(db, builder_id, self.land_manager) if builder_id else None
			self.plan[(x, y)] = (purpose, builder)
			object = self.island.ground_map[(x, y)].object
			if object is None:
				continue

			if purpose == BUILDING_PURPOSE.FISHER and object.id == BUILDINGS.FISHERMAN_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.LUMBERJACK and object.id == BUILDINGS.LUMBERJACK_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.FARM and object.id == BUILDINGS.FARM_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.CLAY_PIT and object.id == BUILDINGS.CLAY_PIT_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.BRICKYARD and object.id == BUILDINGS.BRICKYARD_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.WEAVER and object.id == BUILDINGS.WEAVER_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.DISTILLERY and object.id == BUILDINGS.DISTILLERY_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.IRON_MINE and object.id == BUILDINGS.IRON_MINE_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.SMELTERY and object.id == BUILDINGS.SMELTERY_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.TOOLMAKER and object.id == BUILDINGS.TOOLMAKER_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.CHARCOAL_BURNER and object.id == BUILDINGS.CHARCOAL_BURNER_CLASS:
				self.production_buildings.append(object)
			elif purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add((x, y))

		self.refresh_unused_fields()

	def build_boat_builder(self):
		return AbstractBuilding.buildings[BUILDINGS.BOATBUILDER_CLASS].build(self.settlement_manager, None)[0]

	def build_signal_fire(self):
		return AbstractBuilding.buildings[BUILDINGS.SIGNAL_FIRE_CLASS].build(self.settlement_manager, None)[0]

	def _near_collectors(self, position):
		for building in self.collector_buildings:
			if building.position.distance(position) <= building.radius:
				return True
		return False

	def _get_problematic_collector_coverage_buildings(self):
		problematic_buildings = {}
		for building in self.production_buildings:
			for production in building._get_productions():
				if production.get_age() < 1.5 * PRODUCTION.STATISTICAL_WINDOW:
					continue
				history = production.get_state_history_times(False)
				# take paused time into account because the AI pauses the production when the output storage is full
				amount_paused = history[PRODUCTION.STATES.inventory_full.index] + history[PRODUCTION.STATES.paused.index]
				if amount_paused < self.personality.min_bad_collector_coverage:
					continue
				for resource_id in production.get_produced_res():
					if self.settlement.inventory.get_free_space_for(resource_id) > self.personality.min_free_space:
						# this is actually problematic
						problematic_buildings[building.worldid] = building
		return problematic_buildings.values()

	def enough_collectors(self):
		if self._last_collector_improvement_road + self.personality.collector_improvement_road_expires > Scheduler().cur_tick:
			return True # skip this to leave time for the collectors to do their work

		problematic_buildings = self._get_problematic_collector_coverage_buildings()
		return not problematic_buildings

	def improve_collector_coverage(self):
		"""
		Builds a road to a collector building or an extra storage tent to improve collector coverage.
		"""
		current_tick = Scheduler().cur_tick

		# which collectors could have actual unused capacity?
		usable_collectors = []
		for building in self.collector_buildings:
			if building.get_utilisation_history_length() < 1000 or building.get_collector_utilisation() < self.personality.max_good_collector_utilisation:
				usable_collectors.append(building)

		# find possible problematic building to usable collector links
		problematic_buildings = self._get_problematic_collector_coverage_buildings()
		potential_road_connections = []
		for building in problematic_buildings:
			for collector_building in usable_collectors:
				distance = building.loading_area.distance(collector_building.position)
				if distance > collector_building.radius:
					continue # out of range anyway
				potential_road_connections.append((distance * collector_building.get_collector_utilisation(), building, collector_building))

		# try the best link from the above list
		for _, building, collector_building in sorted(potential_road_connections):
			result = self.build_extra_road_connection(building, collector_building)
			if result:
				self._last_collector_improvement_road = current_tick
				self.log.info('%s connected %s at %d, %d with %s at %d, %d', self, building.name, building.position.origin.x, \
					building.position.origin.y, collector_building.name, collector_building.position.origin.x, collector_building.position.origin.y)
				return BUILD_RESULT.OK
		self.log.info('%s found no good way to connect buildings that need more collectors to existing collector buildings', self)

		if not self.have_resources(BUILDINGS.STORAGE_CLASS):
			return BUILD_RESULT.NEED_RESOURCES
		if self._last_collector_improvement_storage + self.personality.collector_improvement_storage_expires > current_tick:
			return BUILD_RESULT.IMPOSSIBLE # skip this to leave time for the collectors to do their work

		reachable = dict.fromkeys(self.land_manager.roads) # {(x, y): [(building worldid, distance), ...], ...}
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose == BUILDING_PURPOSE.NONE:
				reachable[coords] = []
		for key in reachable:
			if reachable[key] is None:
				reachable[key] = []

		storage_radius = Entities.buildings[BUILDINGS.STORAGE_CLASS].radius
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		for building in problematic_buildings:
			distance = dict.fromkeys(reachable)
			queue = deque()
			for coords in self._get_possible_road_coords(building.loading_area, building.position):
				if coords in distance:
					distance[coords] = 0
					queue.append(coords)

			while queue:
				x, y = queue[0]
				queue.popleft()
				for dx, dy in moves:
					coords2 = (x + dx, y + dy)
					if coords2 in distance and distance[coords2] is None:
						distance[coords2] = distance[(x, y)] + 1
						queue.append(coords2)

			for coords, dist in distance.iteritems():
				if dist is not None:
					if building.loading_area.distance(coords) <= storage_radius:
						reachable[coords].append((building.worldid, dist))

		options = []
		for (x, y), building_distances in reachable.iteritems():
			builder = self.make_builder(BUILDINGS.STORAGE_CLASS, x, y, False)
			if not builder:
				continue

			actual_distance = {}
			for coords in builder.position.tuple_iter():
				for building_worldid, distance in reachable[coords]:
					if building_worldid not in actual_distance or actual_distance[building_worldid] > distance:
						actual_distance[building_worldid] = distance
			if not actual_distance:
				continue

			usefulness = min(len(actual_distance), self.personality.max_reasonably_served_buildings)
			for distance in actual_distance.itervalues():
				usefulness += 1.0 / (distance + self.personality.collector_extra_distance)

			alignment = 1
			for tile in self._get_neighbour_tiles(builder.position):
				if tile is None:
					continue
				coords = (tile.x, tile.y)
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			value = usefulness + alignment * self.personality.improved_collector_coverage_alignment_coefficient
			options.append((-value, builder))

		for _, builder in sorted(options):
			building = builder.execute()
			if not building:
				return BUILD_RESULT.UNKNOWN_ERROR
			for x, y in builder.position.tuple_iter():
				self.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
			self.register_change(builder.position.origin.x, builder.position.origin.y, BUILDING_PURPOSE.STORAGE, builder)
			self._last_collector_improvement_storage = current_tick
			return BUILD_RESULT.OK

		return BUILD_RESULT.IMPOSSIBLE

	def improve_deposit_coverage(self, building_id):
		"""
		Builds a storage tent to get settlement range closer to the resource deposit.
		"""
		if not self.have_resources(BUILDINGS.STORAGE_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		available_deposits = []
		for building in self.land_manager.resource_deposits[building_id]:
			if building.settlement is None:
				available_deposits.append(building)
		if not available_deposits:
			return BUILD_RESULT.IMPOSSIBLE

		options = []
		for (x, y), (purpose, _) in self.plan.iteritems():
			builder = self.make_builder(BUILDINGS.STORAGE_CLASS, x, y, False)
			if not builder:
				continue

			min_distance = None
			for building in available_deposits:
				distance = building.position.distance(builder.position)
				if min_distance is None or min_distance > distance:
					min_distance = distance

			alignment = 0
			for tile in self._get_neighbour_tiles(builder.position):
				if tile is None:
					continue
				coords = (tile.x, tile.y)
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			value = min_distance - alignment * self.personality.deposit_coverage_alignment_coefficient
			options.append((value, builder))

		for _, builder in sorted(options):
			building = builder.execute()
			if not building:
				return BUILD_RESULT.UNKNOWN_ERROR
			for x, y in builder.position.tuple_iter():
				self.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
			self.register_change(builder.position.origin.x, builder.position.origin.y, BUILDING_PURPOSE.STORAGE, builder)
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def _get_collector_area(self):
		""" returns the set of all coordinates that are reachable from at least one collector by road or open space """
		if self.__collector_area_cache is not None and self.last_change_id == self.__collector_area_cache[0]:
			return self.__collector_area_cache[1]

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		collector_area = set() # unused tiles that are reachable from at least one collector
		for building in self.collector_buildings:
			coverage_area = set()
			for coords in building.position.get_radius_coordinates(building.radius, True):
				coverage_area.add(coords)

			reachable = set()
			queue = deque()
			for coords in building.position.tuple_iter():
				reachable.add(coords)
				queue.append(coords)

			while queue:
				x, y = queue[0]
				queue.popleft()
				for dx, dy in moves:
					coords = (x + dx, y + dy)
					if coords not in reachable and coords in coverage_area:
						if coords in self.land_manager.roads or (coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE):
							queue.append(coords)
							reachable.add(coords)
							if coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE:
								collector_area.add(coords)
		self.__collector_area_cache = (self.last_change_id, collector_area)
		return collector_area

	def enlarge_collector_area(self):
		if not self.have_resources(BUILDINGS.STORAGE_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		collector_area = self._get_collector_area()

		# area_label contains free tiles in the production area and all road tiles
		area_label = dict.fromkeys(self.land_manager.roads) # {(x, y): area_number, ...}
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose == BUILDING_PURPOSE.NONE:
				area_label[coords] = None
		areas = 0
		for coords in collector_area:
			if coords in area_label and area_label[coords] is not None:
				continue

			queue = deque([coords])
			while queue:
				x, y = queue[0]
				queue.popleft()
				for dx, dy in moves:
					coords2 = (x + dx, y + dy)
					if coords2 in area_label and area_label[coords2] is None:
						area_label[coords2] = areas
						queue.append(coords2)
			areas += 1

		coords_set_by_area = defaultdict(lambda: set())
		for coords, area_number in area_label.iteritems():
			if coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE and coords not in collector_area:
				coords_set_by_area[area_number].add(coords)

		options = []
		for (x, y), area_number in area_label.iteritems():
			builder = self.make_builder(BUILDINGS.STORAGE_CLASS, x, y, False)
			if not builder:
				continue

			coords_set = set(builder.position.get_radius_coordinates(Entities.buildings[BUILDINGS.STORAGE_CLASS].radius))
			useful_area = len(coords_set_by_area[area_number].intersection(coords_set))
			if not useful_area:
				continue

			alignment = 1
			for tile in self._get_neighbour_tiles(builder.position):
				if tile is None:
					continue
				coords = (tile.x, tile.y)
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			value = useful_area + alignment * self.personality.collector_area_enlargement_alignment_coefficient
			options.append((-value, builder))

		for _, builder in sorted(options):
			building = builder.execute()
			if not building:
				return BUILD_RESULT.UNKNOWN_ERROR
			for x, y in builder.position.tuple_iter():
				self.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
			self.register_change(builder.position.origin.x, builder.position.origin.y, BUILDING_PURPOSE.STORAGE, builder)
			return BUILD_RESULT.OK

		if self.settlement_manager.village_builder.tent_queue:
			# impossible to build a storage but may be possible to help a bit with a tent
			# TODO: prefer the current section of the village
			tent_size = Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].size
			tent_radius = Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].radius
			best_coords = None
			best_area = 0

			for x, y in self.settlement_manager.village_builder.tent_queue:
				new_area = 0
				for coords in Rect.init_from_topleft_and_size(x, y, tent_size[0] - 1, tent_size[1] - 1).get_radius_coordinates(tent_radius):
					if coords in area_label and coords not in self.land_manager.roads and coords not in collector_area:
						new_area += 1
				if new_area > best_area:
					best_coords = (x, y)
					best_area = new_area
			if best_coords is not None:
				return self._extend_settlement_with_tent(Rect.init_from_topleft_and_size(best_coords[0], best_coords[1], tent_size[0] - 1, tent_size[1] - 1))

		return BUILD_RESULT.IMPOSSIBLE

	def count_available_squares(self, size, max_num = None):
		""" decide based on the number of 3 x 3 squares available vs still possible """
		key = (size, max_num)
		if key in self.__available_squares_cache and self.last_change_id == self.__available_squares_cache[key][0]:
			return self.__available_squares_cache[key][1]

		offsets = list(itertools.product(xrange(size), xrange(size)))
		collector_area = self._get_collector_area()

		available_squares = 0
		total_squares = 0
		for x, y in self.plan:
			ok = True
			accessible = False
			for dx, dy in offsets:
				coords = (x + dx, y + dy)
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					ok = False
					break
				if coords in collector_area:
					accessible = True
			if ok:
				total_squares += 1
				if max_num is not None and total_squares >= max_num:
					break
				if accessible:
					available_squares += 1
		self.__available_squares_cache[key] = (self.last_change_id, (available_squares, total_squares))
		return self.__available_squares_cache[key][1]

	def need_to_enlarge_collector_area(self):
		""" decide based on the number of 3 x 3 squares available vs still possible """
		available_squares, total_squares = self.count_available_squares(3, self.personality.max_interesting_collector_area)
		self.log.info('%s collector area: %d of %d useable', self, available_squares, total_squares)
		return available_squares < min(self.personality.max_interesting_collector_area, total_squares - self.personality.max_collector_area_unreachable)

	def count_fields(self):
		fields = {BUILDING_PURPOSE.POTATO_FIELD: 0, BUILDING_PURPOSE.PASTURE: 0, BUILDING_PURPOSE.SUGARCANE_FIELD: 0}
		for building in self.production_buildings:
			if building.id == BUILDINGS.POTATO_FIELD_CLASS:
				fields[BUILDING_PURPOSE.POTATO_FIELD] += 1
			elif building.id == BUILDINGS.PASTURE_CLASS:
				fields[BUILDING_PURPOSE.PASTURE] += 1
			elif building.id == BUILDINGS.SUGARCANE_FIELD_CLASS:
				fields[BUILDING_PURPOSE.SUGARCANE_FIELD] += 1
		return fields

	def refresh_unused_fields(self):
		self.unused_fields = self._make_empty_unused_fields()
		for coords, (purpose, _) in self.plan.iteritems():
			usable = True
			for dx in xrange(3):
				for dy in xrange(3):
					coords2 = (coords[0] + dx, coords[1] + dy)
					object = self.island.ground_map[coords2].object
					if object is not None and not onject.buildable_upon:
						usable = False
			if not usable:
				continue # don't add used field spots to the list

			if purpose == BUILDING_PURPOSE.POTATO_FIELD:
				self.unused_fields[purpose].append(coords)
			elif purpose == BUILDING_PURPOSE.PASTURE:
				self.unused_fields[purpose].append(coords)
			elif purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
				self.unused_fields[purpose].append(coords)

	def display(self):
		if not AI.HIGHLIGHT_PLANS:
			return

		road_colour = (30, 30, 30)
		fisher_colour = (128, 128, 128)
		lumberjack_colour = (30, 255, 30)
		tree_colour = (0, 255, 0)
		reserved_colour = (0, 0, 128)
		unknown_colour = (128, 0, 0)
		farm_colour = (128, 0, 255)
		potato_field_colour = (255, 0, 128)
		pasture_colour = (0, 192, 0)
		weaver_colour = (0, 64, 64)
		sugarcane_field_colour = (192, 192, 0)
		distillery_colour = (255, 128, 40)
		clay_pit_colour = (0, 64, 0)
		brickyard_colour = (0, 32, 0)
		boatbuilder_colour = (163, 73, 164)
		renderer = self.session.view.renderer['InstanceRenderer']

		for coords, (purpose, _) in self.plan.iteritems():
			tile = self.island.ground_map[coords]
			if purpose == BUILDING_PURPOSE.ROAD:
				renderer.addColored(tile._instance, *road_colour)
			elif purpose == BUILDING_PURPOSE.FISHER:
				renderer.addColored(tile._instance, *fisher_colour)
			elif purpose == BUILDING_PURPOSE.LUMBERJACK:
				renderer.addColored(tile._instance, *lumberjack_colour)
			elif purpose == BUILDING_PURPOSE.TREE:
				renderer.addColored(tile._instance, *tree_colour)
			elif purpose == BUILDING_PURPOSE.FARM:
				renderer.addColored(tile._instance, *farm_colour)
			elif purpose == BUILDING_PURPOSE.POTATO_FIELD:
				renderer.addColored(tile._instance, *potato_field_colour)
			elif purpose == BUILDING_PURPOSE.PASTURE:
				renderer.addColored(tile._instance, *pasture_colour)
			elif purpose == BUILDING_PURPOSE.WEAVER:
				renderer.addColored(tile._instance, *weaver_colour)
			elif purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
				renderer.addColored(tile._instance, *sugarcane_field_colour)
			elif purpose == BUILDING_PURPOSE.DISTILLERY:
				renderer.addColored(tile._instance, *distillery_colour)
			elif purpose == BUILDING_PURPOSE.CLAY_PIT:
				renderer.addColored(tile._instance, *clay_pit_colour)
			elif purpose == BUILDING_PURPOSE.BRICKYARD:
				renderer.addColored(tile._instance, *brickyard_colour)
			elif purpose == BUILDING_PURPOSE.BOAT_BUILDER:
				renderer.addColored(tile._instance, *boatbuilder_colour)
			elif purpose == BUILDING_PURPOSE.RESERVED:
				renderer.addColored(tile._instance, *reserved_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

	def make_builder(self, building_id, x, y, needs_collector, orientation = 0):
		coords = (x, y)
		key = (building_id, coords, needs_collector, orientation)
		size = Entities.buildings[building_id].size
		if orientation == 1 or orientation == 3:
			size = (size[1], size[0])
		if coords not in self.island.last_changed[size]:
			return None

		island_changed = self.island.last_changed[size][coords]
		if key in self.builder_cache and island_changed != self.builder_cache[key][0]:
			del self.builder_cache[key]

		plan_changed = self.last_change_id
		if key in self.builder_cache and plan_changed != self.builder_cache[key][1]:
			del self.builder_cache[key]

		if key not in self.builder_cache:
			self.builder_cache[key] = (island_changed, plan_changed, self._make_builder(building_id, x, y, needs_collector, orientation))
		return self.builder_cache[key][2]

	def _init_cache(self):
		""" initialises the cache that knows when the last time the buildability of a rectangle may have changed in this area """ 
		super(ProductionBuilder, self)._init_cache()

		building_sizes = set()
		db_result = self.session.db("SELECT DISTINCT size_x, size_y FROM building WHERE button_name IS NOT NULL")
		for size_x, size_y in db_result:
			building_sizes.add((size_x, size_y))
			building_sizes.add((size_y, size_x))

		self.last_changed = {}
		for size in building_sizes:
			self.last_changed[size] = {}

		for (x, y) in self.plan:
			for size_x, size_y in building_sizes:
				all_legal = True
				for dx in xrange(size_x):
					for dy in xrange(size_y):
						if (x + dx, y + dy) in self.land_manager.village:
							all_legal = False
							break
					if not all_legal:
						break
				if all_legal:
					self.last_changed[(size_x, size_y)][(x, y)] = self.last_change_id

		# initialise other caches
		self.__collector_area_cache = None
		self.__available_squares_cache = {}

	def register_change(self, x, y, purpose, builder):
		""" registers the possible buildability change of a rectangle on this island """
		super(ProductionBuilder, self).register_change(x, y, purpose, builder)
		coords = (x, y)
		if coords in self.land_manager.village or coords not in self.plan:
			return
		self.last_change_id += 1
		for (area_size_x, area_size_y), building_areas in self.last_changed.iteritems():
			for dx in xrange(area_size_x):
				for dy in xrange(area_size_y):
					coords = (x - dx, y - dy)
					# building area with origin at coords affected
					if coords in building_areas:
						building_areas[coords] = self.last_change_id

	def handle_lost_area(self, coords_list):
		# remove planned fields that are now impossible
		field_size = Entities.buildings[BUILDINGS.POTATO_FIELD_CLASS].size
		removed_list = []
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose in [BUILDING_PURPOSE.POTATO_FIELD, BUILDING_PURPOSE.PASTURE, BUILDING_PURPOSE.SUGARCANE_FIELD]:
				rect = Rect.init_from_topleft_and_size_tuples(coords, field_size)
				for field_coords in rect.tuple_iter():
					if field_coords not in self.land_manager.production:
						removed_list.append(coords)
						break

		for coords in removed_list:
			rect = Rect.init_from_topleft_and_size_tuples(coords, field_size)
			for field_coords in rect.tuple_iter():
				self.plan[field_coords] = (BUILDING_PURPOSE.NONE, None)
		self.refresh_unused_fields()
		super(ProductionBuilder, self).handle_lost_area(coords_list)

	def handle_new_area(self):
		# new production area may be freed up when the village area is reduced
		for coords in self.land_manager.production:
			if coords not in self.plan:
				self.plan[coords] = (BUILDING_PURPOSE.NONE, None)

	def __str__(self):
		return '%s.PB(%s/%d)' % (self.owner, self.settlement.name if hasattr(self, 'settlement') else 'unknown', self.worldid)

decorators.bind_all(ProductionBuilder)
