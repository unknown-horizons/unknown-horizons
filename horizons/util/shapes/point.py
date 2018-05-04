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

from horizons.util.python import Const
from horizons.util.shapes import Shape


class Point(Shape):
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def copy(self):
		return Point(self.x, self.y)

	def to_tuple(self):
		"""Returns point as a tuple"""
		return (self.x, self.y)

	@property
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
		return self.x == point.x and self.y == point.y

	def __str__(self):
		""" nice representation for debugging purposes """
		return 'Point({}, {})'.format(self.x, self.y)

	def __eq__(self, other):
		if other is None:
			return False
		elif isinstance(other, Point):
			return self.x == other.x and self.y == other.y
		else: # other is tuple
			try:
				return self.x == other[0] and self.y == other[1]
			except TypeError:
				return False

	def __add__(self, other):
		assert isinstance(other, Point)
		return Point(self.x + other.x, self.y + other.y)

	def __sub__(self, other):
		assert isinstance(other, Point)
		return Point(self.x - other.x, self.y - other.y)

	def __hash__(self):
		return hash((self.x, self.y))

	def tuple_iter(self):
		yield self.to_tuple()

	def iter_without_border(self):
		yield self


class ConstPoint(Const, Point):
	"""An immutable Point"""
	pass
