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

from horizons.world.buildability.terraincache import TerrainBuildabilityCache


class PartialBinaryBuildabilityCache:
	"""
	A cache that knows where rectangles can be placed such that they are entirely inside the area.

	This cache can be used to keep track of building buildability in case the
	buildability depends on the building being at least partly within a certain area.
	The binary part of the name refers to the fact that a node either is or isn't part of
	the area that the instance is about.

	A query of the form (x, y) in instance.cache[(width, height)] is a very cheap way of
	finding out whether a rectangle of size (width, height) can be placed on origin (x, y)
	such that at least some part of it is within the given area.

	All elements of instance.cache[(width, height)] can be iterated to get a complete list
	of all such coordinates.
	"""

	def __init__(self, terrain_cache):
		self.terrain_cache = terrain_cache
		self.coords_set = set() # set((x, y), ...)
		self._row2 = set()

		sizes = set(TerrainBuildabilityCache.sizes)
		# extra sizes for the intermediate computation
		sizes.add((3, 4))
		sizes.add((4, 5))
		sizes.add((5, 5))
		sizes.add((5, 6))

		self.cache = {} # {(width, height): set((x, y), ...), ...}
		self.cache[(1, 1)] = self.coords_set
		for size in sizes:
			if size != (1, 1):
				self.cache[size] = set()
				if size[0] != size[1]:
					self.cache[(size[1], size[0])] = set()

	@classmethod
	def _extend_set(cls, cur_set, prev_set_additions, dx, dy):
		base_set_additions = set()
		for coords in prev_set_additions:
			x, y = coords
			prev_coords = (x - dx, y - dy)
			if prev_coords not in cur_set:
				cur_set.add(prev_coords)
				base_set_additions.add(prev_coords)
			next_coords = (x + dx, y + dy)
			if next_coords not in prev_set_additions and coords not in cur_set:
				cur_set.add(coords)
				base_set_additions.add(coords)
		return base_set_additions

	def add_area(self, new_coords_list):
		"""Add a list of new coordinates to the area."""
		for coords in new_coords_list:
			assert coords not in self.coords_set
			assert coords in self.terrain_cache.land_or_coast
			self.coords_set.add(coords)

		added_coords_set = set(new_coords_list)
		new_row2 = self._extend_set(self._row2, added_coords_set, 1, 0)
		new_r2x2 = self._extend_set(self.cache[(2, 2)], new_row2, 0, 1)

		new_r2x3 = self._extend_set(self.cache[(2, 3)], new_r2x2, 0, 1)
		new_r2x4 = self._extend_set(self.cache[(2, 4)], new_r2x3, 0, 1)

		new_r3x2 = self._extend_set(self.cache[(3, 2)], new_r2x2, 1, 0)
		new_r4x2 = self._extend_set(self.cache[(4, 2)], new_r3x2, 1, 0)

		new_r3x3 = self._extend_set(self.cache[(3, 3)], new_r3x2, 0, 1)

		# the further sizes are created just to support 4x4 and 6x6 buildings
		new_r3x4 = self._extend_set(self.cache[(3, 4)], new_r3x3, 0, 1)
		new_r4x4 = self._extend_set(self.cache[(4, 4)], new_r3x4, 1, 0)
		new_r4x5 = self._extend_set(self.cache[(4, 5)], new_r4x4, 0, 1)
		new_r5x5 = self._extend_set(self.cache[(5, 5)], new_r4x5, 1, 0)
		new_r5x6 = self._extend_set(self.cache[(5, 6)], new_r5x5, 0, 1)
		self._extend_set(self.cache[(6, 6)], new_r5x6, 1, 0)

	@classmethod
	def _reduce_set(cls, cur_set, prev_set, prev_set_removals, dx, dy):
		base_set_removals = set()
		for coords in prev_set_removals:
			x, y = coords
			prev_coords = (x - dx, y - dy)
			if prev_coords not in prev_set:
				cur_set.discard(prev_coords)
				base_set_removals.add(prev_coords)
			next_coords = (x + dx, y + dy)
			if next_coords not in prev_set_removals and next_coords not in prev_set:
				cur_set.discard(coords)
				base_set_removals.add(coords)
		return base_set_removals

	def remove_area(self, removed_coords_list):
		"""Remove a list of existing coordinates from the area."""
		for coords in removed_coords_list:
			assert coords in self.coords_set
			assert coords in self.terrain_cache.land_or_coast
			self.coords_set.discard(coords)
		removed_coords_set = set(removed_coords_list)

		removed_row2 = self._reduce_set(self._row2, self.coords_set, removed_coords_set, 1, 0)
		removed_r2x2 = self._reduce_set(self.cache[(2, 2)], self._row2, removed_row2, 0, 1)

		removed_r2x3 = self._reduce_set(self.cache[(2, 3)], self.cache[(2, 2)], removed_r2x2, 0, 1)
		removed_r2x4 = self._reduce_set(self.cache[(2, 4)], self.cache[(2, 3)], removed_r2x3, 0, 1)

		removed_r3x2 = self._reduce_set(self.cache[(3, 2)], self.cache[(2, 2)], removed_r2x2, 1, 0)
		removed_r4x2 = self._reduce_set(self.cache[(4, 2)], self.cache[(3, 2)], removed_r3x2, 1, 0)

		removed_r3x3 = self._reduce_set(self.cache[(3, 3)], self.cache[(3, 2)], removed_r3x2, 0, 1)
		removed_r3x4 = self._reduce_set(self.cache[(3, 4)], self.cache[(3, 3)], removed_r3x3, 0, 1)
		removed_r4x4 = self._reduce_set(self.cache[(4, 4)], self.cache[(3, 4)], removed_r3x4, 1, 0)
		removed_r4x5 = self._reduce_set(self.cache[(4, 5)], self.cache[(4, 4)], removed_r4x4, 0, 1)
		removed_r5x5 = self._reduce_set(self.cache[(5, 5)], self.cache[(4, 5)], removed_r4x5, 1, 0)
		removed_r5x6 = self._reduce_set(self.cache[(5, 6)], self.cache[(5, 5)], removed_r5x5, 0, 1)
		self._reduce_set(self.cache[(6, 6)], self.cache[(5, 6)], removed_r5x6, 1, 0)
