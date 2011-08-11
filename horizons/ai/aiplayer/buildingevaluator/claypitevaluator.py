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
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, RES

class ClayPitEvaluator(BuildingEvaluator):
	def __init__(self, area_builder, builder, distance_to_collector):
		super(ClayPitEvaluator, self).__init__(area_builder, builder)
		self.distance_to_collector = distance_to_collector
		self.value = 1.0 / (distance_to_collector + 1)

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.CLAY_PIT_CLASS, x, y, True, orientation)
		if not builder:
			return None

		distance_to_collector = cls.distance_to_nearest_collector(area_builder, builder, False)
		return ClayPitEvaluator(area_builder, builder, distance_to_collector)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.CLAY_PIT

decorators.bind_all(ClayPitEvaluator)
