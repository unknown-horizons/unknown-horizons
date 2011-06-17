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
import logging

from collections import deque

from builder import Builder
from roadplanner import RoadPlanner

from horizons.ai.aiplayer.buildingevaluator.fisherevaluator import FisherEvaluator
from horizons.ai.aiplayer.buildingevaluator.farmevaluator import FarmEvaluator
from horizons.ai.aiplayer.buildingevaluator.claypitevaluator import ClayPitEvaluator
from horizons.ai.aiplayer.buildingevaluator.brickyardevaluator import BrickyardEvaluator
from horizons.ai.aiplayer.buildingevaluator.weaverevaluator import WeaverEvaluator
from horizons.ai.aiplayer.buildingevaluator.distilleryevaluator import DistilleryEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.constants import AI, BUILDINGS, RES
from horizons.util import Point, Rect, WorldObject
from horizons.util.python import decorators
from horizons.entities import Entities

class ProductionBuilder(WorldObject):
	log = logging.getLogger("ai.aiplayer")

	def __init__(self, settlement_manager):
		super(ProductionBuilder, self).__init__()
		self.__init(settlement_manager)
		self.plan = dict.fromkeys(self.land_manager.production, (PRODUCTION_PURPOSE.NONE, None))
		for coords in settlement_manager.branch_office.position.tuple_iter():
			if coords in self.plan:
				self.plan[coords] = (PRODUCTION_PURPOSE.BRANCH_OFFICE, None)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self.land_manager = settlement_manager.land_manager
		self.island = self.land_manager.island
		self.session = self.island.session
		self.owner = self.land_manager.owner
		self.settlement = self.land_manager.settlement
		self.collector_buildings = [settlement_manager.branch_office]
		self.production_buildings = []
		self.plan = {}
		self.unused_fields = self._make_empty_unused_fields()

	@classmethod
	def _make_empty_unused_fields(self):
		return {
			PRODUCTION_PURPOSE.POTATO_FIELD: deque(),
			PRODUCTION_PURPOSE.PASTURE: deque(),
			PRODUCTION_PURPOSE.SUGARCANE_FIELD: deque(),
		}

	def save(self, db):
		super(ProductionBuilder, self).save(db)
		db("INSERT INTO ai_production_builder(rowid, settlement_manager) VALUES(?, ?)", self.worldid, \
			self.settlement_manager.worldid)
		for (x, y), (purpose, builder) in self.plan.iteritems():
			db("INSERT INTO ai_production_builder_coords(production_builder, x, y, purpose, builder) VALUES(?, ?, ?, ?, ?)", \
				self.worldid, x, y, purpose, None if builder is None else builder.worldid)
			if builder is not None:
				assert isinstance(builder, Builder)
				builder.save(db)

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_production_builder WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(ProductionBuilder, self).load(db, worldid)
		self.__init(settlement_manager)

		db_result = db("SELECT x, y, purpose, builder FROM ai_production_builder_coords WHERE production_builder = ?", worldid)
		for x, y, purpose, builder_id in db_result:
			coords = (x, y)
			builder = Builder.load(db, builder_id, self.land_manager) if builder_id else None
			self.plan[coords] = (purpose, builder)
			object = self.island.ground_map[coords].object
			if object is None:
				continue

			if purpose == PRODUCTION_PURPOSE.FISHER and object.id == BUILDINGS.FISHERMAN_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.LUMBERJACK and object.id == BUILDINGS.LUMBERJACK_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.FARM and object.id == BUILDINGS.FARM_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.CLAY_PIT and object.id == BUILDINGS.CLAY_PIT_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.BRICKYARD and object.id == BUILDINGS.BRICKYARD_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.WEAVER and object.id == BUILDINGS.WEAVER_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.DISTILLERY and object.id == BUILDINGS.DISTILLERY_CLASS:
				self.production_buildings.append(object)
			elif purpose == PRODUCTION_PURPOSE.STORAGE and object.id == BUILDINGS.STORAGE_CLASS:
				self.collector_buildings.append(object)

		self.refresh_unused_fields()

	def _get_neighbour_tiles(self, rect):
		"""
		returns the surrounding tiles except the corners
		"""
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		for x, y in rect.tuple_iter():
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if not rect.contains_tuple(coords):
					yield self.island.get_tile_tuple(coords)

	def _get_possible_road_coords(self, rect):
		for tile in self._get_neighbour_tiles(rect):
			if tile is None:
				continue
			point = Point(tile.x, tile.y)
			building = self.session.world.get_building(point)
			if building is None:
				road = Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, point)
				if road:
					yield (tile.x, tile.y)
			else:
				if building.buildable_upon or building.id == BUILDINGS.TRAIL_CLASS:
					yield (tile.x, tile.y)

	def _fill_distance(self, distance, nodes):
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		queue = deque([item for item in distance.iteritems()])

		while len(queue) > 0:
			(coords, dist) = queue.popleft()
			for dx, dy in moves:
				coords2 = (coords[0] + dx, coords[1] + dy)
				if coords2 in nodes and coords2 not in distance:
					distance[coords2] = dist + 1
					queue.append((coords2, dist + 1))

	def _get_path_nodes(self):
		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

		nodes = {}
		distance_to_road = {}
		distance_to_boundary = {}
		for coords in self.plan:
			if coords not in self.land_manager.settlement.ground_map:
				continue
			if self.plan[coords][0] == PRODUCTION_PURPOSE.NONE:
				nodes[coords] = 1
			elif self.plan[coords][0] == PRODUCTION_PURPOSE.ROAD:
				nodes[coords] = 1
				distance_to_road[coords] = 0

			for (dx, dy) in moves:
				coords2 = (coords[0] + dx, coords[1] + dy)
				if coords2 not in self.land_manager.production:
					distance_to_boundary[coords] = 1
					break

		for coords in self.land_manager.village:
			building = self.island.get_building(Point(coords[0], coords[1]))
			if building is not None and building.id == BUILDINGS.TRAIL_CLASS:
				nodes[coords] = 1
				distance_to_road[coords] = 0

		self._fill_distance(distance_to_road, self.island.path_nodes.nodes)
		self._fill_distance(distance_to_boundary, self.island.path_nodes.nodes)

		for coords in nodes:
			if coords in distance_to_road:
				distance = distance_to_road[coords]
				if distance > 9:
					nodes[coords] += 0.5
				elif 0 < distance <= 9:
					nodes[coords] += 0.7 + (10 - distance) * 0.15
			else:
				nodes[coords] += 0.1

			if coords in distance_to_boundary:
				distance = distance_to_boundary[coords]
				if 1 < distance <= 10:
					nodes[coords] += 0.3 + (11 - distance) * 0.03
			else:
				nodes[coords] += 0.1

		return nodes

	def _get_road_to_builder(self, builder):
		collector_coords = set()
		for building in self.collector_buildings:
			for coords in self._get_possible_road_coords(building.position):
				collector_coords.add(coords)

		blocked_coords = set([coords for coords in builder.position.tuple_iter()])
		destination_coords = set(self._get_possible_road_coords(builder.position))

		pos = builder.position
		beacon = Rect.init_from_borders(pos.left - 1, pos.top - 1, pos.right + 1, pos.bottom + 1)

		return RoadPlanner()(collector_coords, destination_coords, beacon, self._get_path_nodes(), blocked_coords = blocked_coords)

	def _build_road_connection(self, builder):
		path = self._get_road_to_builder(builder)
		if path is not None:
			for x, y in path:
				point = Point(x, y)
				self.plan[point.to_tuple()] = (PRODUCTION_PURPOSE.ROAD, None)
				building = self.island.get_building(point)
				if building is not None and building.id == BUILDINGS.TRAIL_CLASS:
					continue
				assert Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, point).execute()
		return path is not None

	def _road_connection_possible(self, builder):
		return self._get_road_to_builder(builder) is not None

	def _near_collectors(self, position):
		for building in self.collector_buildings:
			if building.position.distance(position) <= building.radius:
				return True
		return False

	def make_builder(self, building_id, x, y, needs_collector, orientation=0):
		""" Returns the Builder if it is allowed to be built at the location, otherwise returns None """
		coords = (x, y)
		if building_id == BUILDINGS.CLAY_PIT_CLASS:
			# clay deposits are outside the production plan until they are constructed
			if coords in self.plan or coords not in self.land_manager.settlement.ground_map:
				return None
		else:
			if coords not in self.plan or self.plan[coords][0] != PRODUCTION_PURPOSE.NONE or coords not in self.land_manager.settlement.ground_map:
				return None
		builder = Builder.create(building_id, self.land_manager, Point(x, y), orientation=orientation)
		if not builder or not self.land_manager.legal_for_production(builder.position):
			return None
		if building_id == BUILDINGS.FISHERMAN_CLASS: #
			for coords in builder.position.tuple_iter():
				if coords in self.plan and self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					return None
		elif building_id != BUILDINGS.CLAY_PIT_CLASS:
			# clay deposits are outside the production plan until they are constructed
			for coords in builder.position.tuple_iter():
				if coords not in self.plan or self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					return None
		if needs_collector and not self._near_collectors(builder.position):
			return None
		return builder

	def have_resources(self, building_id):
		return Entities.buildings[building_id].have_resources([self.land_manager.settlement], self.owner)

	def get_next_fisher(self):
		"""
		Finds a reasonable place for a fisher and returns the BuildingEvaluator object.
		"""
		options = []
		for (x, y) in self.plan:
			evaluator = FisherEvaluator.create(self, x, y)
			if evaluator is not None:
				options.append(evaluator)

		for evaluator in sorted(options):
			if self._road_connection_possible(evaluator.builder):
				return evaluator
		return None

	def build_lumberjack(self):
		"""
		Finds a reasonable place for a lumberjack and builds the lumberjack along with
		a road connection and additional trees.
		"""
		if not self.have_resources(BUILDINGS.LUMBERJACK_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
		options = []

		cell_value = {}
		alignment_value = {}
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose == PRODUCTION_PURPOSE.NONE:
				cell_value[coords] = 3
			elif purpose == PRODUCTION_PURPOSE.TREE:
				cell_value[coords] = 1
			else:
				continue

			alignment = 0
			for dx, dy in moves:
				coords2 = (coords[0] + dx, coords[1] + dy)
				if coords2 not in self.plan or self.plan[coords][0] == PRODUCTION_PURPOSE.ROAD:
					alignment += 2 if abs(dx) + abs(dy) == 1 else 1
			alignment_value[coords] = alignment

		for (x, y) in self.plan:
			lumberjack = self.make_builder(BUILDINGS.LUMBERJACK_CLASS, x, y, True)
			if not lumberjack:
				continue

			value = 0
			alignment = 0
			used_area = set(lumberjack.position.get_radius_coordinates(3, True))
			for coords in lumberjack.position.get_radius_coordinates(3):
				if coords in cell_value:
					value += cell_value[coords]
					alignment += alignment_value[coords]
			value = min(value, 100)
			if value >= 30:
				options.append((-value - math.log(alignment + 1) - alignment / 5.0, lumberjack))

		for _, lumberjack in sorted(options):
			if not self._build_road_connection(lumberjack):
				continue
			building = lumberjack.execute()
			if not building:
				return BUILD_RESULT.UNKNOWN_ERROR
			for coords in lumberjack.position.tuple_iter():
				self.plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
			self.plan[sorted(lumberjack.position.tuple_iter())[0]] = (PRODUCTION_PURPOSE.LUMBERJACK, lumberjack)

			for coords in lumberjack.position.get_radius_coordinates(3):
				if coords in self.plan and self.plan[coords][0] == PRODUCTION_PURPOSE.NONE:
					self.plan[coords] = (PRODUCTION_PURPOSE.TREE, None)
					tree = Builder.create(BUILDINGS.TREE_CLASS, self.land_manager, Point(coords[0], coords[1])).execute()
			self.production_buildings.append(building)
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def get_next_farm(self, unused_field_purpose):
		"""
		Finds a reasonable place for a farm and returns the BuildingEvaluator object.
		"""
		if self.owner.settler_level < 1:
			return None

		road_side = [(-1, 0), (0, -1), (0, 3), (3, 0)]
		options = []

		most_fields = 1
		for (x, y) in self.plan:
			# try the 4 road configurations (road through the farm area on any of the farm's sides)
			for road_dx, road_dy in road_side:
				evaluator = FarmEvaluator.create(self, x, y, road_dx, road_dy, most_fields, unused_field_purpose)
				if evaluator is not None:
					options.append(evaluator)
					most_fields = max(most_fields, evaluator.fields)

		for evaluator in sorted(options):
			if self._road_connection_possible(evaluator.builder):
				return evaluator
		return None

	def build_food_producer(self):
		build_fields = False
		if not self.unused_fields[PRODUCTION_PURPOSE.POTATO_FIELD]:
			if not self.have_resources(BUILDINGS.FISHERMAN_CLASS) and not self.have_resources(BUILDINGS.FARM_CLASS):
				return BUILD_RESULT.NEED_RESOURCES
			next_fisher = self.get_next_fisher()
			next_farm = self.get_next_farm(PRODUCTION_PURPOSE.UNUSED_POTATO_FIELD)
			if next_fisher is None:
				if next_farm is None:
					return BUILD_RESULT.IMPOSSIBLE
				# build the farm
				result = next_farm.execute()
				if result != BUILD_RESULT.OK:
					return result
				build_fields = True
			elif next_farm is None:
				# build the fisher
				result = next_fisher.execute()
				if result == BUILD_RESULT.OK:
					self.settlement_manager.num_fishers += 1
				return result
			else:
				resource_limits = {} # 
				cost_farm = next_farm.get_unit_cost(RES.FOOD_ID, resource_limits)
				cost_fisher = next_fisher.get_unit_cost(RES.FOOD_ID, resource_limits)
				self.log.info('%s farm %.5f, fisher %.5f', self.settlement_manager, cost_farm, cost_fisher)
				if cost_farm <= cost_fisher:
					result = next_farm.execute()
					if result != BUILD_RESULT.OK:
						return result
					build_fields = True
				else:
					result = next_fisher.execute()
					if result == BUILD_RESULT.OK:
						self.settlement_manager.num_fishers += 1
					return result
		else:
			build_fields = True

		if build_fields:
			assert len(self.unused_fields[PRODUCTION_PURPOSE.POTATO_FIELD]) > 0
			coords = self.unused_fields[PRODUCTION_PURPOSE.POTATO_FIELD][0]
			builder = Builder.create(BUILDINGS.POTATO_FIELD_CLASS, self.land_manager, Point(coords[0], coords[1]))
			if not builder.execute():
				return BUILD_RESULT.UNKNOWN_ERROR
			self.unused_fields[PRODUCTION_PURPOSE.POTATO_FIELD].popleft()
			self.plan[coords] = (PRODUCTION_PURPOSE.POTATO_FIELD, builder)
			self.settlement_manager.num_fields[PRODUCTION_PURPOSE.POTATO_FIELD] += 1
			return BUILD_RESULT.OK

	def build_simple_field_producer(self, field_purpose, field_id):
		if not self.unused_fields[field_purpose]:
			if not self.have_resources(BUILDINGS.FARM_CLASS):
				return BUILD_RESULT.NEED_RESOURCES
			next_farm = self.get_next_farm(PRODUCTION_PURPOSE.get_unused_purpose(field_purpose))
			if next_farm is None:
				return BUILD_RESULT.IMPOSSIBLE
			# build the farm
			result = next_farm.execute()
			if result != BUILD_RESULT.OK:
				return result

		assert len(self.unused_fields[field_purpose]) > 0
		coords = self.unused_fields[field_purpose][0]
		builder = Builder.create(field_id, self.land_manager, Point(coords[0], coords[1]))
		if not builder.execute():
			return BUILD_RESULT.UNKNOWN_ERROR
		self.unused_fields[field_purpose].popleft()
		self.plan[coords] = (field_purpose, builder)
		self.settlement_manager.num_fields[field_purpose] += 1
		return BUILD_RESULT.OK

	def build_wool_producer(self):
		return self.build_simple_field_producer(PRODUCTION_PURPOSE.PASTURE, BUILDINGS.PASTURE_CLASS)

	def build_sugar_producer(self):
		return self.build_simple_field_producer(PRODUCTION_PURPOSE.SUGARCANE_FIELD, BUILDINGS.SUGARCANE_FIELD_CLASS)

	def build_simple_producer(self, building_id, evaluator_class):
		""" Builds a producer and a road leading to it """
		if not self.have_resources(building_id):
			return BUILD_RESULT.NEED_RESOURCES

		options = []
		for (x, y) in self.plan:
			evaluator = evaluator_class.create(self, x, y)
			if evaluator is not None:
				options.append(evaluator)

		for evaluator in sorted(options):
			return evaluator.execute()
		return BUILD_RESULT.IMPOSSIBLE

	def build_weaver(self):
		""" Builds a weaver and a road leading to it """
		return self.build_simple_producer(BUILDINGS.WEAVER_CLASS, WeaverEvaluator)

	def build_distillery(self):
		""" Builds a distillery and a road leading to it """
		return self.build_simple_producer(BUILDINGS.DISTILLERY_CLASS, DistilleryEvaluator)

	def enough_collectors(self):
		produce_quantity = 0
		for building in self.production_buildings:
			if building.id == BUILDINGS.FARM_CLASS:
				produce_quantity += 2
			elif building.id == BUILDINGS.CLAY_PIT_CLASS:
				pass
			else:
				produce_quantity += 1
		return 1 + 2 * len(self.collector_buildings) > produce_quantity

	def _get_collector_data(self):
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		
		data = {}
		keys = {}
		for building in self.production_buildings:
			data[building] = {}
			for coords in building.position.tuple_iter():
				keys[coords] = building

		for collector in self.collector_buildings:
			distance = {}
			queue = deque()
			for tile in self._get_neighbour_tiles(collector.position):
				if tile is None:
					continue
				point = Point(tile.x, tile.y)
				building = self.session.world.get_building(point)
				if building and building.id == BUILDINGS.TRAIL_CLASS:
					distance[(tile.x, tile.y)] = 0
					queue.append(((tile.x, tile.y), 0))

			while len(queue) > 0:
				(coords, dist) = queue.popleft()
				for dx, dy in moves:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in distance:
						point2 = Point(coords2[0], coords2[1])
						building = self.session.world.get_building(point2)
						if building and building.id == BUILDINGS.TRAIL_CLASS:
							distance[coords2] = dist + 1
							queue.append((coords2, dist + 1))
						elif coords2 in keys and collector not in data[keys[coords2]]:
							distance[coords2] = dist + 1
							data[keys[coords2]][collector] = dist + 1
		return (data, keys)

	def evaluate_collector_data(self, data):
		"""
		Calculates the value of the collector arrangement
		@param data: {building -> {building/builder -> distance}}
		@return: the value of the arrangement (smaller is better)
		"""
		result = 0
		for building_data in data.itervalues():
			value = 0.000001
			for collector, distance in building_data.iteritems():
				collectors = 2 if isinstance(collector, Builder) else len(collector.get_local_collectors())
				value += collectors / (5.0 + distance)
			result += 1 / value
		return result

	def improve_collector_coverage(self):
		"""
		Builds a storage tent to improve collector coverage.
		"""
		if not self.have_resources(BUILDINGS.STORAGE_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		(data, keys) = self._get_collector_data()
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		options = []

		for (x, y), (purpose, _) in self.plan.iteritems():
			if purpose != PRODUCTION_PURPOSE.NONE or (x, y) not in self.land_manager.settlement.ground_map:
				continue
			point = Point(x, y)
			builder = Builder.create(BUILDINGS.STORAGE_CLASS, self.land_manager, point)
			if not builder or not self.land_manager.legal_for_production(builder.position):
				continue
			for coords in builder.position.tuple_iter():
				if self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					builder = None
			if builder is None:
				continue # part of the land is already reserved

			distance = {}
			alignment = 1
			queue = deque()
			for tile in self._get_neighbour_tiles(builder.position):
				if tile is None:
					continue
				point = Point(tile.x, tile.y)
				coords = (tile.x, tile.y)
				building = self.session.world.get_building(point)
				if building and building.id == BUILDINGS.TRAIL_CLASS:
					distance[coords] = 0
					queue.append((coords, 0))
				if coords not in self.plan or self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					alignment += 1
			if not distance:
				continue

			extra_data = {}
			for key in data:
				extra_data[key] = copy.copy(data[key])

			while len(queue) > 0:
				(coords, dist) = queue.popleft()
				for dx, dy in moves:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in distance:
						point2 = Point(coords2[0], coords2[1])
						building = self.session.world.get_building(point2)
						if building and building.id == BUILDINGS.TRAIL_CLASS:
							distance[coords2] = dist + 1
							queue.append((coords2, dist + 1))
						elif coords2 in keys and builder not in extra_data[keys[coords2]]:
							distance[coords2] = dist + 1
							extra_data[keys[coords2]][builder] = dist + 1

			value = self.evaluate_collector_data(extra_data) - math.log(alignment) * 0.001
			options.append((value, builder))

		for _, builder in sorted(options):
			building = builder.execute()
			if not building:
				return BUILD_RESULT.UNKNOWN_ERROR
			for coords in builder.position.tuple_iter():
				self.plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
			self.plan[sorted(builder.position.tuple_iter())[0]] = (PRODUCTION_PURPOSE.STORAGE, builder)
			self.collector_buildings.append(building)
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def build_clay_pit(self):
		""" Builds a clay pit and a road leading to it """
		if not self.have_resources(BUILDINGS.CLAY_PIT_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		options = []
		for building in self.settlement.get_buildings_by_id(BUILDINGS.CLAY_DEPOSIT_CLASS):
			(x, y) = building.position.origin.to_tuple()
			evaluator = ClayPitEvaluator.create(self, x, y)
			if evaluator is not None:
				options.append(evaluator)

		for evaluator in sorted(options):
			return evaluator.execute()
		return BUILD_RESULT.IMPOSSIBLE

	def build_brickyard(self):
		""" Builds a brickyard and a road leading to it """
		if not self.have_resources(BUILDINGS.BRICKYARD_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		options = []
		for (x, y) in self.plan:
			for orientation in xrange(0, 2):
				evaluator = BrickyardEvaluator.create(self, x, y, orientation)
				if evaluator is not None:
					options.append(evaluator)

		for evaluator in sorted(options):
			return evaluator.execute()
		return BUILD_RESULT.IMPOSSIBLE

	def count_fishers(self):
		fishers = 0
		for building in self.production_buildings:
			if building.id == BUILDINGS.FISHERMAN_CLASS:
				fishers += 1
		return fishers

	def count_fields(self):
		fields = {PRODUCTION_PURPOSE.POTATO_FIELD: 0, PRODUCTION_PURPOSE.PASTURE: 0}
		for building in self.production_buildings:
			if building.id == BUILDINGS.POTATO_FIELD_CLASS:
				fields[PRODUCTION_PURPOSE.POTATO_FIELD] += 1
			elif building.id == BUILDINGS.PASTURE_CLASS:
				fields[PRODUCTION_PURPOSE.PASTURE] += 1
			elif building.id == BUILDINGS.SUGARCANE_FIELD_CLASS:
				fields[PRODUCTION_PURPOSE.SUGARCANE_FIELD] += 1
		return fields

	def refresh_unused_fields(self):
		self.unused_fields = self._make_empty_unused_fields()
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose == PRODUCTION_PURPOSE.UNUSED_POTATO_FIELD:
				self.unused_fields[PRODUCTION_PURPOSE.POTATO_FIELD].append(coords)
			elif purpose == PRODUCTION_PURPOSE.UNUSED_PASTURE:
				self.unused_fields[PRODUCTION_PURPOSE.PASTURE].append(coords)
			elif purpose == PRODUCTION_PURPOSE.UNUSED_SUGARCANE_FIELD:
				self.unused_fields[PRODUCTION_PURPOSE.SUGARCANE_FIELD].append(coords)

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
		unused_potato_field_colour = (255, 0, 128)
		potato_field_colour = (0, 128, 0)
		unused_pasture_colour = (255, 0, 192)
		pasture_colour = (0, 192, 0)
		weaver_colour = (0, 64, 64)
		unused_sugarcane_field_colour = (255, 255, 0)
		sugarcane_field_colour = (192, 192, 0)
		distillery_colour = (255, 128, 40)
		clay_pit_colour = (0, 64, 0)
		brickyard_colour = (0, 32, 0)
		renderer = self.session.view.renderer['InstanceRenderer']

		for coords, (purpose, _) in self.plan.iteritems():
			tile = self.island.ground_map[coords]
			if purpose == PRODUCTION_PURPOSE.ROAD:
				renderer.addColored(tile._instance, *road_colour)
			elif purpose == PRODUCTION_PURPOSE.FISHER:
				renderer.addColored(tile._instance, *fisher_colour)
			elif purpose == PRODUCTION_PURPOSE.LUMBERJACK:
				renderer.addColored(tile._instance, *lumberjack_colour)
			elif purpose == PRODUCTION_PURPOSE.TREE:
				renderer.addColored(tile._instance, *tree_colour)
			elif purpose == PRODUCTION_PURPOSE.FARM:
				renderer.addColored(tile._instance, *farm_colour)
			elif purpose == PRODUCTION_PURPOSE.UNUSED_POTATO_FIELD:
				renderer.addColored(tile._instance, *unused_potato_field_colour)
			elif purpose == PRODUCTION_PURPOSE.POTATO_FIELD:
				renderer.addColored(tile._instance, *potato_field_colour)
			elif purpose == PRODUCTION_PURPOSE.UNUSED_PASTURE:
				renderer.addColored(tile._instance, *unused_pasture_colour)
			elif purpose == PRODUCTION_PURPOSE.PASTURE:
				renderer.addColored(tile._instance, *pasture_colour)
			elif purpose == PRODUCTION_PURPOSE.WEAVER:
				renderer.addColored(tile._instance, *weaver_colour)
			elif purpose == PRODUCTION_PURPOSE.UNUSED_SUGARCANE_FIELD:
				renderer.addColored(tile._instance, *unused_sugarcane_field_colour)
			elif purpose == PRODUCTION_PURPOSE.SUGARCANE_FIELD:
				renderer.addColored(tile._instance, *sugarcane_field_colour)
			elif purpose == PRODUCTION_PURPOSE.DISTILLERY:
				renderer.addColored(tile._instance, *distillery_colour)
			elif purpose == PRODUCTION_PURPOSE.CLAY_PIT:
				renderer.addColored(tile._instance, *clay_pit_colour)
			elif purpose == PRODUCTION_PURPOSE.BRICKYARD:
				renderer.addColored(tile._instance, *brickyard_colour)
			elif purpose == PRODUCTION_PURPOSE.RESERVED:
				renderer.addColored(tile._instance, *reserved_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

decorators.bind_all(ProductionBuilder)
