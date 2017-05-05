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

from . import Shape
from .point import Point


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

	def contains(self, point):
		assert isinstance(point, Point)
		dx = point.x - self.center.x
		dy = point.y - self.center.y
		return dx * dx + dy * dy <= self.radius * self.radius

	def intersects_rect(self, rect):
		return rect.distance(self.center) > self.radius

	def __str__(self):
		return "Circle(center={},radius={})".format(self.center, self.radius)

	def __eq__(self, other):
		try:
			return self.center == other.center and self.radius == other.radius
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash((self.center, self.radius))

	def tuple_iter(self):
		"""Iterate through all coords in the circle as tuples."""
		cx = self.center.x
		cy = self.center.y
		radius_sq = self.radius * self.radius
		for x in range(cx - self.radius, cx + self.radius + 1):
			for y in range(cy - self.radius, cy + self.radius + 1):
				dx = cx - x
				dy = cy - y
				dist_sq = dx * dx + dy * dy
				if dist_sq <= radius_sq:
					yield (x, y)

	def get_border_coordinates(self, bordersize=1):
		"""Returns only coordinates at the border. Very naive implementation"""
		for x in range(self.center.x - self.radius, self.center.x + self.radius + 1):
			for y in range(self.center.y - self.radius, self.center.y + self.radius + 1):
				if (self.radius - bordersize) <= self.center.distance((x, y)) <= self.radius:
					yield (x, y)
