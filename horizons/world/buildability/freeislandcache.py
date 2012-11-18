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

from horizons.world.buildability.binarycache import BinaryBuildabilityCache

class FreeIslandBuildabilityCache(object):
	def __init__(self, island):
		self._binary_cache = BinaryBuildabilityCache(island.terrain_cache)
		self.cache = self._binary_cache.cache
		self.island = island
		self._init()

	def _init(self):
		land_or_coast = self._binary_cache.terrain_cache.land_or_coast
		coords_list = []
		for (coords, tile) in self.island.ground_map.iteritems():
			if coords not in land_or_coast:
				continue
			if tile.settlement is not None:
				continue
			if tile.object is not None and not tile.object.buildable_upon:
				continue
			coords_list.append(coords)
		self._binary_cache.add_area(coords_list)

	def remove_area(self, coords_list):
		clean_list = []
		for coords in coords_list:
			if coords in self._binary_cache.coords_set:
				clean_list.append(coords)
		self._binary_cache.remove_area(clean_list)
