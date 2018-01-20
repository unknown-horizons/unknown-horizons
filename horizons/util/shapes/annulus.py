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


class Annulus(Shape):
	"""Class for the shape of an annulus
	You can access center and radius of the annulus as public members."""
	def __init__(self, center, min_radius, max_radius):
		"""
		@param center: Point
		@param min_radius: int
		@param max_radius: int
		"""
		assert isinstance(center, Point)
		self.center = center
		self.min_radius = min_radius
		self.max_radius = max_radius

	def contains(self, point):
		assert isinstance(point, Point)
		return self.min_radius <= point.distance(self.center) <= self.max_radius

	def __str__(self):
		return ("Annulus(center={},min_radius={},max_radius={})"
				.format(self.center, self.min_radius, self.max_radius))

	def __eq__(self, other):
		try:
			return self.center == other.center and \
			       self.min_radius == other.min_radius and \
			       self.max_radius == other.max_radius
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash((self.center, self.min_radius, self.max_radius))

	def tuple_iter(self):
		for x in range(self.center.x - self.max_radius, self.center.x + self.max_radius + 1):
			for y in range(self.center.y - self.max_radius, self.center.y + self.max_radius + 1):
				if self.min_radius <= self.center.distance((x, y)) <= self.max_radius:
					yield (x, y)
