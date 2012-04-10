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

class AbstractSignalFire(AbstractBuilding):
	def iter_potential_locations(self, settlement_manager):
		for (x, y) in settlement_manager.settlement.warehouse.position.get_radius_coordinates(self.radius):
			if (x, y) in settlement_manager.production_builder.plan:
				if (x, y) in settlement_manager.island.last_changed[self.size]:
					yield (x, y, 0)

	@property
	def evaluator_class(self):
		return SignalFireEvaluator

	@property
	def producer_building(self):
		""" signal fires don't produce anything """
		return False

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.SIGNAL_FIRE] = cls

class SignalFireEvaluator(BuildingEvaluator):
	need_collector_connection = False

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.SIGNAL_FIRE, x, y, cls.need_collector_connection, orientation)
		if not builder:
			return None

		sea_area = 0
		for coords in builder.position.get_radius_coordinates(Entities.buildings[BUILDINGS.SIGNAL_FIRE].radius):
			if coords in area_builder.session.world.water:
				sea_area += 1

		personality = area_builder.owner.personality_manager.get('SignalFireEvaluator')
		alignment = cls._get_alignment(area_builder, builder.position.tuple_iter())
		value = sea_area + alignment * personality.alignment_importance
		return SignalFireEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.SIGNAL_FIRE

AbstractSignalFire.register_buildings()

decorators.bind_all(AbstractSignalFire)
decorators.bind_all(SignalFireEvaluator)
