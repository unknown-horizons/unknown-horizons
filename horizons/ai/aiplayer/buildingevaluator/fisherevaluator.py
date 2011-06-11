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
import math
import heapq

from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, COLLECTORS, RES

class FisherEvaluator(BuildingEvaluator):
	refill_cycle_in_tiles = 12
	fisher_range = 16

	def __init__(self, production_builder, builder, fishers_in_range, fish_value):
		super(FisherEvaluator, self).__init__(production_builder, builder)
		self.fishers_in_range = fishers_in_range
		self.fish_value = fish_value
		self.value = fish_value / fishers_in_range
		self.production_level = None

	def get_expected_production_level(self, resource_id):
		assert resource_id == RES.FOOD_ID
		if self.production_level is None:
			fishers_coords = [fisher.position.origin.to_tuple() for fisher in self.production_builder.owner.fishers]
			self.production_level = FisherSimulator.extra_productivity(self.production_builder.session, \
				fishers_coords, self.builder.position.origin.to_tuple())
		max_possible = self.production_builder.owner.virtual_fisher.get_expected_production_level(resource_id)
		return min(self.production_level, max_possible)

	@classmethod
	def create(cls, production_builder, x, y):
		builder = production_builder.make_builder(BUILDINGS.FISHERMAN_CLASS, x, y, True)
		if not builder:
			return None

		fishers_in_range = 1.0
		for other_fisher in production_builder.owner.fishers:
			distance = builder.position.distance(other_fisher.position)
			if distance < cls.fisher_range:
				fishers_in_range += 1 - distance / float(cls.fisher_range)

		tiles_used = 0
		fish_value = 0.0
		for fish in production_builder.session.world.fish_indexer.get_buildings_in_range((x, y)):
			if tiles_used >= 3 * cls.refill_cycle_in_tiles:
				break
			distance = builder.position.distance(fish.position) + 1.0
			if tiles_used >= cls.refill_cycle_in_tiles:
				fish_value += min(1.0, (3 * cls.refill_cycle_in_tiles - tiles_used) / distance) / 10.0
			else:
				fish_value += min(1.0, (cls.refill_cycle_in_tiles - tiles_used) / distance)
			tiles_used += distance

		if fish_value == 0:
			return None
		return FisherEvaluator(production_builder, builder, fishers_in_range, fish_value)

	def execute(self):
		if not self.production_builder.have_resources(self.builder.building_id):
			return BUILD_RESULT.NEED_RESOURCES
		if not self.production_builder._build_road_connection(self.builder):
			return BUILD_RESULT.IMPOSSIBLE
		building = self.builder.execute()
		if not building:
			return BUILD_RESULT.UNKNOWN_ERROR
		self.production_builder.owner.fishers.append(self.builder)
		for coords in self.builder.position.tuple_iter():
			self.production_builder.plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
		self.production_builder.plan[sorted(self.builder.position.tuple_iter())[0]] = (PRODUCTION_PURPOSE.FISHER, self.builder)
		self.production_builder.production_buildings.append(building)
		return BUILD_RESULT.OK

class FisherSimulator(object):
	# TODO: get these values the right way
	move_time = 12 # in ticks
	fish_respawn_time = 480 # 30 seconds in ticks
	simulation_time = 4800 # 5 minutes in ticks

	@classmethod
	def extra_productivity(cls, session, fishers, coords):
		fish_indexer = session.world.fish_indexer
		old_productivity = cls.simulate(fish_indexer, fishers)
		new_list = copy.copy(fishers)
		new_list.append(coords)
		return cls.simulate(fish_indexer, new_list) - old_productivity

	@classmethod
	def simulate(cls, fish_indexer, fishers):
		if not fishers:
			return 0

		fish_map = {} # (x, y); tick_available
		heap = [] # (tick, fisher_coords)
		for fisher_coords in fishers:
			for fish in fish_indexer.get_buildings_in_range(fisher_coords):
				fish_map[fish.position.origin.to_tuple()] = 0
			heap.append((0, fisher_coords))
		heapq.heapify(heap)

		fish_caught = 0
		while True:
			(tick, fisher_coords) = heapq.heappop(heap)
			if tick > cls.simulation_time:
				break # simulate for 1 minute

			found_fish = False
			for fish in fish_indexer.get_buildings_in_range(fisher_coords):
				fish_coords = fish.position.origin.to_tuple()
				if fish_map[fish_coords] > tick:
					continue
				distance = math.sqrt((fish_coords[0] - fisher_coords[0]) ** 2 + (fish_coords[1] - fisher_coords[1]) ** 2)
				move_time = cls.move_time * int(round(distance))
				fish_map[fish_coords] = tick + move_time + COLLECTORS.DEFAULT_WORK_DURATION + cls.fish_respawn_time
				if tick + 2 * move_time + COLLECTORS.DEFAULT_WORK_DURATION <= cls.simulation_time:
					fish_caught += 1
				next_time = tick + 2 * move_time + COLLECTORS.DEFAULT_WORK_DURATION + COLLECTORS.DEFAULT_WAIT_TICKS
				heapq.heappush(heap, (next_time, fisher_coords))
				found_fish = True
				break

			if not found_fish:
				heapq.heappush(heap, (tick +  COLLECTORS.DEFAULT_WAIT_TICKS, fisher_coords))
		return float(fish_caught) / cls.simulation_time

decorators.bind_all(FisherEvaluator)
decorators.bind_all(FisherSimulator)
