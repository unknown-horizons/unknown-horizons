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

from horizons.util.shapes import distances


class Shape:

	def get_coordinates(self):
		"""Return all coordinates in the shape."""
		return list(self.tuple_iter())

	def __iter__(self):
		"""Return all coordinates in the shape as points."""
		for x, y in self.tuple_iter():
			yield Point(x, y)

	def tuple_iter(self):
		raise NotImplementedError

	def distance(self, other):
		# TODO pre-build a dictionary for fast function lookup
		co1 = self.__class__.__name__.lower()
		co2 = other.__class__.__name__.lower()

		# ConstX and X are the same w.r.t to distances
		co1 = co1.replace('const', '')
		co2 = co2.replace('const', '')

		dist = getattr(distances, "distance_{}_{}".format(co1, co2), None)
		if dist:
			return dist(self, other)
		else:
			dist = getattr(distances, "distance_{}_{}".format(co2, co1), None)
			if dist:
				return dist(other, self)

		raise TypeError("No distance defined between {} and {}".format(co1, co2))

	def get_distance_function(self, other):
		# TODO pre-build a dictionary for fast function lookup
		co1 = self.__class__.__name__.lower()
		co2 = other.__class__.__name__.lower()

		# ConstX and X are the same w.r.t to distances
		co1 = co1.replace('const', '')
		co2 = co2.replace('const', '')

		dist_func = getattr(distances, "distance_{}_{}".format(co1, co2), None)
		if dist_func:
			return dist_func

		dist_func = getattr(distances, "distance_{}_{}".format(co2, co1), None)
		if dist_func:
			return dist_func

		raise TypeError("No distance defined between {} and {}".format(co1, co2))

# Convenience methods so you can use 'from horizons.util.shapes import Circle, Rect'


from horizons.util.shapes.point import ConstPoint, Point # isort:skip
from horizons.util.shapes.rect import ConstRect, Rect # isort:skip
from horizons.util.shapes.annulus import Annulus # isort:skip
from horizons.util.shapes.circle import Circle # isort:skip
from horizons.util.shapes.radiusshape import RadiusRect, RadiusShape # isort:skip
