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

from horizons.world.buildability.partialbinarycache import PartialBinaryBuildabilityCache


class SimpleCollectorAreaCache:
	"""
	A specialized PartialBinaryBuildabilityCache for keeping track of collector coverage.

	The AI uses instances of this class to figure out where it can place buildings such
	that at least some part of the building would be covered by a general collector. It
	is a simple version in that it doesn't check whether a road to the corresponding
	collector would be possible.
	"""

	def __init__(self, terrain_cache):
		self.terrain_cache = terrain_cache
		self._area_cache = PartialBinaryBuildabilityCache(terrain_cache)
		self.cache = self._area_cache.cache # {(width, height): set((x, y), ...), ...}
		self._buildings = set()
		self._area_coverage = {}

	def add_building(self, building):
		"""Take the the coverage area of the given building into account."""
		self._buildings.add(building)

		new_coords_list = []
		for coords in building.position.get_radius_coordinates(building.radius, True):
			if coords not in self.terrain_cache.land_or_coast:
				continue

			if coords not in self._area_coverage:
				self._area_coverage[coords] = 1
				new_coords_list.append(coords)
			else:
				self._area_coverage[coords] += 1
		for coords in new_coords_list:
			assert coords in self.terrain_cache.land_or_coast
		self._area_cache.add_area(new_coords_list)

	def remove_building(self, building):
		"""Stop taking the coverage area of the given building into account."""
		self._buildings.remove(building)

		removed_coords_list = []
		for coords in building.position.get_radius_coordinates(building.radius, True):
			if coords not in self.terrain_cache.land_or_coast:
				continue

			if self._area_coverage[coords] == 1:
				removed_coords_list.append(coords)
				del self._area_coverage[coords]
			else:
				self._area_coverage[coords] -= 1
		self._area_cache.remove_area(removed_coords_list)
