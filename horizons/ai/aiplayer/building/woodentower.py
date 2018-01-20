# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

class AbstractWoodenTower(AbstractBuilding):
	@property
	def evaluator_class(self):
		return WoodenTowerEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.WOODEN_TOWER] = cls

class WoodenTowerEvaluator(BuildingEvaluator):
	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = BasicBuilder.create(BUILDINGS.WOODEN_TOWER, (x, y), orientation)
		
		distance_to_collector = cls._distance_to_nearest_collector(area_builder, builder)
		if distance_to_collector is None:
			return None

		distance_to_villagebuilding = cls._distance_to_nearest_building(area_builder, builder, BUILDINGS.MAIN_SQUARE)
		alignment = cls._get_alignment(area_builder, builder.position.tuple_iter())

		personality = area_builder.owner.personality_manager.get('WoodenTowerEvaluator')
		distance_penalty = Entities.buildings[BUILDINGS.WOODEN_TOWER].radius * personality.distance_penalty

		distance = cls._weighted_distance(distance_to_collector, [(personality.villagebuilding_distance_importance, distance_to_villagebuilding)],
			distance_penalty)
		value = float(Entities.buildings[BUILDINGS.WOODEN_TOWER].radius) / distance + alignment * personality.alignment_importance
		return WoodenTowerEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.WOODEN_TOWER

AbstractWoodenTower.register_buildings()
