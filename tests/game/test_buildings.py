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


from itertools import product

from horizons.command.building import Build, Tear
from horizons.util.worldobject import WorldObject, WorldObjectNotFound
from horizons.command.unit import CreateUnit
from horizons.constants import BUILDINGS, UNITS, RES
from horizons.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer

from tests.game import game_test, settle


@game_test
def test_lumberjack(s, p):
	"""
	Lumberjack will produce boards out of wood, collected from nearby trees.
	"""
	settlement, island = settle(s)

	jack = Build(BUILDINGS.LUMBERJACK, 30, 30, island, settlement=settlement)(p)
	assert jack

	assert jack.get_component(StorageComponent).inventory[RES.BOARDS] == 0
	assert jack.get_component(StorageComponent).inventory[RES.TREES] == 0

	for (x_off, y_off) in product([-2, 2], repeat=2):
		x = 30 + x_off
		y = 30 + y_off
		tree = Build(BUILDINGS.TREE, x, y, island, settlement=settlement)(p)
		assert tree
		tree.get_component(Producer).finish_production_now()

	s.run(seconds=20)

	assert jack.get_component(StorageComponent).inventory[RES.BOARDS]


@game_test
def test_hunter(s, p):
	"""
	Hunter will produce food from dear meat. No animals were harmed in this test.
	"""
	settlement, island = settle(s)

	hunter = Build(BUILDINGS.HUNTER, 30, 30, island, settlement=settlement)(p)
	assert hunter

	assert hunter.get_component(StorageComponent).inventory[RES.FOOD] == 0
	assert hunter.get_component(StorageComponent).inventory[RES.DEER_MEAT] == 0

	for (x_off, y_off) in product([-5, -4, 4, 5], repeat=2):
		x = 30 + x_off
		y = 30 + y_off
		animal = CreateUnit(island.worldid, UNITS.WILD_ANIMAL, x, y)(None)
		# wild animals are slow eaters, we feed them directly
		animal.get_component(StorageComponent).inventory.alter(12, 10)
		animal.get_component(Producer).finish_production_now()
		assert animal

	s.run(seconds=30)

	assert hunter.get_component(StorageComponent).inventory[RES.FOOD]


@game_test
def test_fisherman(s, p):
	"""
	A fisherman produces food out of fish, collecting in nearby fish deposits.
	"""
	settlement, island = settle(s)

	for x in (25, 30, 35):
		school = Build(BUILDINGS.FISH_DEPOSIT, x, 18, s.world, ownerless=True)(None)
		assert school
		school.get_component(Producer).finish_production_now()

	fisherman = Build(BUILDINGS.FISHER, 25, 20, island, settlement=settlement)(p)
	assert fisherman

	assert fisherman.get_component(StorageComponent).inventory[RES.FOOD] == 0
	assert fisherman.get_component(StorageComponent).inventory[RES.FISH] == 0

	s.run(seconds=20)

	assert fisherman.get_component(StorageComponent).inventory[RES.FOOD]


@game_test
def test_brick_production_chain(s, p):
	"""
	A brickyard makes bricks from clay. Clay is collected by a clay pit on a deposit.
	"""
	settlement, island = settle(s)

	assert Build(BUILDINGS.CLAY_DEPOSIT, 30, 30, island, ownerless=True)(None)
	assert Build(BUILDINGS.CLAY_PIT, 30, 30, island, settlement=settlement)(p)

	brickyard = Build(BUILDINGS.BRICKYARD, 30, 25, island, settlement=settlement)(p)
	assert brickyard.get_component(StorageComponent).inventory[RES.BRICKS] == 0
	assert brickyard.get_component(StorageComponent).inventory[RES.CLAY] == 0

	s.run(seconds=60) # 15s clay pit, 15s brickyard

	assert brickyard.get_component(StorageComponent).inventory[RES.BRICKS]


@game_test
def test_tool_production_chain(s, p):
	"""
	Check if a iron mine gathers raw iron, a smeltery produces iron ingots, boards are converted
	to charcoal and tools are produced.

	Pretty much for a single test, but these are rather trivial in their assertions anyway.
	"""
	settlement, island = settle(s)

	assert Build(BUILDINGS.MOUNTAIN, 30, 35, island, ownerless=True)(None)
	assert Build(BUILDINGS.IRON_MINE, 30, 35, island, settlement=settlement)(p)

	charcoal = Build(BUILDINGS.CHARCOAL_BURNER, 25, 35, island, settlement=settlement)(p)
	assert charcoal
	charcoal.get_component(StorageComponent).inventory.alter(RES.BOARDS, 10) # give him boards directly

	assert Build(BUILDINGS.SMELTERY, 25, 30, island, settlement=settlement)(p)

	toolmaker = Build(BUILDINGS.TOOLMAKER, 22, 32, island, settlement=settlement)(p)
	assert toolmaker
	toolmaker.get_component(StorageComponent).inventory.alter(RES.BOARDS, 10) # give him boards directly

	assert toolmaker.get_component(StorageComponent).inventory[RES.TOOLS] == 0
	s.run(seconds=120)
	assert toolmaker.get_component(StorageComponent).inventory[RES.TOOLS]

@game_test
def test_build_tear(s, p):
	"""
	Build stuff and tear it later
	"""
	settlement, island = settle(s)
	tree = Build(BUILDINGS.TREE, 30, 35, island, settlement=settlement)(p)

	s.run(seconds=1)

	wid = tree.worldid
	Tear(tree)(p)

	try:
		WorldObject.get_object_by_id(wid)
	except WorldObjectNotFound:
		pass # should be gone
	else:
		assert False


@game_test(timeout=60)
def test_tree_production(s, p):
	"""Check whether trees produce wood"""
	settlement, island = settle(s)
	tree = Build(BUILDINGS.TREE, 30, 35, island, settlement=settlement)(p)

	n = 20

	inv = tree.get_component(StorageComponent).inventory
	for i in xrange(n):  # we want n units

		while not inv[RES.TREES]:
			s.run(seconds=5)

		# take one away to free storage space
		#from tests import set_trace ; set_trace()
		inv.alter(RES.TREES, -1)

	# here, n tons of wood have been produced

