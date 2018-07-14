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

from . import Shape
from .point import Point


class Rect(Shape):
	__slots__ = ('top', 'left', 'right', 'bottom', 'origin')

	def __init__(self, *args):
		if len(args) == 2 and isinstance(args[0], Point) and isinstance(args[1], Point): #args: edge1, edge2
			self.top = min(args[0].y, args[1].y)
			self.left = min(args[0].x, args[1].x)
			self.right = max(args[0].x, args[1].x)
			self.bottom = max(args[0].y, args[1].y)
		elif len(args) == 3 and isinstance(args[0], Point) and isinstance(args[1], int) and isinstance(args[2], int): #args: position, width, height
			self.top = args[0].y
			self.left = args[0].x
			self.right = self.left + args[1]
			self.bottom = self.top + args[2]
		elif len(args) == 4 and isinstance(args[0], int) and isinstance(args[1], int) and isinstance(args[2], int) and isinstance(args[3], int):
			self.top = min(args[1], args[3])
			self.left = min(args[0], args[2])
			self.right = max(args[0], args[2])
			self.bottom = max(args[1], args[3])

		else:
			assert False

		# Convenience attributes (can be used to make code more easy to read/understand)
		self.origin = Point(self.left, self.top)

	# NAMED CONSTRUCTORS:

	@classmethod
	def init_from_borders(cls, left, top, right, bottom):
		self = cls.__new__(cls)
		self.left = left
		self.top = top
		self.right = right
		self.bottom = bottom
		self.origin = Point(self.left, self.top)
		return self

	@classmethod
	def init_from_topleft_and_size(cls, x, y, width, height):
		self = cls.__new__(cls)
		self.left = x
		self.top = y
		self.right = x + width - 1
		self.bottom = y + height - 1
		self.origin = Point(self.left, self.top)
		return self

	@classmethod
	def init_from_topleft_and_size_tuples(cls, coords, size):
		self = cls.__new__(cls)
		self.left = coords[0]
		self.top = coords[1]
		self.right = coords[0] + size[0] - 1
		self.bottom = coords[1] + size[1] - 1
		self.origin = Point(self.left, self.top)
		return self

	@classmethod
	def init_from_corners(cls, point1, point2):
		"""Init rect with 2 points interpreted as 2 corner points"""
		self = cls.__new__(cls)
		x_coords = [int(round(point1.x)), int(round(point2.x))]
		x_coords.sort()
		self.left = x_coords[0]
		self.right = x_coords[1]
		y_coords = [int(round(point1.y)), int(round(point2.y))]
		y_coords.sort()
		self.top = y_coords[0]
		self.bottom = y_coords[1]
		self.origin = Point(self.left, self.top)
		return self

	@property
	def height(self):
		return self.bottom - self.top + 1

	@property
	def width(self):
		return self.right - self.left + 1

	def copy(self):
		return Rect.init_from_borders(self.left, self.top, self.right, self.bottom)

	def get_radius_coordinates(self, radius, include_self=False):
		"""Returns list of all coordinates (as tuples), that are in the radius
		This is a generator.
		@param include_self: whether to include coords in self"""
		# NOTE: this function has to be very fast, since it's blocking on building select
		#       therefore, the distance_to_tuple function is inlined manually.
		"""
		ALGORITHM:
		Idea:
		calculate the borders of the shape for every line (y-axis) to the left and the right
		and fill it up later.
		The borders are calculated this way:
		Take a corner (here we use top right) and calculate a quarter of a circle (top right quarter).
		This can be mirrored to every other corner.
		Then there is only the space exactly above, below and left and right to the rect left.
		Here, since we only got along one axis, we know that the border coords are right + radius, etc.
		q.e.d. ;)
		"""
		borders = {}

		# start with special case

		# above, below
		borders[self.top - radius] = (self.left, self.right)
		borders[self.bottom + radius] = (self.left, self.right)

		# left, right
		for y in range(self.top, self.bottom + 1):
			borders[y] = (self.left - radius, self.right + radius)

		x = radius
		radius_squared = radius ** 2
		# calculate border for line y (y = 0 and y = radius are special cases handled above)
		for y in range(1, radius):
			test_val = radius_squared - y ** 2
			# TODO: check if it's possible if x is decreased more than once here.
			#       if not, change the while to an if
			while (x ** 2) > test_val: # this is equivalent to  x^2 + y^2 > radius^2
				x -= 1

			# both sides are symmetrical, since it's a rect
			borders[self.top - y] = (self.left - x, self.right + x)
			borders[self.bottom + y] = (self.left - x, self.right + x)

		if not include_self:
			self_coords = frozenset(self.get_coordinates())
			for y, x_range in borders.items():
				if self.top <= y <= self.bottom: # we have to sort out the self_coords here
					for x in range(x_range[0], x_range[1] + 1):
						t = (x, y)
						if t not in self_coords:
							yield t
				else: # coords of this rect cannot appear here
					for x in range(x_range[0], x_range[1] + 1):
						yield (x, y)
		else:
			for y, x_range in borders.items():
				for x in range(x_range[0], x_range[1] + 1):
					yield (x, y)

	@property
	def center(self):
		"""Returns the center point of the rect.
		Implemented with integer division, which means the upper left is preferred."""
		return Point((self.right + self.left) // 2, (self.bottom + self.top) // 2)

	def __contains__(self, point):
		return self.contains(point)

	def contains(self, point):
		""" Returns if this rect (self) contains the point.
		@param point: Point that is checked to be in this rect
		@return: Returns whether the Point point is in this rect (self).
		"""
		return (self.left <= point.x <= self.right) and (self.top <= point.y <= self.bottom)

	def contains_without_border(self, point):
		"""Same as contains, see iter_without_border for difference"""
		return (self.left <= point.x < self.right) and (self.top <= point.y < self.bottom)

	def contains_tuple(self, tup):
		"""Same as contains, but takes a tuple (x, y) as parameter (overloaded function)"""
		return (self.left <= tup[0] <= self.right) and (self.top <= tup[1] <= self.bottom)

	def intersect(self, rect):
		""" Returns a rect that is the intersection of this rect and the rect parameter.
		@param rect: Rect that will be intersected with this rect.
		@return: A Rect which is the intersection of self and rect or None if the intersection is empty.
		"""
		if not self.intersects(rect):
			return None
		return Rect(max(self.left, rect.left), max(self.top, rect.top),
		            min(self.right, rect.right), min(self.bottom, rect.bottom))

	def intersects(self, rect):
		""" Returns if the rectangle intersects with the rect parameter.
		@param rect: Rect that will be intersected with this rect.
		@return: A bool.
		"""
		return not (rect.right < self.left or self.right < rect.left
		            or rect.bottom < self.top or self.bottom < rect.top)

	def get_corners(self):
		"""Returns corners of rect in this order: topleft topright bottomright bottomleft
		@return: tuple of coord-tuples"""
		return ((self.left, self.top), (self.right, self.top),
		        (self.right, self.bottom), (self.left, self.bottom))

	def get_surrounding(self, include_corners=True):
		"""Returns neighboring coords of the rect.
		@param include_corners: whether to also move diagonally from the rect corners"""
		# top and bottom
		surrounding_top = self.top - 1
		surrounding_bottom = self.bottom + 1
		for x in range(self.left, self.right + 1):
			yield (x, surrounding_bottom)
			yield (x, surrounding_top)
		# left and right
		surrounding_left = self.left - 1
		surrounding_right = self.right + 1
		for y in range(self.top, self.bottom + 1):
			yield (surrounding_left, y)
			yield (surrounding_right, y)

		if include_corners:
			yield (self.left - 1, self.top - 1)
			yield (self.right + 1, self.top - 1)
			yield (self.left - 1, self.bottom + 1)
			yield (self.right + 1, self.bottom + 1)

	def __str__(self):
		return "Rect(o:({},{}),w:{},h:{})".format(self.left, self.top, self.width, self.height)

	def __eq__(self, other):
		if not isinstance(other, Rect):
			return False
		return (self.top == other.top and self.left == other.left
		        and self.right == other.right and self.bottom == other.bottom)

	def __ne__(self, other):
		return not self.__eq__(other)

	def __lt__(self, other):
		if self.left != other.left:
			return self.left < other.left
		if self.top != other.top:
			return self.top < other.top
		if self.right != other.right:
			return self.right < other.right
		return self.bottom < other.bottom

	def __hash__(self):
		return hash((self.top, self.right, self.bottom, self.left))

	def tuple_iter(self):
		"""Generates an iterator, that returns tuples"""
		for x in range(self.left, self.right + 1):
			for y in range(self.top, self.bottom + 1):
				yield x, y

	def iter_without_border(self):
		"""There are 2 possible interpretations about what *width* means.
		You can either include the last point in the area calculation or
		just consider points without any extensions.
		This method iterates over the points without extensions, while the
		default iteration behavior in other methods is to include said area.
		"""
		for x in range(self.left, self.right):
			for y in range(self.top, self.bottom):
				yield Point(x, y)

	@classmethod
	def get_surrounding_offsets(cls, size):
		rect = cls.init_from_topleft_and_size_tuples((0, 0), size)
		return list(rect.get_surrounding())


class ConstRect(Const, Rect):
	"""An immutable Rect.
	Can be used for manual const-only optimization"""
	pass
