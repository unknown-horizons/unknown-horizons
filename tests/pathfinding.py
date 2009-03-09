#!/usr/bin/env python

# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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


"""
NOT MAINTAINED

import unittest

from game.world.pathfinding import findPath
from game.util import Point, Rect

class TestPathfinding(unittest.TestCase):

	def testA(self):
		p = findPath(Point(1,1), Rect(2,2,2,2), [(1,2)])
		self.assertEqual(p, [(1, 1), (1, 2), (2, 2)])

	def testB(self):
		p = findPath(Point(1,1), Rect(2,2,2,2), [(1,2)], diagonal = True)
		self.assertEqual(p,[(1, 1), (2, 2)])

	def testC(self):
		p = findPath(Point(1,1), Rect(3,3,3,3), [(1,2),(2,2),(2,1),(2,3)])
		self.assertEqual(p, [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3)])

	def testD(self):
		p = findPath(Point(1,1), Rect(3,3,5,5), [(1,2),(2,2),(2,1),(2,3)])
		self.assertEqual(p, [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3)])

		# missing:
		# - different source/target formats
		# - blocked_choords

"""