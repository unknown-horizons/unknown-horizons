# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.util.shapes.point import Point
from horizons.util.shapes.circle import Circle
from horizons.util.python.decorators import make_constants


class BuildingIndexer(object):
	"""
	Indexes a subset of the buildings on an island to improve nearby building 
	lookup performance.

	Used to answer queries of the form 'I am at (x, y), where is the closest / random
	building that provides resource X in my range'.
	"""

	def __init__(self, radius, coords_list, random):
		"""
		Create a BuildingIndexer
		@param radius: int, maximum required radius of the buildings
		@param coords_list: list of tuples, the coordinates of the island
		@param random: the rng of the session
		"""
		self._offsets = Circle(Point(0, 0), radius).get_coordinates()
		self._map = {}
		for coords in coords_list:
			self._map[coords] = BuildingIndex(coords, random)
		self._add_set = set()
		self._remove_set = set()
		self._changed = False

	@make_constants()
	def add(self, building):
		self._remove_set.discard(building)
		self._add_set.add(building)
		self._changed = True

	@make_constants()
	def remove(self, building):
		self._add_set.discard(building)
		self._remove_set.add(building)
		self._changed = True

	@make_constants()
	def _get_tuples_in_range(self, building):
		# TODO: this should be improved to work better on buildings with more than one tile
		for building_coords in building.position.tuple_iter():
			for x_offset, y_offset in self._offsets:
				coords = (building_coords[0] + x_offset, building_coords[1] + y_offset)
				if coords in self._map:
					yield coords

	def _update(self):
		for building in self._remove_set:
			for coords in self._get_tuples_in_range(building):
				self._map[coords].remove(building)
		for building in self._add_set:
			for coords in self._get_tuples_in_range(building):
				self._map[coords].add(building)

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
			for building in self._map[coords].get_buildings_in_range():
				yield building

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



class BuildingIndex(object):
	"""Indexes a subset of the buildings near a tile to improve nearby building 
	lookup performance."""

	def __init__(self, coords, random):
		self._coords = coords
		self._random = random
		self._add_set = set()
		self._remove_set = set()
		self._list = []
		self._changed = False

	@make_constants()
	def add(self, building):
		self._remove_set.discard(building)
		self._add_set.add(building)
		self._changed = True

	@make_constants()
	def remove(self, building):
		self._add_set.discard(building)
		self._remove_set.add(building)
		self._changed = True

	def _update(self):
		new_list = []
		for element in self._list:
			if element.building not in self._remove_set:
				new_list.append(element)
		for building in self._add_set:
			new_list.append(BuildingIndexElement(building.position.distance_to_tuple(self._coords), building))
		self._list = new_list
		self._list.sort()

		self._add_set.clear()
		self._remove_set.clear()
		self._changed = False

	def get_buildings_in_range(self):
		if self._changed:
			self._update()
		for element in self._list:
			yield element.building

	def get_random_building_in_range(self):
		if self._changed:
			self._update()
		if self._list:
			return self._random.choice(self._list).building
		return None



class BuildingIndexElement(object):
	"""This is a single element in a BuildingIndex object."""

	def __init__(self, distance, building):
		self.distance = distance
		self.building = building

	@make_constants()
	def __cmp__(self, other):
		if abs(self.distance - other.distance) > -1e-7:
			return -1 if self.distance < other.distance else 1
		self_pos = self.building.position
		other_pos = other.position
		if self_pos.top != other_pos.top:
			return self_pos.top - other_pos.top
		elif self_pos.bottom != other_pos.bottom:
			return self_pos.bottom - other_pos.bottom
		elif self_pos.left != other_pos.left:
			return self_pos.left - other_pos.left
		return self_pos.right - other_pos.right
