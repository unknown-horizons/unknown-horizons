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

from . import Shape
from .point import Point


class Annulus(Shape):
	"""Class for the shape of an annulus
	You can access center and radius of the annulus as public members."""

	center: Point
	min_radius: int
	max_radius: int

	def __init__(self, center: Point, min_radius: int, max_radius: int) -> None:
		"""
		@param center: Point
		@param min_radius: int
		@param max_radius: int
		"""
		assert isinstance(center, Point)
		self.center = center
		self.min_radius = min_radius
		self.max_radius = max_radius

	def contains(self, point: Point) -> bool:
		assert isinstance(point, Point)
		return self.min_radius <= point.distance(self.center) <= self.max_radius

	def __str__(self) -> str:
		return f"Annulus(center={self.center},min_radius={self.min_radius},max_radius={self.max_radius})"

	def __eq__(self, other: object) -> bool:
		try:
			return (
				self.center == other.center
				and self.min_radius == other.min_radius
				and self.max_radius == other.max_radius
			)
		except AttributeError:
			return False

	def __ne__(self, other: object) -> bool:
		return not self.__eq__(other)

	def __hash__(self) -> int:
		return hash((self.center, self.min_radius, self.max_radius))

	def tuple_iter(self) -> Iterator[tuple[int, int]]:
		for x in range(self.center.x - self.max_radius, self.center.x + self.max_radius + 1):
			for y in range(self.center.y - self.max_radius, self.center.y + self.max_radius + 1):
				if self.min_radius <= self.center.distance((x, y)) <= self.max_radius:
					yield (x, y)
