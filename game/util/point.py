# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

class Point(object):
	def __init__(self, x, y):
		self.x, self.y = x, y

	def copy(self):
		return Point(self.x, self.y)

	def distance(self, other):
		if isinstance(other, Point):
			return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
		elif isinstance(other, tuple):
			return ((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2) ** 0.5
		else:
			return other.distance(self)

	def get_coordinates(self):
		""" Returns point as coordinate
		This is useful, because Rect supports this too.
		"""
		return [(self.x, self.y)]

	def offset(self, x_offset, y_offset):
		"""Returns a Point with an offset of x, y relative to this Point.
		@param x_offset: int relative x-offset of the point to return
		@param y_offset: int relative y-offset of the point to return
		@return: a Point with offset x, y relative to the 'self' Point
		"""
		return Point(self.x + x_offset, self.y + y_offset)

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

from game.util.encoder import register_classes
register_classes(Point)
