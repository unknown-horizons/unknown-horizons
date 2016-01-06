# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from horizons.util.color import Color
from tests.unittests import TestCase


class TestColor(TestCase):

	def setUp(self):
		super(TestColor, self).setUp()

		self.db.execute_many(
			"INSERT INTO colors VALUES(?, ?, ?, ?, ?, ?)",
			[('black', 0, 0, 0, 255, 1),
			 ('red', 255, 0, 0, 255, 2)]
		)

	def test_iter(self):
		colors = list(Color)
		self.assertEqual(len(colors), 2)
		self.assertTrue(all(c.is_default_color for c in colors))
		self.assertEqual(colors[0], Color(0, 0, 0, 255))
		self.assertEqual(colors[1], Color(255, 0, 0, 255))

	def test_default_color(self):
		self.assertTrue(Color(0, 0, 0, 255).is_default_color)
		self.assertFalse(Color(1, 2, 3, 255).is_default_color)

	def test_comparison(self):
		self.assertEqual(Color(0, 0, 0, 255), Color(0, 0, 0, 255))
		self.assertNotEqual(Color(0, 0, 0, 255), Color(1, 2, 3, 255))

	def test_indexing(self):
		self.assertEqual(Color[1], Color(0, 0, 0, 255))
		self.assertEqual(Color['black'], Color(0, 0, 0, 255))
