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

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.constants import BUILDINGS
from horizons.util.python import decorators
from horizons.entities import Entities

class AbstractSaltPonds(AbstractBuilding):
	@property
	def evaluator_class(self):
		return SaltPondsEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.SALT_PONDS] = cls

class SaltPondsEvaluator(BuildingEvaluator):
	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.SALT_PONDS, x, y, True, orientation)
		if not builder:
			return None

		alignment = cls._get_alignment(area_builder, builder.position.tuple_iter())
		return SaltPondsEvaluator(area_builder, builder, alignment)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.SALT_PONDS

AbstractSaltPonds.register_buildings()

decorators.bind_all(AbstractSaltPonds)
decorators.bind_all(SaltPondsEvaluator)
