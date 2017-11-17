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

from typing import List, Set, Tuple

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.util.shapes import Rect


class AbstractLumberjack(AbstractBuilding):
	@property
	def evaluator_class(self):
		return LumberjackEvaluator

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.LUMBERJACK] = cls


class LumberjackEvaluator(BuildingEvaluator):
	__template_outline = None # type: List[Set[Tuple[int, int]]]
	__radius_offsets = None # type: List[Tuple[int, int]]

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
		cls.__template_outline = sorted(list(result))
		cls.__radius_offsets = sorted(position.get_radius_coordinates(Entities.buildings[BUILDINGS.LUMBERJACK].radius))

	@classmethod
	def _get_outline(cls, x, y):
		result = []
		for dx, dy in cls.__template_outline:
			result.append((x + dx, y + dy))
		return result

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		# TODO: create a late initialization phase for this kind of stuff
		if cls.__radius_offsets is None:
			cls.__init_outline()

		area_value = 0
		coastline = area_builder.land_manager.coastline
		personality = area_builder.owner.personality_manager.get('LumberjackEvaluator')
		for dx, dy in cls.__radius_offsets:
			coords = (x + dx, y + dy)
			if coords in area_builder.plan and coords not in coastline:
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
		builder = BasicBuilder.create(BUILDINGS.LUMBERJACK, (x, y), orientation)
		return LumberjackEvaluator(area_builder, builder, value)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.LUMBERJACK

	def execute(self):
		# TODO Add a check that figures out if all trees that should be planted are in range of the settlement.
		# If not, return range missing result
		(result, building) = super().execute()
		if result != BUILD_RESULT.OK:
			return (result, None)

		production_builder = self.area_builder
		coastline = production_builder.land_manager.coastline
		island_ground_map = production_builder.island.ground_map
		forest_coords_list = []
		for coords in building.position.get_radius_coordinates(Entities.buildings[BUILDINGS.LUMBERJACK].radius):
			if coords in production_builder.plan and production_builder.plan[coords][0] == BUILDING_PURPOSE.NONE and coords not in coastline:
				if island_ground_map[coords].object is not None and island_ground_map[coords].object.id == BUILDINGS.TREE:
					forest_coords_list.append(coords)
				elif island_ground_map[coords].settlement is not None and island_ground_map[coords].settlement.owner is self.area_builder.owner:
					builder = BasicBuilder(BUILDINGS.TREE, coords, 0)
					if not builder.have_resources(production_builder.land_manager):
						break
					if builder:
						assert builder.execute(production_builder.land_manager)
						forest_coords_list.append(coords)

		production_builder.register_change_list(forest_coords_list, BUILDING_PURPOSE.TREE, None)

		return (BUILD_RESULT.OK, building)


AbstractLumberjack.register_buildings()
