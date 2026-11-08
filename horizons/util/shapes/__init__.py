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

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any

from horizons.util.shapes import distances

if TYPE_CHECKING:
    from horizons.util.shapes.point import Point


class Shape:

	def get_coordinates(self) -> list[tuple[int, int]]:
		"""Return all coordinates in the shape."""
		return list(self.tuple_iter())

	def __iter__(self) -> Iterator[Point]:
		"""Return all coordinates in the shape as points."""
		for x, y in self.tuple_iter():
			yield Point(x, y)

	def tuple_iter(self) -> Iterator[tuple[int, int]]:
		raise NotImplementedError

	def _lookup_distance_function(
		self, other: Shape
	) -> tuple[Callable[..., Any], bool]:
		# TODO pre-build a dictionary for fast function lookup
		co1 = self.__class__.__name__.lower().replace('const', '')
		co2 = other.__class__.__name__.lower().replace('const', '')

		dist_func = getattr(distances, f"distance_{co1}_{co2}", None)
		if dist_func:
			return dist_func, False

		dist_func = getattr(distances, f"distance_{co2}_{co1}", None)
		if dist_func:
			return dist_func, True

		raise TypeError(f"No distance defined between {co1} and {co2}")

	def distance(self, other: Shape) -> float | int:
		dist_func = self.get_distance_function(other)
		return dist_func(self, other)

	def get_distance_function(
		self, other: Shape
	) -> Callable[..., Any]:
		dist_func, swap = self._lookup_distance_function(other)

		if not swap:
			return dist_func

		def swapped(a: Any, b: Any) -> Any:
			return dist_func(b, a)

		return swapped

# Convenience methods so you can use 'from horizons.util.shapes import Circle, Rect'


from horizons.util.shapes.annulus import Annulus
from horizons.util.shapes.circle import Circle
from horizons.util.shapes.point import ConstPoint, Point
from horizons.util.shapes.radiusshape import RadiusRect, RadiusShape
from horizons.util.shapes.rect import ConstRect, Rect
