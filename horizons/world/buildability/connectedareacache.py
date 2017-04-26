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

from collections import deque


class ConnectedAreaCache:
	"""
	Query whether (x1, y1) and (x2, y2) are connected.

	This class aims to let one cheaply query the id of the area where (x, y) are. Getting
	that information for (x1, y1) and (x2, y2) shows that it is possible to get from
	one to the other entirely within the area if and only if they have the same area id.

	The area id is an arbitrary integer that is returned for all coordinates in a
	connected area. It is only valid between updates of the cache (any addition/removal
	may change the area id). Thus the ids should never be used for anything other than
	(in)equality checks.
	"""

	__moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]

	def __init__(self):
		self.area_numbers = {} # {(x, y): area id, ...}
		self.areas = {} # {area id: set((x, y), ...), ...}
		self._next_area_id = 1

	def _label_area(self, seed_coords):
		area_id = self._next_area_id
		self._next_area_id += 1

		area_numbers = self.area_numbers
		area_numbers[seed_coords] = area_id
		new_area = {seed_coords}
		self.areas[area_id] = new_area

		moves = self.__moves
		queue = deque([seed_coords])
		while queue:
			(x, y) = queue.popleft()
			for (dx, dy) in moves:
				coords = (x + dx, y + dy)
				if coords not in area_numbers:
					continue
				if area_numbers[coords] == area_id:
					continue

				area_numbers[coords] = area_id
				new_area.add(coords)
				queue.append(coords)

	def _renumber_affected_areas(self, affected_areas):
		for area_id in affected_areas:
			for coords in self.areas[area_id]:
				if self.area_numbers[coords] == area_id:
					self._label_area(coords)
					assert self.area_numbers[coords] != area_id
			del self.areas[area_id]

	def add_area(self, coords_list):
		"""Add a list of new coordinates to the area."""
		moves = self.__moves
		affected_areas = set()
		for coords in coords_list:
			assert coords not in self.area_numbers
			nearby_areas = []
			for (dx, dy) in moves:
				neighbor_coords = (coords[0] + dx, coords[1] + dy)
				if neighbor_coords in self.area_numbers:
					area_id = self.area_numbers[neighbor_coords]
					if area_id not in nearby_areas:
						nearby_areas.append(area_id)

			if not nearby_areas:
				# create a new area
				area_id = self._next_area_id
				self._next_area_id += 1
				self.area_numbers[coords] = area_id
				self.areas[area_id] = {coords}
			else:
				# add to one of the nearby areas
				area_id = nearby_areas[0]
				self.area_numbers[coords] = area_id
				self.areas[area_id].add(coords)
				if len(nearby_areas) > 1:
					# more than one nearby area; merge them later on
					for nearby_area_id in nearby_areas:
						affected_areas.add(nearby_area_id)

		self._renumber_affected_areas(affected_areas)

	def remove_area(self, coords_list):
		"""Remove a list of existing coordinates from the area."""
		affected_areas = set()
		for coords in coords_list:
			area_id = self.area_numbers[coords]
			del self.area_numbers[coords]
			affected_areas.add(area_id)
			self.areas[area_id].discard(coords)
		self._renumber_affected_areas(affected_areas)
