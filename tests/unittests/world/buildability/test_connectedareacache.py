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

from horizons.world.buildability.connectedareacache import ConnectedAreaCache
from tests.unittests import TestCase


class TestConnectedAreaCache(TestCase):
	def test(self):
		cache = ConnectedAreaCache()
		self.assertEqual(0, len(cache.areas))

		cache.add_area([(0, 0), (1, 1)])
		self.assertEqual(2, len(cache.areas))
		self.assertEqual(set([(0, 0)]), cache.areas[cache.area_numbers[(0, 0)]])
		self.assertEqual(set([(1, 1)]), cache.areas[cache.area_numbers[(1, 1)]])

		cache.add_area([(1, 4), (1, 3), (1, 2)])
		self.assertEqual(2, len(cache.areas))
		self.assertEqual(set([(0, 0)]), cache.areas[cache.area_numbers[(0, 0)]])
		self.assertEqual(set([(1, 1), (1, 2), (1, 3), (1, 4)]), cache.areas[cache.area_numbers[(1, 1)]])

		cache.add_area([(0, 1)])
		self.assertEqual(1, len(cache.areas))
		self.assertEqual(set([(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (1, 4)]), cache.areas[cache.area_numbers[(0, 0)]])

		cache.remove_area([(0, 1)])
		self.assertEqual(2, len(cache.areas))
		self.assertEqual(set([(0, 0)]), cache.areas[cache.area_numbers[(0, 0)]])
		self.assertEqual(set([(1, 1), (1, 2), (1, 3), (1, 4)]), cache.areas[cache.area_numbers[(1, 1)]])

		cache.remove_area([(0, 0)])
		self.assertFalse((0, 0) in cache.area_numbers)
		self.assertEqual(1, len(cache.areas))
		self.assertEqual(set([(1, 1), (1, 2), (1, 3), (1, 4)]), cache.areas[cache.area_numbers[(1, 1)]])

		cache.remove_area([(1, 2), (1, 3)])
		self.assertEqual(2, len(cache.areas))
		self.assertEqual(set([(1, 1)]), cache.areas[cache.area_numbers[(1, 1)]])
		self.assertEqual(set([(1, 4)]), cache.areas[cache.area_numbers[(1, 4)]])

		cache.remove_area([(1, 1), (1, 4)])
		self.assertEqual(0, len(cache.areas))
