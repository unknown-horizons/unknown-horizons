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
from horizons.util.shapes import Shape
from horizons.util.shapes.point import ConstPoint

class Circle(Shape):
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
		coords = []
		for i in self.tuple_iter():
			coords.append(i)
		return coords
		"""
		TODO: check this for correctness before using it
		return midpoint_circle(self.center.x, self.center.y, self.radius)
	  """

	def contains(self, point):
		assert isinstance(point, Point)
		if point.distance(self.center) <= self.radius:
			return True
		else:
			return False

	def center(self):
		return self.center

	def intersects_rect(self, rect):
		if rect.distance(self.center) >  self.radius:
			return True
		return False

	def __str__(self):
		return "Circle(center=%s,radius=%s)" % (self.center, self.radius)

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

	def __iter__(self):
		"""Iterates through all coords in circle as Point"""
		"""
		TODO: check this for correctness before using it
		for coord in midpoint_circle(self.center.x, self.center.y, self.radius):
			yield Point(*coord)
		"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if self.center.distance((x, y)) <= self.radius:
					yield Point(x, y)

	def tuple_iter(self):
		"""Iterates through all coords in circle as tuple"""
		"""
		TODO: check this for correctness before using it
		for coord in midpoint_circle(self.center.x, self.center.y, self.radius):
			yield coord
		"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if self.center.distance((x, y)) <= self.radius:
					yield (x, y)

	def get_border_coordinates(self, bordersize=1):
		"""Returns only coordinates at the border. Very naive implementation"""
		for x in xrange(self.center.x-self.radius, self.center.x+self.radius+1):
			for y in xrange(self.center.y-self.radius, self.center.y+self.radius+1):
				if (self.radius - bordersize) <= self.center.distance((x, y)) <= self.radius:
					yield (x,y)

def midpoint_circle(x0, y0, radius):
	"""Midpoint circle algorithm with filling.
	@see http://en.wikipedia.org/wiki/Midpoint_circle_algorithm.

	This isn't properly tested and adapted to the uh coord system, don't use like this.
	"""
	f = 1 - radius
	ddF_x = 1
	ddF_y = -2 * radius
	x = 0
	y = radius

	coords = set()

	add = coords.add

	#for c in xrange(x0 - radius - 1, x0 + radius) :
	#	add( (c, y0) )
	for c in xrange(y0 - radius - 1, y0 + radius) :
		add( (x0, c) )

	#add( (x0, y0+radius) )
	#add( (x0, y0-radius) )

	while x < y:
		if f >= 0:
			y -= 1
			ddF_y += 2
			f += ddF_y

		x += 1
		ddF_x += 2
		f += ddF_x


		for c in xrange(y0 - y - 1, y0 + y) :
			add( (x0 + x, c) )
			add( (x0 - x, c) )

		"""
		for c in xrange(x0 - x - 1, x0 + x) :
			add ( (c, y0 + y) )
			add ( (c, y0 - y) )

		for c in xrange(x0 - y - 1, x0 + y) :
			add ( (c, y0 + x) )
			add ( (c, y0 - x) )
		"""

	return coords


bind_all(Circle)

