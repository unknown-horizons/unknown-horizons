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

from textwrap import dedent

import pytest

from horizons.util.shapes import Point
from horizons.util.tile_orientation import get_tile_alignment_action


def make_tiles(tiles):
	"""
	Parse the string specification for 9 tiles and returns a 2-dimensional array and a
	function to access tiles with `Point` instances.
	"""
	lines = dedent(tiles).strip().splitlines()
	tiles = [l.split(' ') for l in lines]

	def accessor(point):
		tile = tiles[point.y + 1][point.x + 1]
		return tile.lower() == 'x'

	return tiles, accessor


@pytest.mark.parametrize('expected,tiles', [
	('single', '''
		_ _ _
		_ . _
		_ _ _
	'''),
	('d', '''
		_ _ _
		x . _
		_ _ _
	'''),
	('bd', '''
		_ _ _
		x . x
		_ _ _
	'''),
	('bd', '''
		x _ _
		x . x
		_ _ x
	'''),
	('abdh', '''
		x x _
		x . x
		_ _ _
	'''),
	('single', '''
		x _ _
		_ . _
		_ _ x
	'''),
	('ac', '''
		_ x _
		_ . _
		_ x _
	'''),
	('abcd', '''
		_ x _
		x . x
		_ x _
	'''),
	('abcdeg', '''
		_ x x
		x . x
		x x _
	'''),
	('abcdefgh', '''
		x x x
		x . x
		x x x
	''')

])
def test_get_tile_alignment_action(expected, tiles):
	"""Tests for the road/wall orientation code.

	Basically `get_tile_alignment_action` returns the sorted list of fields that the tile in
	position . should connect.


	Tile names:

		h a e
		d . b
		g c f
	"""
	tiles, accessor = make_tiles(tiles)
	aligned = get_tile_alignment_action(Point(0, 0), accessor)
	assert aligned == expected
