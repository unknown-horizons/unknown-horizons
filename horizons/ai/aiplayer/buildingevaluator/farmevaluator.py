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

import copy

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.util.python import decorators
from horizons.util import Point
from horizons.constants import BUILDINGS

class FarmEvaluator(BuildingEvaluator):
	moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	field_offsets = None

	def __init__(self, production_builder, builder, farm_plan, fields, existing_roads, alignment):
		super(FarmEvaluator, self).__init__(production_builder, builder)
		self.farm_plan = farm_plan
		self.fields = fields
		self.existing_roads = existing_roads
		self.alignment = alignment
		self.value = fields + existing_roads * 0.005 + alignment * 0.001

	@classmethod
	def _make_field_offsets(cls):
		# right next to the farm
		first_class = [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]
		# offset by a road right next to the farm
		second_class = [(-4, -3), (-4, 0), (-4, 3), (-3, -4), (-3, 4), (0, -4), (0, 4), (3, -4), (3, 4), (4, -3), (4, 0), (4, 3)]
		# offset by crossing roads
		third_class = [(-4, -4), (-4, 4), (4, -4), (4, 4)]
		first_class.extend(second_class)
		first_class.extend(third_class)
		return first_class

	@classmethod
	def create(cls, production_builder, x, y, road_dx, road_dy, min_fields):
		builder = production_builder.make_builder(BUILDINGS.FARM_CLASS, x, y, True)
		if not builder:
			return None

		farm_plan = {}

		# place the farm area road
		existing_roads = 0
		for other_offset in xrange(-3, 6):
			coords = None
			if road_dx == 0:
				coords = (x + other_offset, y + road_dy)
			else:
				coords = (x + road_dx, y + other_offset)
			if coords not in production_builder.plan or (production_builder.plan[coords][0] != PRODUCTION_PURPOSE.NONE \
														and production_builder.plan[coords][0] != PRODUCTION_PURPOSE.ROAD):
				farm_plan = None
				break

			if production_builder.plan[coords][0] == PRODUCTION_PURPOSE.NONE:
				road = Builder.create(BUILDINGS.TRAIL_CLASS, production_builder.land_manager, Point(coords[0], coords[1]))
				if road:
					farm_plan[coords] = (PRODUCTION_PURPOSE.ROAD, road)
				else:
					farm_plan = None
					break
			else:
				existing_roads += 1
		if farm_plan is None:
			return None # impossible to build some part of the road

		# place the fields
		fields = 0
		for (dx, dy) in cls.field_offsets:
			if fields >= 8:
				break # unable to place more anyway
			coords = (x + dx, y + dy)
			field = production_builder.make_builder(BUILDINGS.POTATO_FIELD_CLASS, coords[0], coords[1], False)
			if not field:
				continue
			for coords2 in field.position.tuple_iter():
				if coords2 in farm_plan:
					field = None
					break
			if field is None:
				break # some part of the area is reserved for something else
			fields += 1
			for coords2 in field.position.tuple_iter():
				farm_plan[coords2] = (PRODUCTION_PURPOSE.RESERVED, None)
			farm_plan[coords] = (PRODUCTION_PURPOSE.FARM_FIELD, None)
		if fields < min_fields:
			return None # go for the most fields possible

		# add the farm itself to the plan
		for coords in builder.position.tuple_iter():
			farm_plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
		farm_plan[(x, y)] = (PRODUCTION_PURPOSE.FARM, builder)

		alignment = 0
		for x, y in farm_plan:
			for dx, dy in cls.moves:
				coords = (x + dx, y + dy)
				if coords in farm_plan:
					continue
				if coords not in production_builder.plan or production_builder.plan[coords][0] != PRODUCTION_PURPOSE.NONE:
					alignment += 1

		value = fields + existing_roads * 0.005 + alignment * 0.001
		return FarmEvaluator(production_builder, builder, farm_plan, fields, existing_roads, alignment)

	def execute(self):
		if not self.production_builder.have_resources(BUILDINGS.FISHERMAN_CLASS):
			return BUILD_RESULT.NEED_RESOURCES
		backup = copy.copy(self.production_builder.plan)
		for coords, plan_item in self.farm_plan.iteritems():
			self.production_builder.plan[coords] = plan_item
		if not self.production_builder._build_road_connection(self.builder):
			self.production_builder.plan = backup
			return BUILD_RESULT.IMPOSSIBLE
		building = self.builder.execute()
		if not building:
			return BUILD_RESULT.UNKNOWN_ERROR
		for coords, (purpose, builder) in self.farm_plan.iteritems():
			if purpose == PRODUCTION_PURPOSE.FARM_FIELD:
				self.production_builder.unused_fields.append(coords)
		self.production_builder.production_buildings.append(building)
		return BUILD_RESULT.OK

FarmEvaluator.field_offsets = FarmEvaluator._make_field_offsets()

decorators.bind_all(FarmEvaluator)
