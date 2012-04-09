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

class AbstractSmeltery(AbstractBuilding):
	@property
	def evaluator_class(self):
		return SmelteryEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.SMELTERY] = cls

class SmelteryEvaluator(BuildingEvaluator):
	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.SMELTERY, x, y, True, orientation)
		if not builder:
			return None

		distance_to_iron_mine = cls._distance_to_nearest_building(area_builder, builder, BUILDINGS.IRON_MINE)
		distance_to_collector = cls._distance_to_nearest_collector(area_builder, builder)
		distance_to_charcoal_burner = cls._distance_to_nearest_building(area_builder, builder, BUILDINGS.CHARCOAL_BURNER)
		if distance_to_collector is None and (distance_to_charcoal_burner is None or distance_to_iron_mine is None):
			return None

		personality = area_builder.owner.personality_manager.get('SmelteryEvaluator')
		distance_penalty = Entities.buildings[BUILDINGS.SMELTERY].radius * personality.distance_penalty

		alignment = cls._get_alignment(area_builder, builder.position.tuple_iter())
		distance = cls._weighted_distance(distance_to_iron_mine, [(personality.collector_distance_importance, distance_to_collector), \
			(personality.charcoal_burner_distance_importance, distance_to_charcoal_burner)], distance_penalty)
		value = float(Entities.buildings[BUILDINGS.SMELTERY].radius) / distance + alignment * personality.alignment_importance
		return SmelteryEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.SMELTERY

AbstractSmeltery.register_buildings()

decorators.bind_all(AbstractSmeltery)
decorators.bind_all(SmelteryEvaluator)
