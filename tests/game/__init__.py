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


import os
import shutil
import tempfile
from functools import wraps

import horizons.main
import horizons.world	# needs to be imported before session
from horizons.ai.trader import Trader
from horizons.command.building import Build
from horizons.command.unit import CreateUnit
from horizons.constants import PATHS, GROUND, UNITS, BUILDINGS, GAME_SPEED
from horizons.entities import Entities
from horizons.ext.dummy import Dummy
from horizons.extscheduler import ExtScheduler
from horizons.scheduler import Scheduler
from horizons.spsession import SPSession
from horizons.util import (Color, DbReader, Rect, WorldObject, NamedObject, LivingObject,
						   SavegameAccessor, Point)
from horizons.world import World


db = None

def setup_package():
	"""
	Setup read-only database. This might have to change in the future, tests should not
	fail only because a production now takes 1 second more in the game.
	"""
	global db
	db = horizons.main._create_db()


def create_map():
	"""
	Create a map with a square island (20x20) at position (20, 20) and return the path
	to the database file.
	"""

	# Create island.
	islandfile = tempfile.mkstemp()[1]

	db = DbReader(islandfile)
	db("CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL)")
	db("CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")

	db("BEGIN TRANSACTION")
	tiles = []
	for x, y in Rect.init_from_topleft_and_size(0, 0, 20, 20).tuple_iter():
		if (2 < x < 18) and (2 < y < 18):
			ground = GROUND.DEFAULT_LAND
		else:
			# Add coastline at the borders.
			ground = 49
		tiles.append((x, y, ground))
	db.execute_many("INSERT INTO ground VALUES(?, ?, ?)", tiles)
	db("COMMIT")

	# Create savegame with the island above.
	savegame = tempfile.mkstemp()[1]
	shutil.copyfile(PATHS.SAVEGAME_TEMPLATE, savegame)

	db = DbReader(savegame)
	db("BEGIN TRANSACTION")
	db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", 20, 20, islandfile)
	db("COMMIT")

	return (savegame, islandfile)


class SPTestSession(SPSession):

	def __init__(self, db, rng_seed=None):
		"""
		Unfortunately, right now there is no other way to setup Dummy versions of the GUI,
		View etc., unless we want to patch the references in the session module.
		"""
		super(LivingObject, self).__init__()
		self.gui = Dummy()
		self.db = db
		self.savecounter = 0	# this is a new game.
		self.is_alive = True

		WorldObject.reset()
		NamedObject.reset()

		# Game
		self.current_tick = 0
		self.random = self.create_rng(rng_seed)
		self.timer = self.create_timer()
		Scheduler.create_instance(self.timer)
		ExtScheduler.create_instance(Dummy)
		self.manager = self.create_manager()
		self.view = Dummy()
		self.view.renderer = Dummy()
		Entities.load(self.db)
		self.scenario_eventhandler = Dummy()
		self.campaign = {}

		# GUI
		self.gui.session = self
		self.ingame_gui = Dummy()

		GAME_SPEED.TICKS_PER_SECOND = 16

	def load(self, db_files, players):
		"""
		Stripped version of the original code. We don't need to load selections,
		or a scenario, setting up the gui or view.
		"""
		self.db_files = db_files	# keep the paths to the databases, so we can clean up
		savegame_db = SavegameAccessor(db_files[0])

		self.world = World(self)
		self.world._init(savegame_db)
		for i in sorted(players):
			self.world.setup_player(i['id'], i['name'], i['color'], i['local'])
		self.manager.load(savegame_db)

	def end(self):
		"""
		Clean up temporary files.
		"""
		super(SPTestSession, self).end()
		for f in self.db_files:
			os.remove(f)

	def run(self, ticks=1, seconds=None):
		"""
		Run the scheduler the given count of ticks or (in-game) seconds. Default is 1 tick,
		if seconds are passed, they will overwrite the tick count.
		"""
		if seconds:
			ticks = self.timer.get_ticks(seconds)

		for i in range(ticks):
			Scheduler().tick(self.current_tick)
			self.current_tick += 1


def new_session(mapgen=create_map, rng_seed=None):
	"""
	Create a new session with a map, add one human player and a trader (it will crash
	otherwise). It returns both session and player to avoid making the function-baed
	tests too verbose.
	"""
	session = SPTestSession(horizons.main.db, rng_seed=rng_seed)
	players = [{'id': 1, 'name': 'foobar', 'color': Color[1], 'local': True}]

	session.load(create_map(), players)
	session.world.trader = Trader(session, 99999, 'Free Trader', Color())

	return session, session.world.player


def new_settlement(session, pos=Point(30, 20)):
	"""
	Creates a settlement at the given position. It returns the settlement and the island
	where it was created on, to avoid making function-baed tests too verbose.
	"""
	island = session.world.get_island(pos)
	assert island, "No island found at %s" % pos
	player = session.world.player

	ship = CreateUnit(player.worldid, UNITS.PLAYER_SHIP_CLASS, pos.x, pos.y)(player)
	for res, amount in session.db("SELECT resource, amount FROM start_resources"):
		ship.inventory.alter(res, amount)

	building = Build(BUILDINGS.BRANCH_OFFICE_CLASS, pos.x, pos.y, island, ship=ship)(player)
	assert building, "Could not build branch office at %s" % pos

	return (player.settlements[0], island)


def game_test(func):
	"""
	Decorator that is needed for each test in this package. setup/teardown of function
	based tests can't pass arguments to the test, or keep a reference somewhere.
	If a test fails, we need to reset the session under all circumstances, otherwise we
	break the rest of the tests. The global database reference has to be set each time too,
	unittests use this too, and we can't predict the order tests run (we should not rely
	on it anyway).
	"""
	@wraps(func)
	def wrapped():
		horizons.main.db = db
		s, p = new_session()
		try:
			return func(s, p)
		finally:
			s.end()
	return wrapped
game_test.__test__ = False
