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

class Circle(object):
	def __init__(self, center, radius):
		assert isinstance(center, Point)
		self.center = center
		self.radius = radius

	def get_coordinates(self):
		"""Returns all coordinates, that are in the circle"""
		return [ (x, y) for \
						 x in range(self.center.x-self.radius, self.center.x+self.radius+1) for \
						 y in range(self.center.y-self.radius, self.center.y+self.radius+1) if \
						 self.center.distance((x, y)) <= self.radius ]

from encoder import register_classes
register_classes(Circle)