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

class SignalFireEvaluator(BuildingEvaluator):
	need_collector_connection = False

	def __init__(self, area_builder, builder, sea_area, alignment):
		super(SignalFireEvaluator, self).__init__(area_builder, builder)
		self.sea_area = sea_area
		self.alignment = alignment
		self.value = sea_area + alignment * 1.5

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.SIGNAL_FIRE_CLASS, x, y, cls.need_collector_connection, orientation)
		if not builder:
			return None

		sea_area = 0
		for coords in builder.position.get_radius_coordinates(Entities.buildings[BUILDINGS.SIGNAL_FIRE_CLASS].radius):
			if coords in area_builder.session.world.water:
				sea_area += 1

		alignment = cls.get_alignment(area_builder, builder.position.tuple_iter())
		return SignalFireEvaluator(area_builder, builder, sea_area, alignment)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.SIGNAL_FIRE

decorators.bind_all(SignalFireEvaluator)
