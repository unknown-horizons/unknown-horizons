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

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE

from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.util.python import decorators
from horizons.util import Point

class LumberjackEvaluator(BuildingEvaluator):
	def __init__(self, area_builder, builder, area_value, alignment):
		super(LumberjackEvaluator, self).__init__(area_builder, builder)
		self.area_value = area_value
		self.alignment = alignment
		self.value = area_value + alignment * 0.5
	
	@classmethod
	def get_radius(cls):
		return Entities.buildings[BUILDINGS.LUMBERJACK_CLASS].radius

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.LUMBERJACK_CLASS, x, y, True, orientation)
		if not builder:
			return None

		area_value = 0
		for coords in builder.position.get_radius_coordinates(cls.get_radius()):
			if coords in area_builder.plan:
				purpose = area_builder.plan[coords][0]
				if purpose == BUILDING_PURPOSE.NONE:
					area_value += 3
				elif purpose == BUILDING_PURPOSE.TREE:
					area_value += 1
		area_value = min(area_value, 100) # the lumberjack doesn't actually need all the trees
		if area_value < 30:
			return None # the area is too bad for a lumberjack

		alignment = cls.get_alignment(area_builder, builder.position.get_radius_coordinates(cls.get_radius(), True))
		return LumberjackEvaluator(area_builder, builder, area_value, alignment)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.LUMBERJACK

	def execute(self):
		(result, building) = super(LumberjackEvaluator, self).execute()
		if result != BUILD_RESULT.OK:
			return (result, None)

		for coords in building.position.get_radius_coordinates(self.get_radius()):
			if coords in self.area_builder.plan and self.area_builder.plan[coords][0] == BUILDING_PURPOSE.NONE:
				self.area_builder.register_change(coords[0], coords[1], BUILDING_PURPOSE.TREE, None)
				# TODO: don't ignore the return value
				Builder.create(BUILDINGS.TREE_CLASS, self.area_builder.land_manager, Point(coords[0], coords[1])).execute()
		return (BUILD_RESULT.OK, building)

decorators.bind_all(LumberjackEvaluator)
