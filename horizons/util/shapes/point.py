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

from fife import fife

from horizons.util.python.decorators import bind_all
from horizons.util.python import Const

class Point(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def copy(self):
		return Point(self.x, self.y)

	def distance(self, other):
		# trap method: init data, then replace this method with real method
		from circle import Circle
		from rect import Rect, ConstRect
		from annulus import Annulus
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
		return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

	def distance_to_tuple(self, other):
		return ((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2) ** 0.5

	def distance_to_rect(self, other):
		return ((max(other.left - self.x, 0, self.x - other.right) ** 2) +
						(max(other.top - self.y, 0, self.y - other.bottom) ** 2)) ** 0.5

	def distance_to_circle(self, other):
		dist = self.distance(other.center) - other.radius
		return dist if dist >= 0 else 0

	def distance_to_annulus(self, other):
		dist = self.distance(other.center)
		if dist < other.min_radius:
			return other.min_radius - dist
		if dist > other.max_radius:
			return dist - other.max_radius
		return 0

	def get_coordinates(self):
		""" Returns point as coordinate
		This is useful, because Rect supports this too.
		"""
		return [self.to_tuple()]

	def to_tuple(self):
		"""Returns point as a tuple"""
		return (self.x, self.y)

	def to_fife_point(self):
		"""Returns point as fife.Point"""
		return fife.Point(self.x, self.y)

	def center(self):
		"""Returns the center of the point (this makes Point interface more coherent with Rect).
		"""
		return self

	def offset(self, x_offset, y_offset):
		"""Returns a Point with an offset of x, y relative to this Point.
		@param x_offset: int relative x-offset of the point to return
		@param y_offset: int relative y-offset of the point to return
		@return: a Point with offset x, y relative to the 'self' Point
		"""
		return Point(self.x + x_offset, self.y + y_offset)

	def contains(self, point):
		"""For compatibility with Rect"""
		return (self.x == point.x and self.y == point.y)

	def __str__(self):
		""" nice representation for debugging purposes """
		return 'Point(%s, %s)' % (self.x, self.y)

	def __eq__(self, other):
		if other is None:
			return False
		elif isinstance(other, Point):
			return (self.x == other.x and self.y == other.y)
		else: # other is tuple
			try:
				return (self.x == other[0] and self.y == other[1])
			except TypeError:
				return False

	def __add__(self, other):
		assert isinstance(other, Point)
		return Point(self.x+other.x, self.y+other.y)

	def __sub__(self, other):
		assert isinstance(other, Point)
		return Point(self.x-other.x, self.y-other.y)

	def __iter__(self):
		"""For interface-sharing with Rect"""
		yield self

	def tuple_iter(self):
		yield self.to_tuple()

	def iter_without_border(self):
		yield self

class ConstPoint(Const, Point):
	"""An immutable Point"""
	pass


bind_all(Point)
bind_all(ConstPoint)

