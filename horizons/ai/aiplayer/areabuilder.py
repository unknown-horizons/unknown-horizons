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
import logging

from collections import deque

from builder import Builder
from roadplanner import RoadPlanner

from horizons.ai.aiplayer.constants import BUILDING_PURPOSE, BUILD_RESULT
from horizons.constants import BUILDINGS
from horizons.util import Point, Rect, WorldObject
from horizons.util.python import decorators
from horizons.entities import Entities

class AreaBuilder(WorldObject):
	log = logging.getLogger("ai.aiplayer")

	def __init__(self, settlement_manager):
		super(AreaBuilder, self).__init__()
		self.__init(settlement_manager)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self.land_manager = settlement_manager.land_manager
		self.island = self.land_manager.island
		self.session = self.island.session
		self.owner = self.land_manager.owner
		self.settlement = self.land_manager.settlement
		self.plan = {}
		self.builder_cache = {}

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def _load(self, db, settlement_manager, worldid):
		self.__init(settlement_manager)
		super(AreaBuilder, self).load(db, worldid)

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

	def _get_possible_road_coords(self, rect, blocked_rect):
		blocked_coords_set = set(coords for coords in blocked_rect.tuple_iter())
		for tile in self._get_neighbour_tiles(rect):
			if tile is None:
				continue
			coords = (tile.x, tile.y)
			if coords in blocked_coords_set:
				continue
			if coords in self.land_manager.roads or (coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE):
				yield coords

	def _fill_distance(self, distance, nodes):
		"""
		fills the distance dict with the shortest distance
		@param distance: {(x, y): distance, ...}
		@param nodes: {(x, y): penalty, ...}
		"""
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
		""" returns coordinates of current and possible future road tiles in the settlement """
		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

		nodes = {} # {(x, y): penalty, ...}
		distance_to_road = {}
		distance_to_boundary = {}
		for coords in self.plan:
			if coords not in self.settlement.ground_map:
				continue
			if self.plan[coords][0] == BUILDING_PURPOSE.NONE:
				nodes[coords] = 1
			elif self.plan[coords][0] == BUILDING_PURPOSE.ROAD:
				nodes[coords] = 1
				distance_to_road[coords] = 0

			for (dx, dy) in moves:
				coords2 = (coords[0] + dx, coords[1] + dy)
				if coords2 not in self.land_manager.production:
					distance_to_boundary[coords] = 1
					break

		for coords in self.land_manager.village:
			if coords in self.land_manager.roads:
				nodes[coords] = 1
				distance_to_road[coords] = 0
				for (dx, dy) in moves:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in self.land_manager.production:
						distance_to_boundary[coords] = 1
						break

		self._fill_distance(distance_to_road, self.island.path_nodes.nodes)
		self._fill_distance(distance_to_boundary, self.island.path_nodes.nodes)

		for coords in nodes:
			if coords in distance_to_road:
				distance = distance_to_road[coords]
				if distance > self.personality.path_road_penalty_threshold:
					nodes[coords] += self.personality.path_distant_road_penalty
				elif distance > 0:
					nodes[coords] += self.personality.path_near_road_constant_penalty + \
						(self.personality.path_road_penalty_threshold - distance + 1) * self.personality.path_near_road_linear_penalty
			else:
				nodes[coords] += self.personality.path_unreachable_road_penalty

			if coords in distance_to_boundary:
				distance = distance_to_boundary[coords]
				if 1 < distance <= self.personality.path_boundary_penalty_threshold:
					nodes[coords] += self.personality.path_near_boundary_constant_penalty + \
						(self.personality.path_boundary_penalty_threshold - distance + 1) * self.personality.path_near_boundary_linear_penalty
			else:
				nodes[coords] += self.personality.path_unreachable_boundary_penalty

		return nodes

	def _get_road_to_builder(self, builder):
		loading_area = builder.get_loading_area()
		collector_coords = set()
		for building in self.collector_buildings:
			if loading_area.distance(building.position) == 1:
				return []
			if loading_area.distance(building.position) > building.radius:
				continue # the collector building is too far to be useful
			for coords in self._get_possible_road_coords(building.position, building.position):
				collector_coords.add(coords)

		blocked_coords = set([coords for coords in builder.position.tuple_iter()])
		destination_coords = set(self._get_possible_road_coords(loading_area, builder.position))
		beacon = Rect.init_from_borders(loading_area.left - 1, loading_area.top - 1, loading_area.right + 1, loading_area.bottom + 1)

		return RoadPlanner()(self.owner.personality_manager.get('RoadPlanner'), collector_coords, \
			destination_coords, beacon, self._get_path_nodes(), blocked_coords = blocked_coords)

	def _build_road(self, path):
		if path is not None:
			for x, y in path:
				self.register_change(x, y, BUILDING_PURPOSE.ROAD, None)
				building = self.island.ground_map[(x, y)].object
				if building is not None and building.id == BUILDINGS.TRAIL_CLASS:
					continue
				assert Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, Point(x, y)).execute()
		return path is not None

	def build_road_connection(self, builder):
		path = self._get_road_to_builder(builder)
		return self._build_road(path)

	def _get_road_cost(self, path):
		if path is None:
			return None
		length = 0
		if path is not None:
			for x, y in path:
				building = self.island.ground_map[(x, y)].object
				if building is None or building.id != BUILDINGS.TRAIL_CLASS:
					length += 1
		if length == 0:
			return {}
		costs = copy.copy(Entities.buildings[BUILDINGS.TRAIL_CLASS].costs)
		for resource in costs:
			costs[resource] *= length
		return costs

	def get_road_connection_cost(self, builder):
		return self._get_road_cost(self._get_road_to_builder(builder))

	def make_builder(self, building_id, x, y, needs_collector, orientation = 0):
		return Builder.create(building_id, self.land_manager, Point(x, y), orientation = orientation)

	def have_resources(self, building_id):
		return Entities.buildings[building_id].have_resources([self.settlement], self.owner)

	def _extend_settlement_with_tent(self, position):
		size = Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].size
		min_distance = None
		best_coords = None

		for (x, y) in self.settlement_manager.village_builder.tent_queue:
			ok = True
			for dx in xrange(size[0]):
				for dy in xrange(size[1]):
					if (x + dx, y + dy) not in self.settlement.ground_map:
						ok = False
						break
			if not ok:
				continue

			distance = Rect.init_from_topleft_and_size(x, y, size[0] - 1, size[1] - 1).distance(position)
			if min_distance is None or distance < min_distance:
				min_distance = distance
				best_coords = (x, y)

		if min_distance is None:
			return BUILD_RESULT.IMPOSSIBLE
		return self.settlement_manager.village_builder.build_tent(best_coords)

	def _extend_settlement_with_storage(self, position):
		options = []
		for x, y in self.plan:
			builder = self.make_builder(BUILDINGS.STORAGE_CLASS, x, y, True)
			if not builder:
				continue

			alignment = 1
			for tile in self._get_neighbour_tiles(builder.position):
				if tile is None:
					continue
				coords = (tile.x, tile.y)
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			distance = position.distance(builder.position)
			value = distance - alignment * 0.7
			options.append((value, builder))

		for _, builder in sorted(options):
			building = builder.execute()
			if not building:
				return BUILD_RESULT.UNKNOWN_ERROR
			for x, y in builder.position.tuple_iter():
				self.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
			self.register_change(builder.position.origin.x, builder.position.origin.y, BUILDING_PURPOSE.STORAGE, None)
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def extend_settlement(self, position):
		""" build a tent or a storage to extend the settlement towards the position """
		result = self._extend_settlement_with_tent(position)
		if result != BUILD_RESULT.OK:
			result = self._extend_settlement_with_storage(position)
		return result

	def handle_lost_area(self, coords_list):
		# remove the affected tiles from the plan
		for coords in coords_list:
			if coords in self.plan:
				del self.plan[coords]

	def add_building(self, building):
		""" called when a new building is added in the area (the building already exists during the call) """
		self.display()

	def remove_building(self, building):
		""" called when a building is removed from the area (the building still exists during the call) """
		self.display()

	def display(self):
		raise NotImplementedError, 'This function has to be overridden.'

	def _init_cache(self):
		""" initialises the cache that knows when the last time the buildability of a rectangle may have changed in this area """ 
		self.last_change_id = -1

	def register_change(self, x, y, purpose, data):
		if (x, y) in self.plan:
			self.plan[(x, y)] = (purpose, data)
			if purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add((x, y))

decorators.bind_all(AreaBuilder)
