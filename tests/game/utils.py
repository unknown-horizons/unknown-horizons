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

"""Some helper functions to use in game tests.
Do not import from here, import directly from tests.game.
"""

import os
import tempfile

from horizons.command.building import Build
from horizons.command.unit import CreateUnit
from horizons.constants import GROUND, BUILDINGS, UNITS, RES
from horizons.util import Rect, DbReader, Point
from horizons.util.uhdbaccessor import read_savegame_template
from horizons.component.storagecomponent import StorageComponent


def create_map():
	"""
	Create a map with a square island (20x20) at position (20, 20) and return the path
	to the database file.
	"""

	# Create island.
	fd, islandfile = tempfile.mkstemp()
	os.close(fd)

	db = DbReader(islandfile)
	db("CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL, action_id TEXT NOT NULL, rotation INTEGER NOT NULL)")
	db("CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")

	db("BEGIN TRANSACTION")
	tiles = []
	for x, y in Rect.init_from_topleft_and_size(0, 0, 20, 20).tuple_iter():
		if (0 < x < 20) and (0 < y < 20):
			ground = GROUND.DEFAULT_LAND
		else:
			# Add coastline at the borders.
			ground = GROUND.SHALLOW_WATER
		tiles.append([x, y] + list(ground))
	db.execute_many("INSERT INTO ground VALUES(?, ?, ?, ?, ?)", tiles)
	db("COMMIT")

	# Create savegame with the island above.
	fd, savegame = tempfile.mkstemp()
	os.close(fd)

	db = DbReader(savegame)
	read_savegame_template(db)
	db("BEGIN TRANSACTION")
	db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", 20, 20, islandfile)
	db("COMMIT")

	return savegame


def new_settlement(session, pos=Point(30, 20)):
	"""
	Creates a settlement at the given position. It returns the settlement and the island
	where it was created on, to avoid making function-baed tests too verbose.
	"""
	island = session.world.get_island(pos)
	assert island, "No island found at %s" % pos
	player = session.world.player

	ship = CreateUnit(player.worldid, UNITS.PLAYER_SHIP, pos.x, pos.y)(player)
	for res, amount in session.db("SELECT resource, amount FROM start_resources"):
		ship.get_component(StorageComponent).inventory.alter(res, amount)

	building = Build(BUILDINGS.WAREHOUSE, pos.x, pos.y, island, ship=ship)(player)
	assert building, "Could not build warehouse at %s" % pos

	return (building.settlement, island)


def settle(s):
	"""
	Create a new settlement, start with some resources.
	"""
	settlement, island = new_settlement(s)
	settlement.get_component(StorageComponent).inventory.alter(RES.GOLD, 5000)
	settlement.get_component(StorageComponent).inventory.alter(RES.BOARDS, 50)
	settlement.get_component(StorageComponent).inventory.alter(RES.TOOLS, 50)
	settlement.get_component(StorageComponent).inventory.alter(RES.BRICKS, 50)
	return settlement, island
