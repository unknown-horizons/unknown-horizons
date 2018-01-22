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

from horizons.util.color import Color


@pytest.fixture(autouse=True)
def colors(db):
	db.execute_many(
		"INSERT INTO colors VALUES(?, ?, ?, ?, ?, ?)",
		[('black', 0, 0, 0, 255, 1),
		 ('red', 255, 0, 0, 255, 2)]
	)


def test_iter():
	colors = list(Color.get_defaults())
	assert len(colors) == 2
	assert all(c.is_default_color for c in colors)
	assert colors[0] == Color(0, 0, 0, 255)
	assert colors[1] == Color(255, 0, 0, 255)


def test_default_color():
	assert Color(0, 0, 0, 255).is_default_color
	assert not Color(1, 2, 3, 255).is_default_color


def test_comparison():
	assert Color(0, 0, 0, 255) == Color(0, 0, 0, 255)
	assert Color(0, 0, 0, 255) != Color(1, 2, 3, 255)


def test_indexing():
	assert Color.get(1) == Color(0, 0, 0, 255)
	assert Color.get('black') == Color(0, 0, 0, 255)
