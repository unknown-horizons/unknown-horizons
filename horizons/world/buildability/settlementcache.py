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


class SettlementBuildabilityCache(BinaryBuildabilityCache):
	"""A specialized BinaryBuildabilityCache for settlements."""

	def __init__(self, terrain_cache, settlement_ground_map):
		super().__init__(terrain_cache)
		self.settlement_ground_map = settlement_ground_map

	def add_area(self, coords_list):
		"""Add a list of new coordinates to the area."""
		land_or_coast = self.terrain_cache.land_or_coast
		add_list = []
		for coords in coords_list:
			if coords in land_or_coast:
				add_list.append(coords)
		if add_list:
			super().add_area(add_list)

	def modify_area(self, coords_list):
		"""
		Refresh the usability of the coordinates in the given list.

		This function is called with a list of coordinates on which the possibility of
		building a building may have changed to update the underlying BinaryBuildabilityCache.
		"""

		land_or_coast = self.terrain_cache.land_or_coast

		add_list = []
		remove_list = []
		for coords in coords_list:
			assert isinstance(coords, tuple)
			if coords not in land_or_coast or coords not in self.settlement_ground_map:
				continue

			object = self.settlement_ground_map[coords].object
			if object is None or object.buildable_upon:
				if coords not in self.coords_set:
					add_list.append(coords)
			elif coords in self.coords_set:
				remove_list.append(coords)

		if remove_list:
			self.remove_area(remove_list)
		if add_list:
			super().add_area(add_list)
