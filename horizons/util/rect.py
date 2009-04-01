# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

class Rect(object):
	def __init__(self, *args):
		if len(args) == 1 and isinstance(args[0], Rect): #args: rect
			self.top, self.left, self.right, self.bottom = args[0].top, args[0].left, args[0].right, args[0].bottom
		elif len(args) == 2 and isinstance(args[0], Point) and isinstance(args[1], Point): #args: edge1, edge2
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

		#development assert:
		elif __debug__:
			if len(args) > 0 and isinstance(args[0], Rect):
				assert False, "Tried to init rect with rect"
			else:
				assert False, 'Invalid rect initialisation'+str(args)

		# Convenience attributes (can be used to make code more easy to read/understand)
		self.origin = Point(self.left, self.top)

	def distance(self, other):
		"""Calculates distance to another object"""
		if isinstance(other, Point):
			return self.distance_to_point(other)
		elif isinstance(other, Rect):
			return self.distance_to_rect(other)
		else:
			## TODO: other = (x,y, width, height)
			# is other tuple: (x,y)?
			if isinstance(other[0], int) and isinstance(other[1], int):
				return self.distance_to_tuple(other)
			else:
				return other.distance(self)

	def distance_to_point(self, other):
		"""Calculates distance to an instance of Point.
		Don't use this, unless you are sure that distance() is too slow."""
		return ((max(self.left - other.x, 0, other.x - self.right) ** 2) + (max(self.top - other.y, 0, other.y - self.bottom) ** 2)) ** 0.5

	def distance_to_tuple(self, other):
		"""Calculates distance to a coordinate as tuple (x,y)
		Don't use this, unless you are sure that distance() is too slow."""
		return ((max(self.left - other[0], 0, other[0] - self.right) ** 2) + (max(self.top - other[1], 0, other[1] - self.bottom) ** 2)) ** 0.5

	def distance_to_rect(self, other):
		"""Calculates distance to an instance of Rect.
		Don't use this, unless you are sure that distance() is too slow."""
		return ((max(self.left - other.right, 0, other.left - self.right) ** 2) + (max(self.top - other.bottom, 0, other.top - self.bottom) ** 2)) ** 0.5

	# TODO: replace this everywhere with iteration
	def get_coordinates(self):
		""" Returns all coordinates, that are in the Rect """
		return [ (x,y) for x in xrange(self.left, self.right+1) for y in xrange(self.top, self.bottom+1) ]

	# TODO: reimplement this with Rect.__iter__
	def get_radius_coordinates(self, radius):
		""" Returns a list of all coordinates, that are in the radius but are in not the building"""
		self_coords = self.get_coordinates()
		return  [ (x,y) for x in xrange(self.left-radius, self.right+radius+1) \
				  for y in xrange(self.top-radius, self.bottom+radius+1)
						if (x,y) not in self_coords and \
						self.distance_to_tuple( (x,y) ) <= radius ]

	def center(self):
		""" Returns the center point of the rect. Implemented with integer division, which means the upper left is preferred """
		return Point((self.right - self.left) // 2, (self.bottom - self.top) // 2)

	def contains(self, point):
		""" Returns if this rect (self) contains the point.
		@param point: Point that is checked to be in this rect
		@return: Returns whether the Point point is in this rect (self).
		"""
		return (self.left <= point.x <= self.right) and (self.top <= point.y <= self.bottom)

	def intersect(self, rect):
		""" Returns a rect that is the intersection of this rect and the rect parameter.
		@param rect: Rect that will be intersected with this rect.
		@return: A Rect which is the intersection of self and rect or None if the intersection is empty.
		"""
		if not self.intersects(rect):
			return None
		return Rect(max(self.left, rect.left), max(self.top, rect.top), min(self.right, rect.right), min(self.bottom, rect.bottom))

	def intersects(self, rect):
		""" Returns if the rectangle intersects with the rect parameter.
		@param rect: Rect that will be intersected with this rect.
		@return: A bool.
		"""
		return not (rect.right < self.left or self.right < rect.left or rect.bottom < self.top or self.bottom < rect.top)

	def __str__(self):
		# nice representation for debugging purposes
		return "Rect(%s, %s, %s, %s)" % (self.top, self.left, self.right, self.bottom)

	def __eq__(self, other):
		if isinstance(other, Rect):
			return (self.top==other.top and self.left==other.left and self.right==other.right and self.bottom==other.bottom)
		return False

	def __iter__(self):
		for x in xrange(self.left, self.right+1):
			for y in xrange(self.top, self.bottom+1):
				yield Point(x, y)

from game.util.encoder import register_classes
register_classes(Rect)
