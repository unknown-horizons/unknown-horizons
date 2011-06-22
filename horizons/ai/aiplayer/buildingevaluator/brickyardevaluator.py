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

class BrickyardEvaluator(BuildingEvaluator):
	radius = 10 # TODO: load this properly

	def __init__(self, production_builder, builder, distance_to_clay_pit, distance_to_collector, alignment):
		super(BrickyardEvaluator, self).__init__(production_builder, builder)
		self.distance_to_clay_pit = distance_to_clay_pit
		self.distance_to_collector = distance_to_collector
		self.alignment = alignment
		self.production_level = None

		distance = distance_to_clay_pit
		if distance_to_collector is not None:
			distance *= 0.9 + distance_to_collector / float(self.radius) * 0.1
		self.value = 10.0 / distance + alignment * 0.02

	def get_expected_production_level(self, resource_id):
		assert resource_id == RES.BRICKS_ID
		return 0 # TODO: implement this

	@classmethod
	def create(cls, production_builder, x, y, orientation):
		builder = production_builder.make_builder(BUILDINGS.BRICKYARD_CLASS, x, y, True, orientation)
		if not builder:
			return None

		distance_to_clay_pit = None
		for building in production_builder.settlement.get_buildings_by_id(BUILDINGS.CLAY_PIT_CLASS):
			distance = builder.position.distance(building.position)
			if distance <= cls.radius:
				distance_to_clay_pit = distance if distance_to_clay_pit is None or distance < distance_to_clay_pit else distance_to_clay_pit
		if distance_to_clay_pit is None:
			return None

		distance_to_collector = None
		for building in production_builder.collector_buildings:
			distance = builder.position.distance(building.position)
			if distance <= cls.radius:
				distance_to_collector = distance if distance_to_collector is None or distance < distance_to_collector else distance_to_collector

		alignment = 0
		for coords in production_builder._get_neighbour_tiles(builder.position):
			if coords in production_builder.plan:
				purpose = production_builder.plan[coords]
				if purpose == BUILDING_PURPOSE.NONE:
					continue
				elif purpose == BUILDING_PURPOSE.ROAD:
					alignment += 3
				else:
					alignment += 1
			elif coords in production_builder.settlement.ground_map:
				object = production_builder.settlement.ground_map[coords].object
				if object is not None and object.id == BUILDINGS.TRAIL_CLASS:
					alignment += 3
				else:
					alignment += 1
			else:
				alignment += 1

		return BrickyardEvaluator(production_builder, builder, distance_to_clay_pit, distance_to_collector, alignment)

	def execute(self):
		if not self.production_builder.have_resources(self.builder.building_id):
			return BUILD_RESULT.NEED_RESOURCES
		if not self.production_builder._build_road_connection(self.builder):
			return BUILD_RESULT.IMPOSSIBLE
		building = self.builder.execute()
		if not building:
			return BUILD_RESULT.UNKNOWN_ERROR
		for coords in self.builder.position.tuple_iter():
			self.production_builder.plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
		self.production_builder.plan[sorted(self.builder.position.tuple_iter())[0]] = (BUILDING_PURPOSE.BRICKYARD, self.builder)
		self.production_builder.production_buildings.append(building)
		return BUILD_RESULT.OK

decorators.bind_all(BrickyardEvaluator)
