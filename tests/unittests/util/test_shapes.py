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

from horizons.util.shapes import Annulus, Circle, Point, Rect
from horizons.util.shapes.radiusshape import RadiusRect


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

    assert c1 != c2
    assert c1.get_coordinates() == [
        (-1, 0),
        (0, -1),
        (0, 0),
        (0, 1),
        (1, 0),
    ]
    assert c3.get_coordinates() == [(0, 0)]


@pytest.mark.parametrize(
    ("shape_a", "shape_b"),
    [
        (Point(0, 0), Rect(2, 2, 3, 3)),
        (Rect(2, 2, 3, 3), Point(0, 0)),
        (Point(0, 0), Circle(Point(5, 0), 1)),
        (Circle(Point(5, 0), 1), Point(0, 0)),
        (Point(0, 0), Annulus(Point(10, 10), 2, 5)),
        (Annulus(Point(10, 10), 2, 5), Point(0, 0)),
    ],
)
def test_distance_is_symmetric(shape_a, shape_b):
    assert shape_a.distance(shape_b) == shape_b.distance(shape_a)


@pytest.mark.parametrize(
    ("shape", "coord", "expected"),
    [
        (Point(0, 0), (3, 4), 5.0),
        (Circle(Point(0, 0), 1), (3, 4), 4.0),
        (Rect(0, 0, 1, 1), (3, 4), 13 ** 0.5),
    ],
)
def test_distance_to_tuple(shape, coord, expected):
    assert shape.distance(coord) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("point", "expected"),
    [
        (Point(2, 0), True),
        (Point(4, 0), True),
        (Point(1, 0), False),
        (Point(5, 0), False),
    ],
)
def test_annulus_contains(point, expected):
    annulus = Annulus(Point(0, 0), 2, 4)

    assert annulus.contains(point) is expected


def test_annulus_distance():
    annulus = Annulus(Point(0, 0), 2, 4)

    assert annulus.distance((0, 0)) == 2.0
    assert annulus.distance((3, 0)) == 0.0
    assert annulus.distance((5, 0)) == 1.0


def test_circle_contains_border():
    circle = Circle(Point(0, 0), 2)

    assert circle.contains(Point(2, 0))
    assert circle.contains(Point(0, 2))
    assert not circle.contains(Point(3, 0))


def test_zero_radius_circle():
    circle = Circle(Point(5, 5), 0)

    assert circle.contains(Point(5, 5))
    assert not circle.contains(Point(5, 6))


@pytest.mark.parametrize(
    ("point", "expected"),
    [
        (Point(0, 0), True),
        (Point(2, 2), True),
        (Point(-1, 0), False),
        (Point(0, 3), False),
    ],
)
def test_rect_contains(point, expected):
    rect = Rect(0, 0, 2, 2)

    assert rect.contains(point) is expected


def test_rect_intersection():
    rect1 = Rect(0, 0, 3, 3)
    rect2 = Rect(2, 2, 5, 5)

    assert rect1.intersect(rect2) == Rect(2, 2, 3, 3)


def test_rect_intersection_empty():
    rect1 = Rect(0, 0, 1, 1)
    rect2 = Rect(3, 3, 4, 4)

    assert rect1.intersect(rect2) is None


def test_point_hash_and_equality():
    p1 = Point(1, 2)
    p2 = Point(1, 2)

    assert p1 == p2
    assert hash(p1) == hash(p2)


def test_rect_hash_and_equality():
    r1 = Rect(0, 0, 1, 1)
    r2 = Rect(0, 0, 1, 1)

    assert r1 == r2
    assert hash(r1) == hash(r2)


def test_shape_iterator_returns_points():
    rect = Rect(0, 0, 1, 1)

    points = list(rect)

    assert len(points) == 4
    assert all(isinstance(point, Point) for point in points)


def test_radius_rect():
    rect = Rect(0, 0, 1, 1)

    radius_rect = RadiusRect(rect, 5)

    assert radius_rect.center == rect
    assert radius_rect.radius == 5


@pytest.mark.parametrize(
    ("shape", "other"),
    [
        (Point(0, 0), Rect(2, 2, 3, 3)),
        (Rect(2, 2, 3, 3), Point(0, 0)),
        (Point(0, 0), Circle(Point(5, 0), 1)),
        (Circle(Point(5, 0), 1), Point(0, 0)),
    ],
)
def test_get_distance_function_contract(shape, other):
    func = shape.get_distance_function(other)

    assert func(shape, other) == shape.distance(other)
