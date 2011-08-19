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
from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS
from horizons.entities import Entities

class BoatBuilderEvaluator(BuildingEvaluator):
	def __init__(self, area_builder, builder, distance_to_collector, alignment):
		super(BoatBuilderEvaluator, self).__init__(area_builder, builder)
		self.distance_to_collector = distance_to_collector
		self.alignment = alignment
		personality = area_builder.owner.personality_manager.get('BoatBuilderEvaluator')
		self.value = float(Entities.buildings[BUILDINGS.BOATBUILDER_CLASS].radius) / distance_to_collector + alignment * personality.alignment_importance

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.BOATBUILDER_CLASS, x, y, True, orientation)
		if not builder:
			return None

		distance_to_collector = cls.distance_to_nearest_collector(area_builder, builder)
		if distance_to_collector is None:
			return None # require boat builders to have a collector building in range

		alignment = cls.get_alignment(area_builder, builder.position.tuple_iter())
		return BoatBuilderEvaluator(area_builder, builder, distance_to_collector, alignment)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.BOAT_BUILDER

decorators.bind_all(BoatBuilderEvaluator)
