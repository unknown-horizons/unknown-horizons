#!/usr/bin/env python

# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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



import unittest

from horizons.util import Point, Rect, Circle

class TestPathfinding(unittest.TestCase):

	def testPoint(self):
		p1 = Point(0,0)
		p2 = Point(0,2)
		self.assertEqual(p1.distance(p2), 2)
		self.assertEqual(p1.distance((0,1)), 1)
		self.assertEqual(p1.get_coordinates(), [(0,0)])
		self.assertEqual(p1, p1.copy())

	def testRect(self):
		r1 = Rect(Point(0,0), 1, 1)
		r2 = Rect(0, 0, 1 ,1)
		r3 = Rect(Point(2, 2), 1, 1)
		self.assertEqual(r1, r2)
		self.assertTrue(r1 == r2)
		self.assertFalse(r1.contains(Point(-1,-1)))
		self.assertTrue(r2.contains(Point(0,0)))
		self.assertTrue(r2.contains(Point(1,1)))
		self.assertTrue(r1.intersects(r2))
		self.assertFalse(r1.intersects(r3))

	def testCircle(self):
		c1 = Circle(Point(0,0), 1)
		c2 = Circle(Point(0,0), 2)
		c3 = Circle(Point(0,0), 0)
		self.assertFalse(c1 == c2)
		self.assertTrue(c1 != c2)
		self.assertNotEqual(c1, c2)
		self.assertEqual(c1.get_coordinates(), [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)])
		self.assertEqual(c3.get_coordinates(), [(0,0)])
