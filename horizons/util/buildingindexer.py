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

from horizons.util.python import decorators


class BuildingIndexer(object):
	"""
	Indexes a subset of the buildings on an island to improve nearby building
	lookup performance.

	Used to answer queries of the form 'I am at (x, y), where is the closest / random
	building that provides resource X in my range'.
	"""

	def __init__(self, radius, coords_list, random=None, buildings=None):
		"""
		Create a BuildingIndexer
		@param radius: int, maximum required radius of the buildings
		@param coords_list: list of tuples, the coordinates of the island
		@param random: the rng of the session
		@param buildings: initial list of buildings. Will only be read.
		"""
		self.radius = radius
		self._map = {}
		for coords in coords_list:
			self._map[coords] = BuildingIndex(coords, random)
		self._add_set = set()
		self._remove_set = set()
		self._changed = False

		if buildings:
			self._update(add_buildings=buildings, initial=True)

	def add(self, building):
		self._remove_set.discard(building)
		self._add_set.add(building)
		self._changed = True

	def remove(self, building):
		self._add_set.discard(building)
		self._remove_set.add(building)
		self._changed = True

	def _update(self, add_buildings=None, initial=False):
		"""
		@param add_buildings: Don't use unless you know why.
		@param initial: can be set on first call as optimisation
		"""
		for building in self._remove_set:
			for coords in building.position.get_radius_coordinates(self.radius, include_self=True):
				try:
					index = self._map[coords]
				except KeyError:
					continue # should be faster than contains check, since usually true
				index._remove_set.add(building)
				index._add_set.discard(building)
				index._changed = True

		if not add_buildings:
			add_buildings = self._add_set
		for building in add_buildings:
			for coords in building.position.get_radius_coordinates(self.radius, include_self=True):
				try:
					index = self._map[coords]
				except KeyError:
					continue # should be faster than contains check, since usually true
				if not initial:
					index._remove_set.discard(building)
				index._add_set.add(building)
				index._changed = True

		self._changed = False
		self._add_set.clear()
		self._remove_set.clear()

	def get_buildings_in_range(self, coords):
		"""
		Returns all buildings in range in the form of a Building generator
		@param coords: tuple, the point around which to get the buildings
		"""
		if coords in self._map:
			if self._changed:
				self._update()
			return self._map[coords].get_buildings_in_range()
		return []

	def get_random_building_in_range(self, coords):
		"""
		Returns a random building in range or None if one doesn't exist
		Don't use this for user interactions unless you want to break multiplayer
		@param coords: tuple, the point around which to get the building
		"""
		if coords in self._map:
			if self._changed:
				self._update()
			return self._map[coords].get_random_building_in_range()
		return None

	def get_num_buildings_in_range(self, coords):
		"""
		Returns the number of buildings in range of the position
		@param coords: tuple, the centre point
		"""
		if coords in self._map:
			if self._changed:
				self._update()
			return self._map[coords].get_num_buildings_in_range()



class BuildingIndex(object):
	"""
	Indexes buildings around a tile to improve nearby building lookup speed.
	The code isn't particularly pretty for performance reasons.
	"""

	def __init__(self, coords, random):
		self._coords = coords
		self._random = random
		self._add_set = set()
		self._remove_set = set()
		self._list = []
		self._changed = False

	def _update(self):
		new_list = []
		for element in self._list:
			if element[5] not in self._remove_set:
				new_list.append(element)

		x = self._coords[0]
		y = self._coords[1]
		for building in self._add_set:
			pos = building.position
			left = pos.left
			right = pos.right
			top = pos.top
			bottom = pos.bottom

			x_diff = left - x
			if x_diff < x - right:
				x_diff = x - right
			if x_diff < 0:
				x_diff = 0

			y_diff = top - y
			if y_diff < y - bottom:
				y_diff = y - bottom
			if y_diff < 0:
				y_diff = 0

			new_list.append((x_diff * x_diff + y_diff * y_diff, top, bottom, left, right, building))

		self._list = new_list
		self._list.sort()

		self._add_set.clear()
		self._remove_set.clear()
		self._changed = False

	def get_buildings_in_range(self):
		if self._changed:
			self._update()
		for element in self._list:
			yield element[5]

	def get_random_building_in_range(self):
		if self._changed:
			self._update()
		if self._list:
			return self._random.choice(self._list)[5]
		return None

	def get_num_buildings_in_range(self):
		if self._changed:
			self._update()
		return len(self._list)


# apply make_constant to classes
decorators.bind_all(BuildingIndexer)
decorators.bind_all(BuildingIndex)
