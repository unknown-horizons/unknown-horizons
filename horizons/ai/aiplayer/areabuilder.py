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

import copy
import logging
from collections import deque

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.ai.aiplayer.roadplanner import RoadPlanner
from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.util.shapes import Rect
from horizons.util.worldobject import WorldObject


class AreaBuilder(WorldObject):
	"""A class governing the use of a specific type of area of a settlement."""

	log = logging.getLogger("ai.aiplayer.area_builder")

	def __init__(self, settlement_manager):
		super().__init__()
		self.__init(settlement_manager)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self.land_manager = settlement_manager.land_manager
		self.island = self.land_manager.island
		self.session = self.island.session
		self.owner = self.land_manager.owner
		self.settlement = self.land_manager.settlement
		self.plan = {} # {(x, y): (purpose, subclass specific data), ...}

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def _load(self, db, settlement_manager, worldid):
		self.__init(settlement_manager)
		super().load(db, worldid)

	def iter_neighbor_tiles(self, rect):
		"""Iterate over the tiles that share a side with the given Rect."""
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		for x, y in rect.tuple_iter():
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if not rect.contains_tuple(coords):
					yield self.island.get_tile_tuple(coords)

	def iter_possible_road_coords(self, rect, blocked_rect):
		"""Iterate over the possible road tiles that share a side with
		the given Rect and are not in the blocked Rect."""
		blocked_coords_set = {coords for coords in blocked_rect.tuple_iter()}
		for tile in self.iter_neighbor_tiles(rect):
			if tile is None:
				continue
			coords = (tile.x, tile.y)
			if coords in blocked_coords_set or coords in self.land_manager.coastline or coords not in self.settlement.ground_map:
				continue
			if coords in self.land_manager.roads or (coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE):
				yield coords

	@classmethod
	def __fill_distance(cls, distance, nodes):
		"""Fill the distance dict with the shortest distance from the starting nodes.

		@param distance: {(x, y): distance, ...}
		@param nodes: {(x, y): penalty, ...}
		"""

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		queue = deque([item for item in distance.items()])

		while queue:
			(coords, dist) = queue.popleft()
			for dx, dy in moves:
				coords2 = (coords[0] + dx, coords[1] + dy)
				if coords2 in nodes and coords2 not in distance:
					distance[coords2] = dist + 1
					queue.append((coords2, dist + 1))

	def get_path_nodes(self):
		"""Return a dict {(x, y): penalty, ...}
		of current and possible future road tiles in the settlement."""
		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

		nodes = {} # {(x, y): penalty, ...}
		distance_to_road = {}
		distance_to_boundary = {}
		for coords in self.plan:
			if coords not in self.settlement.ground_map or coords in self.land_manager.coastline:
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
			if coords in self.land_manager.roads and coords in self.settlement.ground_map:
				nodes[coords] = 1
				distance_to_road[coords] = 0
				for (dx, dy) in moves:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in self.land_manager.production:
						distance_to_boundary[coords] = 1
						break

		self.__fill_distance(distance_to_road, self.island.path_nodes.nodes)
		self.__fill_distance(distance_to_boundary, self.island.path_nodes.nodes)

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
		"""Return a path from the builder to a building with general
		collectors (None if impossible)."""
		loading_area = builder.get_loading_area()
		collector_coords = set()
		for building in self.collector_buildings:
			if loading_area.distance(building.position) == 1:
				return []
			if loading_area.distance(building.position) > building.radius:
				continue # the collector building is too far to be useful
			for coords in self.iter_possible_road_coords(building.position, building.position):
				collector_coords.add(coords)

		destination_coords = set(self.iter_possible_road_coords(loading_area, builder.position))
		if self is self.settlement_manager.production_builder:
			if not self.settlement_manager.production_builder.road_connectivity_cache.is_connection_possible(collector_coords, destination_coords):
				return None

		blocked_coords = {coords for coords in builder.position.tuple_iter()}.union(self.land_manager.coastline)
		beacon = Rect.init_from_borders(loading_area.left - 1, loading_area.top - 1,
		                                loading_area.right + 1, loading_area.bottom + 1)

		return RoadPlanner()(self.owner.personality_manager.get('RoadPlanner'), collector_coords,
			destination_coords, beacon, self.get_path_nodes(), blocked_coords=blocked_coords)

	def build_road(self, path):
		"""Build the road given a valid path or None.
		Return True if it worked, False if the path was None."""
		if path is not None:
			for x, y in path:
				self.register_change_list([(x, y)], BUILDING_PURPOSE.ROAD, None)
				building = self.island.ground_map[(x, y)].object
				if building is not None and building.id == BUILDINGS.TRAIL:
					continue
				assert BasicBuilder(BUILDINGS.TRAIL, (x, y), 0).execute(self.land_manager)
		return path is not None

	def build_road_connection(self, builder):
		"""Build a road connecting the builder to a building with general collectors.

		Return True if it worked, False if the path was None."""
		path = self._get_road_to_builder(builder)
		return self.build_road(path)

	def get_road_cost(self, path):
		"""Return the cost of building a road on the given path as {resource_id: amount, ...} or None if impossible."""
		if path is None:
			return None
		length = 0
		if path is not None:
			for x, y in path:
				building = self.island.ground_map[(x, y)].object
				if building is None or building.id != BUILDINGS.TRAIL:
					length += 1
		if length == 0:
			return {}
		costs = copy.copy(Entities.buildings[BUILDINGS.TRAIL].costs)
		for resource in costs:
			costs[resource] *= length
		return costs

	def get_road_connection_cost(self, builder):
		"""Return the cost of building a road from the builder to a building with general collectors.

		The returned format is {resource_id: amount, ...} if it is possible to build a road and None otherwise.
		"""
		return self.get_road_cost(self._get_road_to_builder(builder))

	def have_resources(self, building_id):
		"""Return a boolean showing whether we currently have the resources to build a building of the given type."""
		return Entities.buildings[building_id].have_resources([self.settlement], self.owner)

	def build_best_option(self, options, purpose):
		"""Try to build the highest valued option.
		Return a BUILD_RESULT constant showing how it went.

		@param options: [(value, builder), ...]
		@param purpose: a BUILDING_PURPOSE constant
		"""

		if not options:
			return BUILD_RESULT.IMPOSSIBLE

		best_index = 0
		best_value = options[0][0]
		for i in range(1, len(options)):
			if options[i][0] > best_value:
				best_index = i
				best_value = options[i][0]

		builder = options[best_index][1]
		if not builder.execute(self.land_manager):
			return BUILD_RESULT.UNKNOWN_ERROR
		self.register_change_list(list(builder.position.tuple_iter()), BUILDING_PURPOSE.RESERVED, None)
		self.register_change_list([builder.position.origin.to_tuple()], purpose, None)
		return BUILD_RESULT.OK

	def extend_settlement(self, position):
		"""Build a storage to extend the settlement towards the given position.

		Return a BUILD_RESULT constant."""
		return self.settlement_manager.production_builder.extend_settlement_with_storage(position)

	def handle_lost_area(self, coords_list):
		"""Handle losing the potential land in the given coordinates list."""
		# remove the affected tiles from the plan
		for coords in coords_list:
			if coords in self.plan:
				del self.plan[coords]

	def add_building(self, building):
		"""Called when a new building is added in the area (the building already exists during the call)."""
		self.display()

	def remove_building(self, building):
		"""Called when a building is removed from the area (the building still exists during the call)."""
		self.display()

	def display(self):
		"""Show the plan on the map unless it is disabled in the settings."""
		raise NotImplementedError('This function has to be overridden.')

	def _init_cache(self):
		"""Initialize the cache that knows the last time the buildability of a rectangle may have changed in this area."""
		self.last_change_id = -1

	def register_change(self, x, y, purpose, data):
		"""Register the (potential) change of the purpose of land at the given coordinates."""
		if (x, y) in self.plan:
			self.plan[(x, y)] = (purpose, data)
			if purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add((x, y))

	def register_change_list(self, coords_list, purpose, data):
		for (x, y) in coords_list:
			self.register_change(x, y, purpose, data)
