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

from collections import defaultdict, deque
from typing import List, Tuple

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.util.shapes import Rect


class EnlargeCollectorAreaGoal(SettlementGoal):
	"""Enlarge the area of the island covered by collectors."""
	_radius_offsets = None # type: List[Tuple[int, int]]

	@classmethod
	def _init_radius_offsets(cls):
		building_class = Entities.buildings[BUILDINGS.STORAGE]
		size = building_class.size
		assert size[0] == size[1]
		rect = Rect.init_from_topleft_and_size(0, 0, size[0], size[1])

		cls._radius_offsets = []
		for coords in rect.get_radius_coordinates(building_class.radius):
			cls._radius_offsets.append(coords)

	def get_personality_name(self):
		return 'EnlargeCollectorAreaGoal'

	@property
	def active(self):
		return super().active and self._is_active

	def update(self):
		available_squares, total_squares = self.settlement_manager.production_builder.count_available_squares(3, self.personality.max_interesting_collector_area)
		self.log.info('%s collector area: %d of %d useable', self, available_squares, total_squares)
		self._is_active = available_squares < min(self.personality.max_interesting_collector_area, total_squares - self.personality.max_collector_area_unreachable)

	def _enlarge_collector_area(self):
		if not self.production_builder.have_resources(BUILDINGS.STORAGE):
			return BUILD_RESULT.NEED_RESOURCES

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)] # valid moves for collectors
		collector_area = self.production_builder.get_collector_area()
		coastline = self.land_manager.coastline

		# area_label contains free tiles in the production area and all road tiles
		area_label = dict.fromkeys(self.land_manager.roads) # {(x, y): area_number, ...}
		for coords, (purpose, _) in self.production_builder.plan.items():
			if coords not in coastline and purpose == BUILDING_PURPOSE.NONE:
				area_label[coords] = None

		areas = 0
		for coords in collector_area:
			assert coords not in coastline
			if coords in area_label and area_label[coords] is not None:
				continue

			queue = deque([coords])
			while queue:
				x, y = queue.popleft()
				for dx, dy in moves:
					coords2 = (x + dx, y + dy)
					if coords2 in area_label and area_label[coords2] is None:
						area_label[coords2] = areas
						queue.append(coords2)
			areas += 1

		coords_set_by_area = defaultdict(set)
		for coords, area_number in area_label.items():
			if coords in self.production_builder.plan and self.production_builder.plan[coords][0] == BUILDING_PURPOSE.NONE and coords not in collector_area:
				coords_set_by_area[area_number].add(coords)

		storage_class = Entities.buildings[BUILDINGS.STORAGE]
		storage_spots = self.island.terrain_cache.get_buildability_intersection(storage_class.terrain_type,
			storage_class.size, self.settlement.buildability_cache, self.production_builder.buildability_cache)
		storage_surrounding_offsets = Rect.get_surrounding_offsets(storage_class.size)

		options = []
		num_offsets = int(len(self._radius_offsets) * self.personality.overlap_precision)
		radius_offsets = self.session.random.sample(self._radius_offsets, num_offsets)
		for coords in sorted(storage_spots):
			if coords not in area_label:
				continue
			x, y = coords

			area_number = area_label[coords]
			area_coords_set = coords_set_by_area[area_number]
			useful_area = 0
			for dx, dy in radius_offsets:
				coords = (x + dx, y + dy)
				if coords in area_coords_set:
					useful_area += 1
			if not useful_area:
				continue

			alignment = 1
			builder = BasicBuilder.create(BUILDINGS.STORAGE, (x, y), 0)
			for (dx, dy) in storage_surrounding_offsets:
				coords = (x + dx, y + dy)
				if coords in coastline or coords not in self.production_builder.plan or self.production_builder.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			value = useful_area + alignment * self.personality.alignment_coefficient
			options.append((value, builder))

		if options:
			return self.production_builder.build_best_option(options, BUILDING_PURPOSE.STORAGE)

		return BUILD_RESULT.IMPOSSIBLE

	def execute(self):
		if self._radius_offsets is None:
			self._init_radius_offsets()

		result = self._enlarge_collector_area()
		self._log_generic_build_result(result, 'storage coverage building')
		return self._translate_build_result(result)
