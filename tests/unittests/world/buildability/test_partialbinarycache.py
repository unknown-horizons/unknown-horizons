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

from horizons.world.buildability.partialbinarycache import PartialBinaryBuildabilityCache
from horizons.world.buildability.terraincache import TerrainBuildabilityCache
from tests.unittests import TestCase


class MockTerrainBuildabilityCache:
	sizes = TerrainBuildabilityCache.sizes

	def __init__(self, land_or_coast):
		self.land_or_coast = land_or_coast


class TestPartialBinaryBuildabilityCache(TestCase):
	def setUp(self):
		super(TestPartialBinaryBuildabilityCache, self).setUp()
		coords_list = []
		for x in range(10):
			for y in range(10):
				coords_list.append((x, y))
		self.terrain_cache = MockTerrainBuildabilityCache(coords_list)
		self.buildability_cache = PartialBinaryBuildabilityCache(self.terrain_cache)

	def test_horizontal_row2(self):
		bc = self.buildability_cache
		self.assertEqual(bc._row2, set())

		# ..... -> ..#..
		bc.add_area([(2, 1)])
		self.assertEqual(bc._row2, set([(1, 1), (2, 1)]))

		# ..#.. -> ..##.
		bc.add_area([(3, 1)])
		self.assertEqual(bc._row2, set([(1, 1), (2, 1), (3, 1)]))

		# ..##. -> .###.
		bc.add_area([(1, 1)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1), (2, 1), (3, 1)]))

		# .###. -> .#.#.
		bc.remove_area([(2, 1)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1), (2, 1), (3, 1)]))

		# .#.#. -> ...#.
		bc.remove_area([(1, 1)])
		self.assertEqual(bc._row2, set([(2, 1), (3, 1)]))

		# ...#. -> .....
		bc.remove_area([(3, 1)])
		self.assertEqual(bc._row2, set())

	def test_vertical_row2(self):
		bc = self.buildability_cache
		self.assertEqual(bc._row2, set())

		bc.add_area([(1, 1)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1)]))

		bc.add_area([(2, 2)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1), (1, 2), (2, 2)]))

		bc.add_area([(2, 3)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1), (1, 2), (2, 2), (1, 3), (2, 3)]))

		bc.remove_area([(2, 3)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1), (1, 2), (2, 2)]))

		bc.remove_area([(2, 2)])
		self.assertEqual(bc._row2, set([(0, 1), (1, 1)]))

		bc.remove_area([(1, 1)])
		self.assertEqual(bc._row2, set())

	def test_r2x2(self):
		bc = self.buildability_cache
		r2x2 = bc.cache[(2, 2)]
		self.assertEqual(r2x2, set())

		bc.add_area([(1, 1)])
		self.assertEqual(r2x2, set([(0, 0), (0, 1), (1, 0), (1, 1)]))

		bc.add_area([(2, 1)])
		self.assertEqual(r2x2, set([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]))

		bc.add_area([(3, 2)])
		self.assertEqual(r2x2, set([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 1), (3, 2)]))

		bc.remove_area([(2, 1)])
		self.assertEqual(r2x2, set([(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)]))

		bc.remove_area([(3, 2)])
		self.assertEqual(r2x2, set([(0, 0), (0, 1), (1, 0), (1, 1)]))

		bc.remove_area([(1, 1)])
		self.assertEqual(r2x2, set())

	@classmethod
	def _get_coords_set(cls, x, y, width, height):
		res = set()
		for dx in range(width):
			for dy in range(height):
				res.add((x - dx, y - dy))
		return res

	def test_convenience_get_coords_list(self):
		self.assertEqual(self._get_coords_set(1, 1, 2, 1), set([(0, 1), (1, 1)]))
		self.assertEqual(self._get_coords_set(1, 1, 1, 2), set([(1, 0), (1, 1)]))
		self.assertEqual(self._get_coords_set(1, 1, 2, 2), set([(0, 0), (0, 1), (1, 0), (1, 1)]))

	def test_r6x6(self):
		bc = self.buildability_cache
		r6x6 = bc.cache[(6, 6)]
		self.assertEqual(r6x6, set())

		bc.add_area([(7, 7)])
		self.assertEqual(r6x6, self._get_coords_set(7, 7, 6, 6))

		bc.add_area([(8, 7)])
		self.assertEqual(r6x6, self._get_coords_set(7, 7, 6, 6).union(self._get_coords_set(8, 7, 6, 6)))

		bc.add_area([(5, 5)])
		self.assertEqual(r6x6, self._get_coords_set(7, 7, 6, 6).union(self._get_coords_set(8, 7, 6, 6), self._get_coords_set(5, 5, 6, 6)))

		bc.remove_area([(5, 5), (7, 7)])
		self.assertEqual(r6x6, self._get_coords_set(8, 7, 6, 6))

		bc.remove_area([(8, 7)])
		self.assertEqual(r6x6, set())
