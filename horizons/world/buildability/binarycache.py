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

from horizons.world.buildability.terraincache import TerrainBuildabilityCache

class LazyBinaryBuildabilityCacheElement(object):
	def __init__(self, buildability_cache, width):
		super(LazyBinaryBuildabilityCacheElement, self).__init__()
		self._buildability_cache = buildability_cache
		self._width = width
		self._cache = None

	def _init_size_cache(self):
		if self._cache is not None:
			return

		r3x3 = self._buildability_cache.cache[(3, 3)]
		offset = self._width - 3

		usable = set()
		for coords in r3x3:
			x, y = coords
			if (x + offset, y) in r3x3 and (x, y + offset) in r3x3 and (x + offset, y + offset) in r3x3:
				usable.add(coords)

		self._cache = usable
		size = (self._width, self._width)
		self._buildability_cache.cache[size] = usable

	def __getattr__(self, name):
		# required to make set methods such as set.intersect work
		self._init_size_cache()
		return getattr(self._cache, name)

	def __contains__(self, key):
		# required to make the syntax "coords in cache" work efficiently
		self._init_size_cache()
		return key in self._cache

	def __iter__(self):
		# required to make iteration work
		self._init_size_cache()
		return iter(self._cache)

class BinaryBuildabilityCache(object):
	def __init__(self, terrain_cache):
		super(BinaryBuildabilityCache, self).__init__()
		self.terrain_cache = terrain_cache
		self.coords_set = set()
		self._row2 = set()

		self.cache = {}
		self.cache[(1, 1)] = self.coords_set
		for size in TerrainBuildabilityCache.sizes:
			if size != (1, 1):
				self.cache[size] = set()
				if size[0] != size[1]:
					self.cache[(size[1], size[0])] = set()
	
	def _reset_lazy_sets(self):
		self.cache[(4, 4)] = LazyBinaryBuildabilityCacheElement(self, 4)
		self.cache[(6, 6)] = LazyBinaryBuildabilityCacheElement(self, 6)

	@classmethod
	def _extend_set(cls, cur_set, prev_set, prev_set_additions, dx, dy):
		base_set_additions = set()
		for coords in prev_set_additions:
			x, y = coords
			prev_coords = (x - dx, y - dy)
			if prev_coords in prev_set:
				cur_set.add(prev_coords)
				base_set_additions.add(prev_coords)
			next_coords = (x + dx, y + dy)
			if next_coords not in prev_set_additions and next_coords in prev_set:
				cur_set.add(coords)
				base_set_additions.add(coords)
		return base_set_additions

	def add_area(self, new_coords_list):
		for coords in new_coords_list:
			assert coords not in self.coords_set
			assert coords in self.terrain_cache.land_or_coast
			self.coords_set.add(coords)

		coords_set = self.coords_set
		new_coords_set = set(new_coords_list)

		new_row2 = self._extend_set(self._row2, coords_set, new_coords_set, 1, 0)
		new_r2x2 = self._extend_set(self.cache[(2, 2)], self._row2, new_row2, 0, 1)

		new_r2x3 = self._extend_set(self.cache[(2, 3)], self.cache[(2, 2)], new_r2x2, 0, 1)
		new_r2x4 = self._extend_set(self.cache[(2, 4)], self.cache[(2, 3)], new_r2x3, 0, 1)

		new_r3x2 = self._extend_set(self.cache[(3, 2)], self.cache[(2, 2)], new_r2x2, 1, 0)
		new_r4x2 = self._extend_set(self.cache[(4, 2)], self.cache[(3, 2)], new_r3x2, 1, 0)

		new_r3x3 = self._extend_set(self.cache[(3, 3)], self.cache[(3, 2)], new_r3x2, 0, 1)

		self._reset_lazy_sets()

	@classmethod
	def _reduce_set(cls, cur_set, prev_set_removals, dx, dy):
		base_set_removals = set()
		for coords in prev_set_removals:
			x, y = coords
			prev_coords = (x - dx, y - dy)
			if prev_coords in cur_set:
				cur_set.discard(prev_coords)
				base_set_removals.add(prev_coords)
			next_coords = (x + dx, y + dy)
			if next_coords not in prev_set_removals and coords in cur_set:
				cur_set.discard(coords)
				base_set_removals.add(coords)
		return base_set_removals

	def remove_area(self, removed_coords_list):
		for coords in removed_coords_list:
			assert coords in self.coords_set
			assert coords in self.terrain_cache.land_or_coast
			self.coords_set.discard(coords)

		removed_coords_set = set(removed_coords_list)
		coords_set = self.coords_set

		removed_row2 = self._reduce_set(self._row2, removed_coords_set, 1, 0)
		removed_r2x2 = self._reduce_set(self.cache[(2, 2)], removed_row2, 0, 1)

		removed_r2x3 = self._reduce_set(self.cache[(2, 3)], removed_r2x2, 0, 1)
		removed_r2x4 = self._reduce_set(self.cache[(2, 4)], removed_r2x3, 0, 1)

		removed_r3x2 = self._reduce_set(self.cache[(3, 2)], removed_r2x2, 1, 0)
		removed_r4x2 = self._reduce_set(self.cache[(4, 2)], removed_r3x2, 1, 0)

		removed_r3x3 = self._reduce_set(self.cache[(3, 3)], removed_r3x2, 0, 1)

		self._reset_lazy_sets()
