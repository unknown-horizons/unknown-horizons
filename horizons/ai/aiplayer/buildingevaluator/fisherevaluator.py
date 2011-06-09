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

from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS

class FisherEvaluator(BuildingEvaluator):
	refill_cycle_in_tiles = 12
	fisher_range = 16

	def __init__(self, production_builder, builder, fishers_in_range, fish_value):
		super(FisherEvaluator, self).__init__(production_builder, builder)
		self.fishers_in_range = fishers_in_range
		self.fish_value = fish_value
		self.value = fish_value / fishers_in_range

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
		if not self.production_builder.have_resources(BUILDINGS.FISHERMAN_CLASS):
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

decorators.bind_all(FisherEvaluator)
