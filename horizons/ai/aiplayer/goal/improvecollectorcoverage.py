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

from collections import deque

from horizons.ai.aiplayer.roadplanner import RoadPlanner
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, RES, PRODUCTION
from horizons.scheduler import Scheduler
from horizons.util import Rect
from horizons.entities import Entities
from horizons.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer

class ImproveCollectorCoverageGoal(SettlementGoal):
	def get_personality_name(self):
		return 'ImproveCollectorCoverageGoal'

	@property
	def active(self):
		return super(ImproveCollectorCoverageGoal, self).active and self._is_active

	def _get_problematic_collector_coverage_buildings(self):
		problematic_buildings = {}
		for building in self.production_builder.production_buildings:
			for production in building.get_component(Producer).get_productions():
				if production.get_age() < 1.5 * PRODUCTION.STATISTICAL_WINDOW:
					continue
				history = production.get_state_history_times(False)
				# take paused time into account because the AI pauses the production when the output storage is full
				amount_paused = history[PRODUCTION.STATES.inventory_full.index] + history[PRODUCTION.STATES.paused.index]
				if amount_paused < self.personality.min_bad_collector_coverage:
					continue
				for resource_id in production.get_produced_resources():
					if self.settlement.get_component(StorageComponent).inventory.get_free_space_for(resource_id) > self.personality.min_free_space:
						# this is actually problematic
						problematic_buildings[building.worldid] = building
		return problematic_buildings.values()

	def update(self):
		if self.production_builder.last_collector_improvement_road + self.personality.collector_improvement_road_expires > Scheduler().cur_tick:
			# skip this goal leave time for the collectors to do their work
			self._problematic_buildings = None
			self._is_active = False
		else:
			self._problematic_buildings = self._get_problematic_collector_coverage_buildings()
			self._is_active = bool(self._problematic_buildings)

	def _build_extra_road_connection(self, building, collector_building):
		collector_coords = set(coords for coords in self.production_builder.iter_possible_road_coords(collector_building.position, collector_building.position))
		destination_coords = set(coords for coords in self.production_builder.iter_possible_road_coords(building.loading_area, building.position))
		pos = building.loading_area
		beacon = Rect.init_from_borders(pos.left - 1, pos.top - 1, pos.right + 1, pos.bottom + 1)

		path = RoadPlanner()(self.owner.personality_manager.get('RoadPlanner'), collector_coords,
			destination_coords, beacon, self.production_builder.get_path_nodes())
		if path is None:
			return BUILD_RESULT.IMPOSSIBLE

		cost = self.production_builder.get_road_cost(path)
		for resource_id, amount in cost.iteritems():
			if resource_id == RES.GOLD:
				if self.owner.get_component(StorageComponent).inventory[resource_id] < amount:
					return BUILD_RESULT.NEED_RESOURCES
			elif self.settlement.get_component(StorageComponent).inventory[resource_id] < amount:
				return BUILD_RESULT.NEED_RESOURCES
		return BUILD_RESULT.OK if self.production_builder.build_road(path) else BUILD_RESULT.UNKNOWN_ERROR

	def _build_extra_road(self):
		"""Build an extra road between a storage building and a producer building."""
		current_tick = Scheduler().cur_tick

		# which collectors could have actual unused capacity?
		usable_collectors = []
		for building in self.production_builder.collector_buildings:
			if building.get_utilisation_history_length() < 1000 or building.get_collector_utilisation() < self.personality.max_good_collector_utilisation:
				usable_collectors.append(building)

		# find possible problematic building to usable collector links
		potential_road_connections = []
		for building in self._problematic_buildings:
			for collector_building in usable_collectors:
				distance = building.loading_area.distance(collector_building.position)
				if distance > collector_building.radius:
					continue # out of range anyway
				# TODO: check whether the link already exists
				potential_road_connections.append((distance * collector_building.get_collector_utilisation(), building, collector_building))

		# try the best link from the above list
		for _, building, collector_building in sorted(potential_road_connections):
			result = self._build_extra_road_connection(building, collector_building)
			if result == BUILD_RESULT.OK:
				self.production_builder.last_collector_improvement_road = current_tick
				self.log.info('%s connected %s at %d, %d with %s at %d, %d', self, building.name, building.position.origin.x,
					building.position.origin.y, collector_building.name, collector_building.position.origin.x, collector_building.position.origin.y)
			return result
		self.log.info('%s found no good way to connect buildings that need more collectors to existing collector buildings', self)
		return BUILD_RESULT.IMPOSSIBLE

	def _build_extra_storage(self):
		"""Build an extra storage tent to improve collector coverage."""
		if not self.production_builder.have_resources(BUILDINGS.STORAGE):
			return BUILD_RESULT.NEED_RESOURCES

		reachable = dict.fromkeys(self.land_manager.roads) # {(x, y): [(building worldid, distance), ...], ...}
		for coords, (purpose, _) in self.production_builder.plan.iteritems():
			if purpose == BUILDING_PURPOSE.NONE:
				reachable[coords] = []
		for key in reachable:
			if reachable[key] is None:
				reachable[key] = []

		storage_radius = Entities.buildings[BUILDINGS.STORAGE].radius
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		for building in self._problematic_buildings:
			distance = dict.fromkeys(reachable)
			queue = deque()
			for coords in self.production_builder.iter_possible_road_coords(building.loading_area, building.position):
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
			builder = self.production_builder.make_builder(BUILDINGS.STORAGE, x, y, False)
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
			for tile in self.production_builder.iter_neighbour_tiles(builder.position):
				coords = (tile.x, tile.y)
				if coords not in self.production_builder.plan or self.production_builder.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			value = usefulness + alignment * self.personality.alignment_coefficient
			options.append((value, builder))

		return self.production_builder.build_best_option(options, BUILDING_PURPOSE.STORAGE)

	def execute(self):
		result = self._build_extra_road()
		if result == BUILD_RESULT.IMPOSSIBLE:
			if self.production_builder.last_collector_improvement_storage + self.personality.collector_improvement_storage_expires <= Scheduler().cur_tick:
				result = self._build_extra_storage()
				if result == BUILD_RESULT.OK:
					self.production_builder.last_collector_improvement_storage = Scheduler().cur_tick
		self._log_generic_build_result(result, 'storage')
		return self._translate_build_result(result)

decorators.bind_all(ImproveCollectorCoverageGoal)
