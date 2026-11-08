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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from . import Shape
	from .rect import Rect


class RadiusShape:
	"""Class for generic shapes with a radius.
	The shape includes everything, that the center contains plus every point,
	for which this holds: distance(point, center) <= radius
	The center can by any other shape.
	If the center is a point, it's actually a circle.
	"""

	center: Shape
	radius: int | float

	def __init__(self, center: Shape, radius: int | float) -> None:
		self.center = center
		self.radius = radius


class RadiusRect(RadiusShape):
	"""Specialization of RadiusShape with a Rect as center"""

	center: Rect

	def __init__(self, center: Rect, radius: int | float) -> None:
		super().__init__(center, radius)
