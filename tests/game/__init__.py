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

import contextlib
import inspect
import os
from functools import wraps

import mock

import horizons.main
import horizons.world	# needs to be imported before session
from horizons.ai.aiplayer import AIPlayer
from horizons.command.unit import CreateUnit
from horizons.constants import UNITS
from horizons.ext.dummy import Dummy
from horizons.extscheduler import ExtScheduler
from horizons.scheduler import Scheduler
from horizons.spsession import SPSession
from horizons.util import Color, DbReader, SavegameAccessor, DifficultySettings, WorldObject
from horizons.component.storagecomponent import StorageComponent

from tests import RANDOM_SEED
from tests.utils import Timer

# path where test savegames are stored (tests/game/fixtures/)
TEST_FIXTURES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures')


db = None

def setup_package():
	"""
	Setup read-only database. This might have to change in the future, tests should not
	fail only because a production now takes 1 second more in the game.
	"""
	global db
	db = horizons.main._create_main_db()


@contextlib.contextmanager
def _dbreader_convert_dummy_objects():
	"""
	Wrapper around DbReader.__call__ to convert Dummy objects to valid values.

	This is needed because some classes attempt to store Dummy objects in the
	database, e.g. ConcreteObject with self._instance.getActionRuntime().
	We fix this by replacing it with zero, SQLite doesn't care much about types,
	and hopefully a number is less likely to break code than None.

	Yes, this is ugly and will most likely break later. For now, it works.
	"""
	def deco(func):
		@wraps(func)
		def wrapper(self, command, *args):
			args = list(args)
			for i in range(len(args)):
				if args[i].__class__.__name__ == 'Dummy':
					args[i] = 0
			return func(self, command, *args)
		return wrapper

	original = DbReader.__call__
	DbReader.__call__ = deco(DbReader.__call__)
	yield
	DbReader.__call__ = original


class SPTestSession(SPSession):

	@mock.patch('horizons.session.View', Dummy)
	def __init__(self, rng_seed=None):
		ExtScheduler.create_instance(Dummy)
		super(SPTestSession, self).__init__(Dummy, horizons.main.db, rng_seed)
		self.reset_autosave = mock.Mock()

	def save(self, *args, **kwargs):
		"""
		Wrapper around original save function to fix some things.
		"""
		# SavegameManager.write_metadata tries to create a screenshot and breaks when
		# accessing fife properties
		with mock.patch('horizons.session.SavegameManager'):
			# We need to covert Dummy() objects to a sensible value that can be stored
			# in the database
			with _dbreader_convert_dummy_objects():
				return super(SPTestSession, self).save(*args, **kwargs)

	def load(self, savegame, players):
		# keep a reference on the savegame, so we can cleanup in `end`
		self.savegame = savegame
		super(SPTestSession, self).load(savegame, players, False, False, 0)

	def end(self, keep_map=False, remove_savegame=True):
		"""
		Clean up temporary files.
		"""
		super(SPTestSession, self).end()

		# Find all islands in the map first
		savegame_db = SavegameAccessor(self.savegame)
		if not keep_map:
			for (island_file, ) in savegame_db('SELECT file FROM island'):
				if not island_file.startswith('random:'): # random islands don't exist as files
					os.remove(island_file)

		# Finally remove savegame
		savegame_db.close()
		if remove_savegame:
			os.remove(self.savegame)

	@classmethod
	def cleanup(cls):
		"""
		If a test uses manual session management, we cannot be sure that session.end was
		called before a crash, leaving the game in an unclean state. This method should
		return the game to a valid state.
		"""
		Scheduler.destroy_instance()
		ExtScheduler.destroy_instance()
		WorldObject.reset()

	def run(self, ticks=1, seconds=None):
		"""
		Run the scheduler the given count of ticks or (in-game) seconds. Default is 1 tick,
		if seconds are passed, they will overwrite the tick count.
		"""
		if seconds:
			ticks = self.timer.get_ticks(seconds)

		for i in range(ticks):
			Scheduler().tick( Scheduler().cur_tick + 1 )


# import helper functions here, so tests can import from tests.game directly
from tests.game.utils import create_map, new_settlement, settle


def new_session(mapgen=create_map, rng_seed=RANDOM_SEED, human_player = True, ai_players = 0):
	"""
	Create a new session with a map, add one human player and a trader (it will crash
	otherwise). It returns both session and player to avoid making the function-baed
	tests too verbose.
	"""
	session = SPTestSession(rng_seed=rng_seed)
	human_difficulty = DifficultySettings.DEFAULT_LEVEL
	ai_difficulty = DifficultySettings.EASY_LEVEL

	players = []
	if human_player:
		players.append({'id': 1, 'name': 'foobar', 'color': Color[1], 'local': True, 'ai': False, 'difficulty': human_difficulty})
	for i in xrange(ai_players):
		id = i + human_player + 1
		players.append({'id': id, 'name': ('AI' + str(i)), 'color': Color[id], 'local': id == 1, 'ai': True, 'difficulty': ai_difficulty})

	session.load(mapgen(), players)

	if ai_players > 0: # currently only ai tests use the ships
		for player in session.world.players:
			point = session.world.get_random_possible_ship_position()
			ship = CreateUnit(player.worldid, UNITS.PLAYER_SHIP, point.x, point.y)(issuer=player)
			# give ship basic resources
			for res, amount in session.db("SELECT resource, amount FROM start_resources"):
				ship.get_component(StorageComponent).inventory.alter(res, amount)
		AIPlayer.load_abstract_buildings(session.db)

	return session, session.world.player


def load_session(savegame, rng_seed=RANDOM_SEED):
	"""
	Start a new session with the given savegame.
	"""
	session = SPTestSession(rng_seed=rng_seed)

	session.load(savegame, [])

	return session


def game_test(*args, **kwargs):
	"""
	Decorator that is needed for each test in this package. setup/teardown of function
	based tests can't pass arguments to the test, or keep a reference somewhere.
	If a test fails, we need to reset the session under all circumstances, otherwise we
	break the rest of the tests. The global database reference has to be set each time too,
	unittests use this too, and we can't predict the order tests run (we should not rely
	on it anyway).

	The decorator can be used in 2 ways:

		1. No decorator arguments

			@game_test
			def foo(session, player):
				pass

		2. Pass extra arguments (timeout, different map generator)

			@game_test(timeout=10, mapgen=my_map_generator)
			def foo(session, player):
				pass
	"""
	no_decorator_arguments = len(args) == 1 and not kwargs and inspect.isfunction(args[0])

	timeout = kwargs.get('timeout', 15 * 60)	# zero means no timeout, 15min default
	mapgen = kwargs.get('mapgen', create_map)
	human_player = kwargs.get('human_player', True)
	ai_players = kwargs.get('ai_players', 0)
	manual_session = kwargs.get('manual_session', False)
	use_fixture = kwargs.get('use_fixture', False)

	def handler(signum, frame):
		raise Exception('Test run exceeded %ds time limit' % timeout)

	def deco(func):
		@wraps(func)
		def wrapped(*args):
			horizons.main.db = db
			if not manual_session and not use_fixture:
				s, p = new_session(mapgen = mapgen, human_player = human_player, ai_players = ai_players)
			elif use_fixture:
				path = os.path.join(TEST_FIXTURES_DIR, use_fixture + '.sqlite')
				if not os.path.exists(path):
					raise Exception('Savegame %s not found' % path)
				s = load_session(path)

			timelimit = Timer(handler)
			timelimit.start(timeout)

			try:
				if use_fixture:
					return func(s, *args)
				elif not manual_session:
					return func(s, p, *args)
				else:
					return func(*args)
			finally:
				try:
					if use_fixture:
						s.end(remove_savegame=False, keep_map=True)
					elif not manual_session:
						s.end()
				except:
					pass
					# An error happened after cleanup after an error.
					# This is ok since cleanup is only defined to work when invariants are in place,
					# but the first error could have violated one.
					# Therefore only use failsafe cleanup:
				finally:
					SPTestSession.cleanup()


				timelimit.stop()
		return wrapped

	if no_decorator_arguments:
		# return the wrapped function
		return deco(args[0])
	else:
		# return a decorator
		return deco

game_test.__test__ = False


def set_trace():
	"""
	Use this function instead of directly importing if from pdb. The test run
	time limit will be disabled and stdout restored (so the debugger actually
	works).
	"""
	Timer.stop()

	from nose.tools import set_trace
	set_trace()


_multiprocess_can_split_ = True
