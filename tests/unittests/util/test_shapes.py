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

import pytest

from horizons.util.shapes import Circle, Point, Rect


def test_point():
	p1 = Point(0, 0)
	p2 = Point(0, 2)
	assert p1.distance(p2) == 2
	assert p1.distance((0, 1)) == 1
	assert p1.get_coordinates() == [(0, 0)]
	assert p1 == p1.copy()


def test_rect():
	r1 = Rect(Point(0, 0), 1, 1)
	r2 = Rect(0, 0, 1, 1)
	r3 = Rect(Point(2, 2), 1, 1)
	assert r1 == r2
	assert not r1.contains(Point(-1, -1))
	assert r2.contains(Point(0, 0))
	assert r2.contains(Point(1, 1))
	assert r1.intersects(r2)
	assert not r1.intersects(r3)


def test_circle():
	c1 = Circle(Point(0, 0), 1)
	c2 = Circle(Point(0, 0), 2)
	c3 = Circle(Point(0, 0), 0)
	assert not (c1 == c2)
	assert c1 != c2
	assert c1.get_coordinates() == [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]
	assert c3.get_coordinates() == [(0, 0)]
