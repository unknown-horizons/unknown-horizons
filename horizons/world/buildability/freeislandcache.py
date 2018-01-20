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

from horizons.world.buildability.binarycache import BinaryBuildabilityCache


class FreeIslandBuildabilityCache:
	"""
	An instance of this class is used to keep track of the unclaimed area on an island.

	Instances of this class can answer the same queries as BinaryBuildabilityCache.
	It is specialized for keeping track of the unclaimed land on an island. That way it
	is possible to use it in conjunction with the TerrainCache to find all available
	warehouse positions on an island.

	Note that the cache is initialized with all unclaimed tiles on the island and after
	that it can only reduce in size because it is currently impossible for land to change
	ownership after it has been claimed by the first player.
	"""

	def __init__(self, island):
		self._binary_cache = BinaryBuildabilityCache(island.terrain_cache)
		self.cache = self._binary_cache.cache # {(width, height): set((x, y), ...), ...}
		self.island = island
		self._init()

	def _init(self):
		land_or_coast = self._binary_cache.terrain_cache.land_or_coast
		coords_list = []
		for (coords, tile) in self.island.ground_map.items():
			if coords not in land_or_coast:
				continue
			if tile.settlement is not None:
				continue
			if tile.object is not None and not tile.object.buildable_upon:
				continue
			coords_list.append(coords)
		self._binary_cache.add_area(coords_list)

	def remove_area(self, coords_list):
		"""Remove a list of existing coordinates from the area."""
		clean_list = []
		for coords in coords_list:
			if coords in self._binary_cache.coords_set:
				clean_list.append(coords)
		self._binary_cache.remove_area(clean_list)

	def add_area(self, coords_list):
		"""Add a list of coordinates to the area."""
		clean_list = []
		for coords in coords_list:
			if coords not in self._binary_cache.coords_set:
				clean_list.append(coords)
		self._binary_cache.add_area(clean_list)
