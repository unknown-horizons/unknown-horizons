###################################################
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

from __future__ import annotations

from collections.abc import Iterator

from horizons.util.python import Const
from horizons.util.shapes import Shape


class Point(Shape):
	x: int
	y: int

	def __init__(self, x: int, y: int) -> None:
		self.x = x
		self.y = y

	def copy(self) -> Point:
		return Point(self.x, self.y)

	def to_tuple(self) -> tuple[int, int]:
		"""Returns point as a tuple"""
		return (self.x, self.y)

	@property
	def center(self) -> Point:
		"""Returns the center of the point (this makes Point interface more coherent with Rect).
		"""
		return self

	def offset(self, x_offset: int, y_offset: int) -> Point:
		"""Returns a Point with an offset of x, y relative to this Point.
		@param x_offset: int relative x-offset of the point to return
		@param y_offset: int relative y-offset of the point to return
		@return: a Point with offset x, y relative to the 'self' Point
		"""
		return Point(self.x + x_offset, self.y + y_offset)

	def contains(self, point: Point) -> bool:
		"""For compatibility with Rect"""
		return self.x == point.x and self.y == point.y

	def __str__(self) -> str:
		""" nice representation for debugging purposes """
		return f'Point({self.x}, {self.y})'

	def __eq__(self, other: object) -> bool:
		if other is None:
			return False
		elif isinstance(other, Point):
			return self.x == other.x and self.y == other.y
		else:  # other is tuple
			try:
				return self.x == other[0] and self.y == other[1]
			except TypeError:
				return False

	def __add__(self, other: Point) -> Point:
		assert isinstance(other, Point)
		return Point(self.x + other.x, self.y + other.y)

	def __sub__(self, other: Point) -> Point:
		assert isinstance(other, Point)
		return Point(self.x - other.x, self.y - other.y)

	def __hash__(self) -> int:
		return hash((self.x, self.y))

	def tuple_iter(self) -> Iterator[tuple[int, int]]:
		yield self.to_tuple()

	def iter_without_border(self) -> Iterator[Point]:
		yield self


class ConstPoint(Const, Point):
	"""An immutable Point"""
	pass
