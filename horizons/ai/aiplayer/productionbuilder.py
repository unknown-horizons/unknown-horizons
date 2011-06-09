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

from collections import deque

from builder import Builder
from roadplanner import RoadPlanner

from horizons.ai.aiplayer.buildingevaluator.fisherevaluator import FisherEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.constants import AI, BUILDINGS
from horizons.util import Point, Rect, WorldObject
from horizons.util.python import decorators
from horizons.entities import Entities

class ProductionBuilder(WorldObject):
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
		self.unused_fields = deque()

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

	def _build_road_connection(self, builder):
		collector_coords = set()
		for building in self.collector_buildings:
			for coords in self._get_possible_road_coords(building.position):
				collector_coords.add(coords)

		blocked_coords = set([coords for coords in builder.position.tuple_iter()])
		destination_coords = set(self._get_possible_road_coords(builder.position))

		pos = builder.position
		beacon = Rect.init_from_borders(pos.left - 1, pos.top - 1, pos.right + 1, pos.bottom + 1)

		path = RoadPlanner()(collector_coords, destination_coords, beacon, self._get_path_nodes(), blocked_coords = blocked_coords)
		if path is not None:
			for x, y in path:
				point = Point(x, y)
				self.plan[point.to_tuple()] = (PRODUCTION_PURPOSE.ROAD, None)
				building = self.island.get_building(point)
				if building is not None and building.id == BUILDINGS.TRAIL_CLASS:
					continue
				road = Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, point).execute()
		return path is not None

	def _near_collectors(self, position):
		for building in self.collector_buildings:
			if building.position.distance(position) <= building.radius:
				return True
		return False

	def make_builder(self, building_id, x, y, needs_collector):
		""" Returns the Builder if it is allowed to be built at the location, otherwise returns None """
		coords = (x, y)
		if coords not in self.plan or self.plan[coords][0] != PRODUCTION_PURPOSE.NONE or coords not in self.land_manager.settlement.ground_map:
			return None
		builder = Builder.create(building_id, self.land_manager, Point(x, y))
		if not builder or not self.land_manager.legal_for_production(builder.position):
			return None
		if building_id == BUILDINGS.FISHERMAN_CLASS: #
			for coords in builder.position.tuple_iter():
				if coords in self.plan and self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					return None
		else:
			for coords in builder.position.tuple_iter():
				if coords not in self.plan or self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					return None
		if needs_collector and not self._near_collectors(builder.position):
			return None
		return builder

	def have_resources(self, building_id):
		return Entities.buildings[building_id].have_resources([self.land_manager.settlement], self.owner)

	def build_fisher(self):
		"""
		Finds a reasonable place for a fisher and builds the fisher and a road connection.
		"""
		if not self.have_resources(BUILDINGS.FISHERMAN_CLASS):
			return BUILD_RESULT.NEED_RESOURCES

		options = []
		for (x, y) in self.plan:
			builder = FisherEvaluator.create(self, x, y)
			if builder is not None:
				options.append((-builder.value, builder))

		for _, evaluator in sorted(options):
			result = evaluator.execute()
			if result == BUILD_RESULT.OK:
				return result
		return BUILD_RESULT.IMPOSSIBLE

	def build_lumberjack(self):
		"""
		Finds a reasonable place for a lumberjack and builds the lumberjack along with
		a road connection and additional trees.
		"""
		if not self.have_resources(BUILDINGS.LUMBERJACK_CLASS):
			return (True, False)

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
				return (None, False)
			for coords in lumberjack.position.tuple_iter():
				self.plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
			self.plan[sorted(lumberjack.position.tuple_iter())[0]] = (PRODUCTION_PURPOSE.LUMBERJACK, lumberjack)

			for coords in lumberjack.position.get_radius_coordinates(3):
				if coords in self.plan and self.plan[coords][0] == PRODUCTION_PURPOSE.NONE:
					self.plan[coords] = (PRODUCTION_PURPOSE.TREE, None)
					tree = Builder.create(BUILDINGS.TREE_CLASS, self.land_manager, Point(coords[0], coords[1])).execute()
			self.production_buildings.append(building)
			return (lumberjack, True)
		return (None, False)

	def _make_field_offsets(self):
		# right next to the farm
		first_class = [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]
		# offset by a road right next to the farm
		second_class = [(-4, -3), (-4, 0), (-4, 3), (-3, -4), (-3, 4), (0, -4), (0, 4), (3, -4), (3, 4), (4, -3), (4, 0), (4, 3)]
		# offset by crossing roads
		third_class = [(-4, -4), (-4, 4), (4, -4), (4, 4)]
		first_class.extend(second_class)
		first_class.extend(third_class)
		return first_class

	def build_farm(self):
		"""
		Finds a reasonable place for a farm and build the farm along with a road connection.
		The fields will be reserved but not built.
		"""
		if not self.have_resources(BUILDINGS.FARM_CLASS):
			return (True, False)

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		road_side = [(-1, 0), (0, -1), (0, 3), (3, 0)]
		field_offsets = self._make_field_offsets()
		options = []

		most_fields = 1
		for (x, y) in self.plan:
			farm = self.make_builder(BUILDINGS.FARM_CLASS, x, y, True)
			if not farm:
				continue

			# try the 4 road configurations (road through the farm area on any of the farm's sides)
			for road_dx, road_dy in road_side:
				farm_plan = {}

				# place the farm area road
				existing_roads = 0
				for other_offset in xrange(-3, 6):
					coords = None
					if road_dx == 0:
						coords = (x + other_offset, y + road_dy)
					else:
						coords = (x + road_dx, y + other_offset)
					if coords not in self.plan or (self.plan[coords][0] != PRODUCTION_PURPOSE.NONE and self.plan[coords][0] != PRODUCTION_PURPOSE.ROAD):
						farm_plan = None
						break

					if self.plan[coords][0] == PRODUCTION_PURPOSE.NONE:
						road = Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, Point(coords[0], coords[1]))
						if road:
							farm_plan[coords] = (PRODUCTION_PURPOSE.ROAD, road)
						else:
							farm_plan = None
							break
					else:
						existing_roads += 1
				if farm_plan is None:
					continue # impossible to build some part of the road

				# place the fields
				fields = 0
				for (dx, dy) in field_offsets:
					if fields >= 8:
						break # unable to place more anyway
					coords = (x + dx, y + dy)
					field = self.make_builder(BUILDINGS.POTATO_FIELD_CLASS, coords[0], coords[1], False)
					if not field:
						continue
					for coords2 in field.position.tuple_iter():
						if coords2 in farm_plan:
							field = None
							break
					if field is None:
						break # some part of the area is reserved for something else
					fields += 1
					for coords2 in field.position.tuple_iter():
						farm_plan[coords2] = (PRODUCTION_PURPOSE.RESERVED, None)
					farm_plan[coords] = (PRODUCTION_PURPOSE.FARM_FIELD, None)
				if fields < most_fields:
					continue # go for the most fields possible
				most_fields = fields

				# add the farm itself to the plan
				for coords in farm.position.tuple_iter():
					farm_plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
				farm_plan[(x, y)] = (PRODUCTION_PURPOSE.FARM, farm)

				alignment = 0
				for x, y in farm_plan:
					for dx, dy in moves:
						coords = (x + dx, y + dy)
						if coords in farm_plan:
							continue
						if coords not in self.plan or self.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
							alignment += 1

				value = fields + existing_roads * 0.005 + alignment * 0.001
				options.append((-value, farm_plan, farm))

		for _, farm_plan, farm in sorted(options):
			backup = copy.copy(self.plan)
			for coords, plan_item in farm_plan.iteritems():
				self.plan[coords] = plan_item
			if not self._build_road_connection(farm):
				self.plan = backup
				continue
			building = farm.execute()
			if not building:
				return (None, False)
			for coords, (purpose, builder) in farm_plan.iteritems():
				if purpose == PRODUCTION_PURPOSE.FARM_FIELD:
					self.unused_fields.append(coords)
			self.production_buildings.append(building)
			return (farm, True)
		return (None, False)

	def build_potato_field(self):
		if not self.unused_fields:
			result = self.build_farm()
			if not result[1]:
				return result
			self.display()
		assert len(self.unused_fields) > 0

		coords = self.unused_fields[0]
		builder = Builder.create(BUILDINGS.POTATO_FIELD_CLASS, self.land_manager, Point(coords[0], coords[1]))
		if not builder.execute():
			return (None, False)
		self.unused_fields.popleft()
		self.plan[coords] = (PRODUCTION_PURPOSE.POTATO_FIELD, builder)
		return (builder, True)

	def enough_collectors(self):
		produce_quantity = 0
		for building in self.production_buildings:
			if building.id == BUILDINGS.FARM_CLASS:
				produce_quantity += 2
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

		(data, keys) = self._get_collector_data()
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		options = []

		checked_resources = False
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

			if not checked_resources:
				checked_resources = True
				if not builder.have_resources():
					return (True, False)

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
				return (None, False)
			for coords in builder.position.tuple_iter():
				self.plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
			self.plan[sorted(builder.position.tuple_iter())[0]] = (PRODUCTION_PURPOSE.STORAGE, builder)
			self.collector_buildings.append(building)
			return (builder, True)
		return (None, False)

	def count_fishers(self):
		fishers = 0
		for building in self.production_buildings:
			if building.id == BUILDINGS.FISHERMAN_CLASS:
				fishers += 1
		return fishers

	def count_potato_fields(self):
		potato_fields = 0
		for building in self.production_buildings:
			if building.id == BUILDINGS.POTATO_FIELD_CLASS:
				potato_fields += 1
		return potato_fields

	def refresh_unused_fields(self):
		self.unused_fields = deque()
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose == PRODUCTION_PURPOSE.FARM_FIELD:
				self.unused_fields.append(coords)

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
		farm_field_colour = (255, 0, 128)
		potato_field_colour = (0, 128, 0)
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
			elif purpose == PRODUCTION_PURPOSE.FARM_FIELD:
				renderer.addColored(tile._instance, *farm_field_colour)
			elif purpose == PRODUCTION_PURPOSE.POTATO_FIELD:
				renderer.addColored(tile._instance, *potato_field_colour)
			elif purpose == PRODUCTION_PURPOSE.RESERVED:
				renderer.addColored(tile._instance, *reserved_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

decorators.bind_all(ProductionBuilder)
