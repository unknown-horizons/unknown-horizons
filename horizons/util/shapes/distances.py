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


# Point
def distance_point_point(p1, p2):
	return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5


def distance_point_tuple(point, coord_tuple):
	x, y = coord_tuple
	return ((point.x - x) ** 2 + (point.y - y) ** 2) ** 0.5


def distance_point_circle(point, circle):
	dist = point.distance(circle.center) - circle.radius
	return dist if dist >= 0 else 0


def distance_point_rect(point, rect):
	return ((max(rect.left - point.x, 0, point.x - rect.right) ** 2) +
            (max(rect.top - point.y, 0, point.y - rect.bottom) ** 2)) ** 0.5


def distance_point_annulus(point, annulus):
	dist = point.distance(annulus.center)
	if dist < annulus.min_radius:
		return annulus.min_radius - dist
	if dist > annulus.max_radius:
		return dist - annulus.max_radius
	return 0


# Circle
def distance_circle_circle(c1, c2):
	dist = c1.distance(c2.center) - c1.radius - c2.radius
	return dist if dist >= 0 else 0


def distance_circle_tuple(circle, coord_tuple):
	x, y = coord_tuple
	dist = ((circle.center.x - x) ** 2 + (circle.center.y - y) ** 2) ** 0.5 - circle.radius
	return dist if dist >= 0 else 0


def distance_circle_annulus(circle, annulus):
	dist = circle.distance(annulus.center) - circle.radius - annulus.max_radius
	return dist if dist >= 0 else 0


# Rect
def distance_rect_rect(r1, r2):
	dx = 0
	t = r1.left - r2.right
	if t > dx:
		dx = t
	t = r2.left - r1.right
	if t > dx:
		dx = t

	dy = 0
	t = r1.top - r2.bottom
	if t > dy:
		dy = t
	t = r2.top - r1.bottom
	if t > dy:
		dy = t
	return (dx * dx + dy * dy) ** 0.5


def distance_rect_rect_sq(r1, r2):
	dx = 0
	t = r1.left - r2.right
	if t > dx:
		dx = t
	t = r2.left - r1.right
	if t > dx:
		dx = t

	dy = 0
	t = r1.top - r2.bottom
	if t > dy:
		dy = t
	t = r2.top - r1.bottom
	if t > dy:
		dy = t
	return dx * dx + dy * dy


def distance_rect_tuple(rect, coord_tuple):
	x, y = coord_tuple
	dx = 0
	t = rect.left - x
	if t > dx:
		dx = t
	t = x - rect.right
	if t > dx:
		dx = t

	dy = 0
	t = rect.top - y
	if t > dy:
		dy = t
	t = y - rect.bottom
	if t > dy:
		dy = t
	return (dx * dx + dy * dy) ** 0.5


def distance_rect_circle(rect, circle):
	dist = rect.distance(circle.center) - circle.radius
	return dist if dist >= 0 else 0


def distance_rect_annulus(rect, annulus):
	dist = rect.distance(annulus.center) - annulus.max_radius
	return dist if dist >= 0 else 0


# Annulus
def distance_annulus_annulus(a1, a2):
	dist = a1.distance(a2.center) - a1.max_radius - a2.max_radius
	return dist if dist >= 0 else 0


def distance_annulus_tuple(annulus, coord_tuple):
	(x, y) = coord_tuple
	dist = ((annulus.center.x - x) ** 2 + (annulus.center.y - y) ** 2) ** 0.5
	if dist < annulus.min_radius:
		return annulus.min_radius - dist
	if dist > annulus.max_radius:
		return dist - annulus.max_radius
	return 0


# DEBUG
if __name__ == '__main__':
	import itertools
	from . import distances
	shapes = ('rect', 'point', 'tuple', 'circle', 'annulus')
	for s1, s2 in itertools.product(shapes, shapes):
		if not (hasattr(distances, 'distance_{}_{}'.format(s1, s2)) or
		        hasattr(distances, 'distance_{}_{}'.format(s2, s1))):
			print('missing distance between', s1, s2)
