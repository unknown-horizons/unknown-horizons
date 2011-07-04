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
from horizons.command.unit import CreateUnit
from horizons.constants import BUILDINGS, UNITS, RES

from tests.game import game_test, settle


@game_test
def test_lumberjack(s, p):
	"""
	Lumberjack will produce boards out of wood, collected from nearby trees.
	"""
	settlement, island = settle(s)

	jack = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(p)
	assert jack

	assert jack.inventory[RES.BOARDS_ID] == 0
	assert jack.inventory[RES.WOOD_ID] == 0

	for (x_off, y_off) in product([-2, 2], repeat=2):
		x = 30 + x_off
		y = 30 + y_off
		tree = Build(BUILDINGS.TREE_CLASS, x, y, island, settlement=settlement)(p)
		assert tree
		tree.finish_production_now()

	s.run(seconds=20)

	assert jack.inventory[RES.BOARDS_ID]


@game_test
def test_hunter(s, p):
	"""
	Hunter will produce food from dear meat. No animals were harmed in this test.
	"""
	settlement, island = settle(s)

	hunter = Build(BUILDINGS.HUNTER_CLASS, 30, 30, island, settlement=settlement)(p)
	assert hunter

	assert hunter.inventory[RES.FOOD_ID] == 0
	assert hunter.inventory[RES.DEAR_MEAT_ID] == 0

	for (x_off, y_off) in product([-5, -4, 4, 5], repeat=2):
		x = 30 + x_off
		y = 30 + y_off
		animal = CreateUnit(island.worldid, UNITS.WILD_ANIMAL_CLASS, x, y)(None)
		# wild animals are slow eaters, we feed them directly
		animal.inventory.alter(12, 10)
		animal.finish_production_now()
		assert animal

	s.run(seconds=30)

	assert hunter.inventory[RES.FOOD_ID]


@game_test
def test_fisherman(s, p):
	"""
	A fisherman produces food out of fish, collecting in nearby fish deposits.
	"""
	settlement, island = settle(s)

	for x in (25, 30, 35):
		school = Build(BUILDINGS.FISH_DEPOSIT_CLASS, x, 18, s.world, ownerless=True)(None)
		assert school
		school.finish_production_now()

	fisherman = Build(BUILDINGS.FISHERMAN_CLASS, 25, 20, island, settlement=settlement)(p)
	assert fisherman

	assert fisherman.inventory[RES.FOOD_ID] == 0
	assert fisherman.inventory[RES.FISH_ID] == 0

	s.run(seconds=20)

	assert fisherman.inventory[RES.FOOD_ID]


@game_test
def test_brick_production_chain(s, p):
	"""
	A brickyard makes bricks from clay. Clay is collected by a clay pit on a deposit.
	"""
	settlement, island = settle(s)

	assert Build(BUILDINGS.CLAY_DEPOSIT_CLASS, 30, 30, island, ownerless=True)(None)
	assert Build(BUILDINGS.CLAY_PIT_CLASS, 30, 30, island, settlement=settlement)(p)

	brickyard = Build(BUILDINGS.BRICKYARD_CLASS, 30, 25, island, settlement=settlement)(p)
	assert brickyard.inventory[RES.BRICKS_ID] == 0
	assert brickyard.inventory[RES.CLAY_ID] == 0

	s.run(seconds=60) # 15s clay pit, 15s brickyard

	assert brickyard.inventory[RES.BRICKS_ID]


@game_test
def test_tool_production_chain(s, p):
	"""
	Check if a iron mine gathers raw iron, a smeltery produces iron ingots, boards are converted
	to charcoal and tools are produced.

	Pretty much for a single test, but these are rather trivial in their assertions anyway.
	"""
	settlement, island = settle(s)

	assert Build(BUILDINGS.MOUNTAIN_CLASS, 30, 35, island, ownerless=True)(None)
	assert Build(BUILDINGS.IRON_MINE_CLASS, 30, 35, island, settlement=settlement)(p)

	charcoal = Build(BUILDINGS.CHARCOAL_BURNER_CLASS, 25, 35, island, settlement=settlement)(p)
	assert charcoal
	charcoal.inventory.alter(RES.BOARDS_ID, 10) # give him boards directly

	assert Build(BUILDINGS.SMELTERY_CLASS, 25, 30, island, settlement=settlement)(p)

	toolmaker = Build(BUILDINGS.TOOLMAKER_CLASS, 22, 32, island, settlement=settlement)(p)
	assert toolmaker
	toolmaker.inventory.alter(RES.BOARDS_ID, 10) # give him boards directly

	assert toolmaker.inventory[RES.TOOLS_ID] == 0
	s.run(seconds=120)
	assert toolmaker.inventory[RES.TOOLS_ID]
