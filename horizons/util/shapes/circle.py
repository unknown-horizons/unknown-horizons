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

from horizons.util.python.decorators import bind_all
from horizons.util.shapes.point import ConstPoint, Point

class Circle(object):
	"""Class for the shape of a circle
	You can access center and radius of the circle as public members."""
	def __init__(self, center, radius):
		"""
		@param center: Point
		@param radius: int
		"""
		assert isinstance(center, Point)
		self.center = center
		self.radius = radius

	def get_coordinates(self):
		"""Returns all coordinates, that are in the circle"""
		return [coord for coord in self.tuple_iter()]

	def contains(self, point):
		assert isinstance(point, Point)
		return point.distance_to_point(self.center) <= self.radius

	def center(self):
		return self.center

	def intersects_rect(self, rect):
		return rect.distance_to_point(self.center) > self.radius

	def __str__(self):
		return "Circle(center=%s,radius=%s)" % (self.center, self.radius)

	def __eq__(self, other):
		try:
			return self.center == other.center and self.radius == other.radius
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def distance(self, other):
		from horizons.util.shapes.annulus import Annulus
		from horizons.util.shapes.rect import Rect, ConstRect
		# trap method: init data, then replace this method with real method
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
		return other.distance_to_circle(self)

	def distance_to_tuple(self, other):
		dist = ((self.center.x - other[0]) ** 2 + (self.center.y - other[1]) ** 2) ** 0.5 - self.radius
		return dist if dist >= 0 else 0

	def distance_to_rect(self, other):
		return other.distance_to_circle(self)

	def distance_to_circle(self, other):
		dist = self.distance(other.center) - self.radius - other.radius
		return dist if dist >= 0 else 0

	def distance_to_annulus(self, other):
		dist = self.distance(other.center) - self.radius - other.max_radius
		return dist if dist >= 0 else 0

	def __iter__(self):
		"""Iterates through all coords in circle as Point"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if self.center.distance_to_tuple((x, y)) <= self.radius:
					yield Point(x, y)

	def tuple_iter(self):
		"""Iterates through all coords in circle as tuple"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if self.center.distance_to_tuple((x, y)) <= self.radius:
					yield (x, y)

	def get_border_coordinates(self, bordersize=1):
		"""Returns only coordinates at the border. Very naive implementation"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if (self.radius - bordersize) <= self.center.distance_to_tuple((x, y)) <= self.radius:
					yield (x,y)

bind_all(Circle)
