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

from horizons.util.python.decorators import make_constants

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

	@make_constants()
	def get_coordinates(self):
		"""Returns all coordinates, that are in the circle"""
		coords = []
		for i in self.tuple_iter():
			coords.append(i)
		return coords

	@make_constants()
	def contains(self, point):
		assert isinstance(point, Point)
		if point.distance_to_point(self.center) <= self.radius:
			return True
		else:
			return False

	@make_constants()
	def intersects_rect(self, rect):
		if rect.distance_to_point(self.center) >  self.radius:
			return True
		return False

	def __str__(self):
		return "Circle(center=%s,radius=%s)" % (self.center, self.radius)

	@make_constants()
	def __eq__(self, other):
		try:
			if self.center == other.center and \
				 self.radius == other.radius:
				return True
			else:
				return False
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	@make_constants()
	def __iter__(self):
		"""Iterates through all coords in circle as Point"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if self.center.distance_to_tuple((x, y)) <= self.radius:
					yield Point(x, y)

	@make_constants()
	def tuple_iter(self):
		"""Iterates through all coords in circle as tuple"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if self.center.distance_to_tuple((x, y)) <= self.radius:
					yield (x, y)

