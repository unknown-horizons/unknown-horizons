#!/usr/bin/env python

# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.world.storage import *

class TestStorages(unittest.TestCase):

	def test_specialized(self):
		s = SpecializedStorage()

		self.assertEqual(s.alter(1, 3), 3)
		self.assertEqual(s.alter(1, -3), -3)

		self.assertFalse(s.has_resource_slot(1))
		s.add_resource_slot(1)
		self.assertTrue(s.has_resource_slot(1))

		self.assertEqual(s.alter(1, 3), 0)
		self.assertEqual(s.alter(1, -3), 0)

	def test_sized_specialized(self, s = SizedSpecializedStorage()):

		self.assertEqual(s.alter(1, 3), 3)
		self.assertEqual(s.alter(1, -3), -3)

		self.assertFalse(s.has_resource_slot(1))
		s.add_resource_slot(1, 10)
		self.assertTrue(s.has_resource_slot(1))
		self.assertTrue(s.get_limit(1), 10)

		self.assertEqual(s.get_free_space_for(1), 10)
		self.assertEqual(s.alter(1, 3), 0)
		self.assertEqual(s.get_free_space_for(1), 7)
		self.assertEqual(s.alter(1, -3), 0)
		self.assertEqual(s.get_free_space_for(1), 10)

	def test_total(self, s = TotalStorage(10)):

		self.assertEqual(s.get_limit(), 10)
		self.assertEqual(s.get_limit(1), 10)
		self.assertEqual(s.get_free_space_for(1), 10)
		self.assertEqual(s.get_free_space_for(2), 10)

		self.assertEqual(s.alter(2,  2), 0)

		self.assertEqual(s.get_limit(), 10)
		self.assertEqual(s.get_limit(1), 10)
		self.assertEqual(s.get_free_space_for(1), 8)
		self.assertEqual(s.get_free_space_for(2), 8)

		self.assertEqual(s.alter(2,  10), 2)

		self.assertEqual(s.get_free_space_for(1), 0)
		self.assertEqual(s.get_free_space_for(2), 0)

	def test_positive(self, s = PositiveStorage()):

		self.assertEqual(s.alter(1, -2), -2)
		self.assertEqual(s.alter(1, 2), 0)
		self.assertEqual(s.alter(1, -2), 0)
		self.assertEqual(s.alter(1, -1), -1)

	def test_positive_total(self):
		s = PositiveTotalStorage(10)
		self.test_positive(s)
		self.test_total(s)

	def test_sized_slotted(self):
		s = PositiveSizedSlotStorage(10)

		self.assertEqual(s.alter(1,6), 0)
		self.assertEqual(s.alter(1,6), 2)
		self.assertEqual(s.alter(1, -20), -10)



