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


from itertools import product

from horizons.command.building import Build

from tests.game import game_test, settle


WEAVER = 7
PASTURE = 18
POTATO_FIELD = 19
FARM = 20
SUGAR_FIELD = 22
DISTILLERY = 26


def _build_farm(x, y, field_type, island, settlement, owner):
	"""
	Build a farm at (x, y) and 4 fields of field_type.

	F   F
	  X		  (X - farm, F - field)
	F   F
	"""
	farm = Build(FARM, x, y, island, settlement=settlement)(owner)
	assert farm, "Failed to build a farm at (%d, %d)" % (x, y)

	for (x_off, y_off) in product([-3, 3], repeat=2):
		fx = x + x_off
		fy = x + y_off
		field = Build(field_type, fx, fy, island, settlement=settlement)(owner)
		assert field, "Failed to build a field (%d) at (%d, %d)" % (field_type, x, y)

	return farm


@game_test
def test_weaver(s, p):
	"""
	A weaver produces textiles from wool. A pasture provides lamb wool for a farm,
	which it converts to wool for the weaver.
	"""
	settlement, island = settle(s)

	_build_farm(30, 30, PASTURE, island, settlement, p)

	weaver = Build(WEAVER, 27, 30, island, settlement=settlement)(p)
	assert weaver
	assert weaver.inventory[3] == 0	# textile

	s.run(seconds=60)	# pasture 30s, farm 1s, weaver 12s

	assert weaver.inventory[3]


@game_test
def test_distillery(s, p):
	"""
	Distillery produces liquor out of sugar. A farm will collect raw sugar from a
	sugar field and produce sugar.
	"""
	settlement, island = settle(s)

	_build_farm(30, 30, SUGAR_FIELD, island, settlement, p)

	distillery = Build(DISTILLERY, 27, 30, island, settlement=settlement)(p)
	assert distillery
	assert distillery.inventory[22] == 0	# liquor

	s.run(seconds=60)	# sugarfield 30s, farm 1s, distillery 12s

	assert distillery.inventory[22]


@game_test
def test_potato_field(s, p):
	"""
	A farm collects potatoes from the field and produces food.
	"""
	settlement, island = settle(s)

	farm = _build_farm(30, 30, POTATO_FIELD, island, settlement, p)
	assert farm.inventory[5] == 0	# food
	assert farm.inventory[15] == 0	# potatoes

	s.run(seconds=60)	# potato field 26s, farm 1s

	assert farm.inventory[5]
