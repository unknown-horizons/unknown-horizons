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


from point import Point

from horizons.util.python.decorators import bind_all
from horizons.util.shapes.point import ConstPoint

class Annulus(object):
	"""Class for the shape of an annulus
	You can access center and radius of the annulus as public members."""
	def __init__(self, center, min_radius, max_radius):
		"""
		@param center: Point
		@param min_radius: int
		@param max_radius: int
		"""
		assert isinstance(center, Point)
		self.center = center
		self.min_radius = min_radius
		self.max_radius = max_radius

	def get_coordinates(self):
		"""Returns all coordinates, that are in the annulus"""
		coords = []
		for i in self.tuple_iter():
			coords.append(i)
		return coords

	def contains(self, point):
		assert isinstance(point, Point)
		if point.distance_to_point(self.center) <= self.max_radius and\
		   point.distance_to_point(self.center) >= self.min_radius:
			return True
		else:
			return False

	def center(self):
		return self.center

	def __str__(self):
		return "Annulus(center=%s,min_radius=%s,max_radius=%s)" % (self.center, self.min_radius, self.max_radius)

	def __eq__(self, other):
		try:
			if self.center == other.center and \
				 self.min_radius == other.min_radius and \
				 self.max_radius == other.max_radius:
				return True
			else:
				return False
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def distance(self, other):
		# trap method: init data, then replace this method with real method
		from rect import Rect, ConstRect
		from circle import Circle
		self._distance_functions_map = {
			Point: self.distance_to_point,
			ConstPoint: self.distance_to_point,
			tuple: self.distance_to_tuple,
			Circle: self.distance_to_circle,
			Rect: self.distance_to_rect,
			ConstRect: self.distance_to_rect,
			Annulus: self.distance_to_annulus
		}
		self.distance = self.__real_distance
		return self.distance(other)

	def __real_distance(self, other):
		try:
			return self._distance_functions_map[other.__class__](other)
		except KeyError:
			return other.distance(self)

	def distance_to_point(self, other):
		return other.distance_to_annulus(self)

	def distance_to_tuple(self, other):
		dist = ((self.center.x - other[0]) ** 2 + (self.center.y - other[1]) ** 2) ** 0.5
		if dist < self.min_radius:
			return self.min_radius - dist
		if dist > self.max_radius:
			return dist - self.max_radius
		return 0

	#TODO check and fix these methods
	def distance_to_rect(self, other):
		return other.distance_to_annulus(self)

	def distance_to_circle(self, other):
		dist = self.distance(other.center) - self.max_radius - other.radius
		return dist if dist >= 0 else 0

	def distance_to_annulus(self, other):
		dist = self.distance(other.center) - self.max_radius - other.max_radius
		return dist if dist >= 0 else 0

	def __iter__(self):
		for x in xrange(self.center.x-self.max_radius, self.center.x+self.max_radius+1):
			for y in xrange(self.center.y-self.max_radius, self.center.y+self.max_radius+1):
				if self.center.distance_to_tuple((x, y)) <= self.max_radius and \
					self.center.distance_to_tuple((x, y)) >= self.min_radius:
					yield Point(x, y)

	def tuple_iter(self):
		for x in xrange(self.center.x-self.max_radius, self.center.x+self.max_radius+1):
			for y in xrange(self.center.y-self.max_radius, self.center.y+self.max_radius+1):
				if self.center.distance_to_tuple((x, y)) <= self.max_radius and \
					self.center.distance_to_tuple((x, y)) >= self.min_radius:
					yield (x, y)

bind_all(Annulus)

