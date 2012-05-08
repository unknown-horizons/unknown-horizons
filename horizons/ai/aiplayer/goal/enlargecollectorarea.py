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

from collections import deque, defaultdict

from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.util.python import decorators
from horizons.constants import BUILDINGS
from horizons.util import Rect
from horizons.entities import Entities

class EnlargeCollectorAreaGoal(SettlementGoal):
	"""Enlarge the area of the island covered by collectors."""

	def get_personality_name(self):
		return 'EnlargeCollectorAreaGoal'

	@property
	def active(self):
		return super(EnlargeCollectorAreaGoal, self).active and self._is_active

	def update(self):
		available_squares, total_squares = self.settlement_manager.production_builder.count_available_squares(3, self.personality.max_interesting_collector_area)
		self.log.info('%s collector area: %d of %d useable', self, available_squares, total_squares)
		self._is_active = available_squares < min(self.personality.max_interesting_collector_area, total_squares - self.personality.max_collector_area_unreachable)

	def _enlarge_collector_area(self):
		if not self.production_builder.have_resources(BUILDINGS.STORAGE):
			return BUILD_RESULT.NEED_RESOURCES

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)] # valid moves for collectors
		collector_area = self.production_builder.get_collector_area()

		# area_label contains free tiles in the production area and all road tiles
		area_label = dict.fromkeys(self.land_manager.roads) # {(x, y): area_number, ...}
		for coords, (purpose, _) in self.production_builder.plan.iteritems():
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
			if coords in self.production_builder.plan and self.production_builder.plan[coords][0] == BUILDING_PURPOSE.NONE and coords not in collector_area:
				coords_set_by_area[area_number].add(coords)

		options = []
		for (x, y), area_number in area_label.iteritems():
			builder = self.production_builder.make_builder(BUILDINGS.STORAGE, x, y, False)
			if not builder:
				continue

			coords_set = set(builder.position.get_radius_coordinates(Entities.buildings[BUILDINGS.STORAGE].radius))
			useful_area = len(coords_set_by_area[area_number].intersection(coords_set))
			if not useful_area:
				continue

			alignment = 1
			for tile in self.production_builder.iter_neighbour_tiles(builder.position):
				coords = (tile.x, tile.y)
				if coords not in self.production_builder.plan or self.production_builder.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			value = useful_area + alignment * self.personality.alignment_coefficient
			options.append((value, builder))

		if options:
			return self.production_builder.build_best_option(options, BUILDING_PURPOSE.STORAGE)

		# enlarge the settlement area instead since just enlarging the collector area is impossible
		if self.village_builder.tent_queue:
			tent_size = Entities.buildings[BUILDINGS.RESIDENTIAL].size
			tent_radius = Entities.buildings[BUILDINGS.RESIDENTIAL].radius
			best_coords = None
			best_area = 0

			for x, y in self.village_builder.tent_queue:
				new_area = 0
				for coords in Rect.init_from_topleft_and_size(x, y, tent_size[0], tent_size[1]).get_radius_coordinates(tent_radius):
					if coords in area_label and coords not in self.land_manager.roads and coords not in collector_area:
						new_area += 1
				if new_area > best_area:
					best_coords = (x, y)
					best_area = new_area
			if best_coords is not None:
				return self.production_builder.extend_settlement_with_tent(Rect.init_from_topleft_and_size_tuples(best_coords, tent_size))
		return BUILD_RESULT.IMPOSSIBLE

	def execute(self):
		result = self._enlarge_collector_area()
		self._log_generic_build_result(result, 'storage coverage building')
		return self._translate_build_result(result)

decorators.bind_all(EnlargeCollectorAreaGoal)
