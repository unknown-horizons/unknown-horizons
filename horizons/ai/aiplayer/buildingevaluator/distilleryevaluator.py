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

class DistilleryEvaluator(BuildingEvaluator):
	def __init__(self, area_builder, builder, distance_to_farm, distance_to_collector, alignment):
		super(DistilleryEvaluator, self).__init__(area_builder, builder)
		self.distance_to_farm = distance_to_farm
		self.distance_to_collector = distance_to_collector
		self.alignment = alignment

		distance = distance_to_collector
		if distance_to_farm is not None:
			distance *= 0.7 + distance_to_farm / float(Entities.buildings[BUILDINGS.DISTILLERY_CLASS].radius) * 0.3
		self.value = 10.0 / distance + alignment * 0.02

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.DISTILLERY_CLASS, x, y, True, orientation)
		if not builder:
			return None

		distance_to_farm = None
		for building in area_builder.settlement.get_buildings_by_id(BUILDINGS.FARM_CLASS):
			distance = builder.position.distance(building.position)
			if distance <= Entities.buildings[BUILDINGS.DISTILLERY_CLASS].radius:
				sugarcane_producer = False
				for provider in building._get_providers():
					if isinstance(provider, Entities.buildings[BUILDINGS.SUGARCANE_FIELD_CLASS]):
						sugarcane_producer = True
						break
				if sugarcane_producer:
					distance_to_farm = distance if distance_to_farm is None or distance < distance_to_farm else distance_to_farm

		distance_to_collector = cls.distance_to_nearest_collector(area_builder, builder)
		if distance_to_collector is None:
			return None # require distilleries to have a collector building in range

		alignment = cls.get_alignment(area_builder, builder.position.tuple_iter())
		return DistilleryEvaluator(area_builder, builder, distance_to_farm, distance_to_collector, alignment)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.DISTILLERY

decorators.bind_all(DistilleryEvaluator)
