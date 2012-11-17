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

from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.world.buildability.connectedareacache import ConnectedAreaCache

class PotentialRoadConnectivityCache(object):
	def __init__(self, area_builder):
		self._area_builder = area_builder
		self._land_manager = area_builder.land_manager
		self._settlement_ground_map = area_builder.settlement.ground_map
		self._cache = ConnectedAreaCache()
		self.area_numbers = self._cache.area_numbers

	def modify_area(self, coords_list):
		add_list = []
		remove_list = []

		for coords in coords_list:
			if coords not in self._settlement_ground_map:
				if coords in self.area_numbers:
					remove_list.append(coords)
			elif coords in self._land_manager.coastline:
				if coords in self.area_numbers:
					remove_list.append(coords)
			elif coords in self._land_manager.roads:
				if coords not in self.area_numbers:
					add_list.append(coords)
			elif coords in self._area_builder.plan:
				if self._area_builder.plan[coords][0] == BUILDING_PURPOSE.NONE:
					if coords not in self.area_numbers:
						add_list.append(coords)
				else:
					assert self._area_builder.plan[coords][0] != BUILDING_PURPOSE.ROAD
					if coords in self.area_numbers:
						remove_list.append(coords)
			else:
				if coords in self.area_numbers:
					remove_list.append(coords)

		if add_list:
			self._cache.add_area(add_list)
		if remove_list:
			self._cache.remove_area(remove_list)

	def is_connection_possible(self, coords_set1, coords_set2):
		areas1 = set()
		for coords in coords_set1:
			if coords in self.area_numbers:
				areas1.add(self.area_numbers[coords])
		for coords in coords_set2:
			if coords in self.area_numbers:
				if self.area_numbers[coords] in areas1:
					return True
		return False
