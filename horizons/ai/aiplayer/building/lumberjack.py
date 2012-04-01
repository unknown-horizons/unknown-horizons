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

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.entities import Entities
from horizons.constants import BUILDINGS
from horizons.util.python import decorators
from horizons.util import Point, Rect

class AbstractLumberjack(AbstractBuilding):
	@property
	def evaluator_class(self):
		return LumberjackEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.LUMBERJACK] = cls

class LumberjackEvaluator(BuildingEvaluator):
	__template_outline = None

	@classmethod
	def __init_outline(cls):
		"""Save a template outline that surrounds a lumberjack."""
		position = Rect.init_from_topleft_and_size_tuples((0, 0), Entities.buildings[BUILDINGS.LUMBERJACK].size)
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		coords_list = set(position.get_radius_coordinates(Entities.buildings[BUILDINGS.LUMBERJACK].radius, True))

		result = set()
		for x, y in coords_list:
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords not in coords_list:
					result.add(coords)
		cls.__template_outline = list(result)

	@classmethod
	def _get_outline(cls, x, y):
		if cls.__template_outline is None:
			cls.__init_outline()

		result = []
		for dx, dy in cls.__template_outline:
			result.append((x + dx, y + dy))
		return result

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.LUMBERJACK, x, y, True, orientation)
		if not builder:
			return None

		area_value = 0
		personality = area_builder.owner.personality_manager.get('LumberjackEvaluator')
		for coords in builder.position.get_radius_coordinates(Entities.buildings[BUILDINGS.LUMBERJACK].radius):
			if coords in area_builder.plan:
				purpose = area_builder.plan[coords][0]
				if purpose == BUILDING_PURPOSE.NONE:
					area_value += personality.new_tree
				elif purpose == BUILDING_PURPOSE.TREE:
					area_value += personality.shared_tree
		area_value = min(area_value, personality.max_forest_value) # the lumberjack doesn't actually need all the trees
		if area_value < personality.min_forest_value:
			return None # the area is too bad for a lumberjack

		personality = area_builder.owner.personality_manager.get('LumberjackEvaluator')
		alignment = cls._get_alignment_from_outline(area_builder, cls._get_outline(x, y))
		value = area_value + alignment * personality.alignment_importance
		return LumberjackEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.LUMBERJACK

	def execute(self):
		(result, building) = super(LumberjackEvaluator, self).execute()
		if result != BUILD_RESULT.OK:
			return (result, None)

		for coords in building.position.get_radius_coordinates(Entities.buildings[BUILDINGS.LUMBERJACK].radius):
			if coords in self.area_builder.plan and self.area_builder.plan[coords][0] == BUILDING_PURPOSE.NONE:
				self.area_builder.register_change(coords[0], coords[1], BUILDING_PURPOSE.TREE, None)
				# TODO: don't ignore the return value
				Builder.create(BUILDINGS.TREE, self.area_builder.land_manager, Point(coords[0], coords[1])).execute()
		return (BUILD_RESULT.OK, building)

AbstractLumberjack.register_buildings()

decorators.bind_all(AbstractLumberjack)
decorators.bind_all(LumberjackEvaluator)
