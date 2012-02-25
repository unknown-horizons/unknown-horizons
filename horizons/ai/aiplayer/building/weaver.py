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

class AbstractWeaver(AbstractBuilding):
	@property
	def evaluator_class(self):
		return WeaverEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.WEAVER_CLASS] = cls

class WeaverEvaluator(BuildingEvaluator):
	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.WEAVER_CLASS, x, y, True, orientation)
		if not builder:
			return None

		distance_to_farm = None
		for building in area_builder.settlement.buildings_by_id.get(BUILDINGS.FARM_CLASS, []):
			distance = builder.position.distance(building.position)
			if distance <= Entities.buildings[BUILDINGS.WEAVER_CLASS].radius:
				wool_producer = False
				for provider in building._get_providers():
					if isinstance(provider, Entities.buildings[BUILDINGS.PASTURE_CLASS]):
						wool_producer = True
						break
				if wool_producer:
					distance_to_farm = distance if distance_to_farm is None or distance < distance_to_farm else distance_to_farm

		distance_to_collector = cls._distance_to_nearest_collector(area_builder, builder)
		if distance_to_collector is None:
			return None # require weavers to have a collector building in range

		personality = area_builder.owner.personality_manager.get('WeaverEvaluator')
		distance_penalty = Entities.buildings[BUILDINGS.WEAVER_CLASS].radius * personality.distance_penalty
		alignment = cls._get_alignment(area_builder, builder.position.tuple_iter())
		distance = cls._weighted_distance(distance_to_collector, [(personality.farm_distance_importance, distance_to_farm)], distance_penalty)
		value = float(Entities.buildings[BUILDINGS.WEAVER_CLASS].radius) / distance + alignment * personality.alignment_importance
		return WeaverEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.WEAVER

AbstractWeaver.register_buildings()

decorators.bind_all(AbstractWeaver)
decorators.bind_all(WeaverEvaluator)
