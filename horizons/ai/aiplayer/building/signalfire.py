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

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.constants import BUILDINGS
from horizons.entities import Entities


class AbstractSignalFire(AbstractBuilding):
	@classmethod
	def _get_buildability_intersection(cls, settlement_manager, size, terrain_type, need_collector_connection):
		coords_set = super(AbstractSignalFire, cls)._get_buildability_intersection(settlement_manager, size, terrain_type, need_collector_connection)
		radius = Entities.buildings[BUILDINGS.SIGNAL_FIRE].radius
		return coords_set.intersection(set(settlement_manager.settlement.warehouse.position.get_radius_coordinates(radius)))

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
		builder = BasicBuilder.create(BUILDINGS.SIGNAL_FIRE, (x, y), orientation)

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
