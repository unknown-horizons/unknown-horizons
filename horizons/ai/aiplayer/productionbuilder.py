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

from areabuilder import AreaBuilder
from builder import Builder
from constants import BUILD_RESULT, BUILDING_PURPOSE

from horizons.constants import AI, BUILDINGS, RES
from horizons.util import Point
from horizons.util.python import decorators

class ProductionBuilder(AreaBuilder):
	def __init__(self, settlement_manager):
		super(ProductionBuilder, self).__init__(settlement_manager)
		self.__init(settlement_manager)
		self.plan = dict.fromkeys(self.land_manager.production, (BUILDING_PURPOSE.NONE, None))
		for coords in settlement_manager.branch_office.position.tuple_iter():
			if coords in self.plan:
				self.plan[coords] = (BUILDING_PURPOSE.BRANCH_OFFICE, None)

	def __init(self, settlement_manager):
		self.collector_buildings = [settlement_manager.branch_office]
		self.production_buildings = []
		self.unused_fields = self._make_empty_unused_fields()

	@classmethod
	def _make_empty_unused_fields(self):
		return {
			BUILDING_PURPOSE.POTATO_FIELD: deque(),
			BUILDING_PURPOSE.PASTURE: deque(),
			BUILDING_PURPOSE.SUGARCANE_FIELD: deque(),
		}

	def save(self, db):
		super(ProductionBuilder, self).save(db, 'ai_production_builder_coords')
		db("INSERT INTO ai_production_builder(rowid, settlement_manager) VALUES(?, ?)", self.worldid, \
			self.settlement_manager.worldid)

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
			elif purpose == BUILDING_PURPOSE.STORAGE and object.id == BUILDINGS.STORAGE_CLASS:
				self.collector_buildings.append(object)

		self.refresh_unused_fields()

	def _near_collectors(self, position):
		for building in self.collector_buildings:
			if building.position.distance(position) <= building.radius:
				return True
		return False

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
			if purpose == BUILDING_PURPOSE.NONE:
				cell_value[coords] = 3
			elif purpose == BUILDING_PURPOSE.TREE:
				cell_value[coords] = 1
			else:
				continue

			alignment = 0
			for dx, dy in moves:
				coords2 = (coords[0] + dx, coords[1] + dy)
				if coords2 not in self.plan or self.plan[coords][0] == BUILDING_PURPOSE.ROAD:
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
				self.plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
			self.plan[sorted(lumberjack.position.tuple_iter())[0]] = (BUILDING_PURPOSE.LUMBERJACK, lumberjack)

			for coords in lumberjack.position.get_radius_coordinates(3):
				if coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE:
					self.plan[coords] = (BUILDING_PURPOSE.TREE, None)
					tree = Builder.create(BUILDINGS.TREE_CLASS, self.land_manager, Point(coords[0], coords[1])).execute()
			self.production_buildings.append(building)
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

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
			builder = self.make_builder(BUILDINGS.STORAGE_CLASS, x, y, True)
			if not builder:
				continue

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
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
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
				self.plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
			self.plan[sorted(builder.position.tuple_iter())[0]] = (BUILDING_PURPOSE.STORAGE, builder)
			self.collector_buildings.append(building)
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def count_fields(self):
		fields = {BUILDING_PURPOSE.POTATO_FIELD: 0, BUILDING_PURPOSE.PASTURE: 0}
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
			if purpose == BUILDING_PURPOSE.UNUSED_POTATO_FIELD:
				self.unused_fields[BUILDING_PURPOSE.POTATO_FIELD].append(coords)
			elif purpose == BUILDING_PURPOSE.UNUSED_PASTURE:
				self.unused_fields[BUILDING_PURPOSE.PASTURE].append(coords)
			elif purpose == BUILDING_PURPOSE.UNUSED_SUGARCANE_FIELD:
				self.unused_fields[BUILDING_PURPOSE.SUGARCANE_FIELD].append(coords)

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
			elif purpose == BUILDING_PURPOSE.UNUSED_POTATO_FIELD:
				renderer.addColored(tile._instance, *unused_potato_field_colour)
			elif purpose == BUILDING_PURPOSE.POTATO_FIELD:
				renderer.addColored(tile._instance, *potato_field_colour)
			elif purpose == BUILDING_PURPOSE.UNUSED_PASTURE:
				renderer.addColored(tile._instance, *unused_pasture_colour)
			elif purpose == BUILDING_PURPOSE.PASTURE:
				renderer.addColored(tile._instance, *pasture_colour)
			elif purpose == BUILDING_PURPOSE.WEAVER:
				renderer.addColored(tile._instance, *weaver_colour)
			elif purpose == BUILDING_PURPOSE.UNUSED_SUGARCANE_FIELD:
				renderer.addColored(tile._instance, *unused_sugarcane_field_colour)
			elif purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
				renderer.addColored(tile._instance, *sugarcane_field_colour)
			elif purpose == BUILDING_PURPOSE.DISTILLERY:
				renderer.addColored(tile._instance, *distillery_colour)
			elif purpose == BUILDING_PURPOSE.CLAY_PIT:
				renderer.addColored(tile._instance, *clay_pit_colour)
			elif purpose == BUILDING_PURPOSE.BRICKYARD:
				renderer.addColored(tile._instance, *brickyard_colour)
			elif purpose == BUILDING_PURPOSE.RESERVED:
				renderer.addColored(tile._instance, *reserved_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

decorators.bind_all(ProductionBuilder)
