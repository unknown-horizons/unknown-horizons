#!/usr/bin/env python

# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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


from unittest import TestCase

from horizons.world.storage import *

class TestGenericStorage(TestCase):

	def test_alter(self):
		s = GenericStorage()
		self.assertEqual(s.alter(1, 5), 0)
		self.assertEqual(s.alter(2, 3), 0)
		self.assertEqual(s[1], 5)
		self.assertEqual(s[2], 3)

		self.assertEqual(s.alter(1, 10), 0)
		self.assertEqual(s[1], 15)

	def test_reset(self):
		s = GenericStorage()
		s.alter(1, 5)
		s.alter(2, 3)
		s.reset(1)
		self.assertEqual(s[1], 0)
		self.assertEqual(s[2], 3)

	def test_reset_all(self):
		s = GenericStorage()
		s.alter(1, 5)
		s.alter(2, 3)
		s.reset_all()
		self.assertEqual(s[1], 0)
		self.assertEqual(s[2], 0)

	def test_limit(self):
		import sys
		s = GenericStorage()
		self.assertEqual(s.get_limit(), sys.maxint)
		self.assertEqual(s.get_limit(1), sys.maxint)

	def test_sum_of_stored_resources(self):
		s = GenericStorage()
		s.alter(1, 5)
		s.alter(2, 3)
		self.assertEqual(s.get_sum_of_stored_resources(), 8)

	def test_get_item(self):
		s = GenericStorage()
		s.alter(1, 5)
		self.assertEqual(s[1], 5)
		self.assertEqual(s[2], 0)


class TestSpecializedStorages(TestCase):

	def test_specialized(self):
		s = SpecializedStorage()

		self.assertEqual(s.alter(1, 3), 3)
		self.assertEqual(s.alter(1, -3), -3)

		self.assertFalse(s.has_resource_slot(1))
		s.add_resource_slot(1)
		self.assertTrue(s.has_resource_slot(1))

		self.assertEqual(s.alter(1, 3), 0)
		self.assertEqual(s.alter(1, -3), 0)

	def test_sized_specialized(self):
		s = SizedSpecializedStorage()

		self.assertEqual(s.alter(1, 3), 3)
		self.assertEqual(s.alter(1, -3), -3)
		self.assertEqual(s.get_limit(1), 0)

		self.assertFalse(s.has_resource_slot(1))
		s.add_resource_slot(1, 10)
		self.assertTrue(s.has_resource_slot(1))
		self.assertEqual(s.get_limit(1), 10)

		self.assertEqual(s.get_free_space_for(1), 10)
		self.assertEqual(s.alter(1, 3), 0)
		self.assertEqual(s.get_free_space_for(1), 7)
		self.assertEqual(s.alter(1, -3), 0)
		self.assertEqual(s.get_free_space_for(1), 10)

		self.assertEqual(s.alter(1, 12), 2)


class TestGlobalLimitStorage(TestCase):

	def test_adjust_limit(self):
		s = GlobalLimitStorage(10)
		self.assertEqual(s.get_limit(), 10)

		s.alter(1, 10)
		self.assertEqual(s[1], 10)
		s.adjust_limit(-5)
		self.assertEqual(s.get_limit(), 5)
		self.assertEqual(s[1], 5)

		s.adjust_limit(-10)
		self.assertEqual(s.get_limit(), 0)


class TestOtherStorages(TestCase):

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

	def test_positive_sized_num_slot(self):
		s = PositiveSizedNumSlotStorage(10, 3)
		self.assertEqual(s.get_limit(), 10)
		self.assertEqual(s.get_limit(1), 10)

		self.assertEqual(s.alter(1, 10), 0)
		self.assertEqual(s.alter(1, 2), 2)

		self.assertEqual(s.alter(2, 0), 0)

		self.assertEqual(s.alter(2, 5), 0)
		self.assertEqual(s.alter(3, 5), 0)

		self.assertEqual(s.alter(4, 1), 1)

