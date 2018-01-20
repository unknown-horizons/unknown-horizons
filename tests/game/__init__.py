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

import contextlib
import os
import tempfile
from functools import wraps
from unittest import mock

import horizons.globals
import horizons.main
import horizons.world  # needs to be imported before session
from horizons.extscheduler import ExtScheduler
from horizons.scheduler import Scheduler
from horizons.spsession import SPSession
from horizons.util.color import Color
from horizons.util.dbreader import DbReader
from horizons.util.difficultysettings import DifficultySettings
from horizons.util.savegameaccessor import SavegameAccessor
from horizons.util.startgameoptions import StartGameOptions
from tests import RANDOM_SEED
from tests.dummy import Dummy
from tests.utils import Timer

# path where test savegames are stored (tests/game/fixtures/)
TEST_FIXTURES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures')


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
			mapped_args = [
				arg if arg.__class__.__name__ != 'Dummy' else 0
				for arg in args
			]
			return func(self, command, *mapped_args)
		return wrapper

	original = DbReader.__call__
	DbReader.__call__ = deco(DbReader.__call__)
	yield
	DbReader.__call__ = original


class SPTestSession(SPSession):

	@mock.patch('horizons.session.View', Dummy)
	def __init__(self, rng_seed=None):
		ExtScheduler.create_instance(mock.Mock())
		super().__init__(horizons.globals.db, rng_seed, ingame_gui_class=Dummy)
		self.reset_autosave = mock.Mock()

	def save(self, *args, **kwargs):
		"""
		Wrapper around original save function to fix some things.
		"""
		# SavegameManager._write_screenshot tries to create a screenshot and breaks when
		# accessing fife properties
		with mock.patch('horizons.session.SavegameManager._write_screenshot'):
			# We need to covert Dummy() objects to a sensible value that can be stored
			# in the database
			with _dbreader_convert_dummy_objects():
				return super().save(*args, **kwargs)

	def load(self, savegame, players, is_ai_test, is_map):
		# keep a reference on the savegame, so we can cleanup in `end`
		self.savegame = savegame
		self.started_from_map = is_map
		if is_ai_test:
			# enable trader, pirate and natural resources in AI tests.
			options = StartGameOptions.create_ai_test(savegame, players)
		else:
			# disable the above in usual game tests for simplicity.
			options = StartGameOptions.create_game_test(savegame, players)
			options.is_map = is_map
		super().load(options)

	def end(self, keep_map=False, remove_savegame=True):
		"""
		Clean up temporary files.
		"""
		super().end()

		# remove the saved game
		savegame_db = SavegameAccessor(self.savegame, self.started_from_map)
		savegame_db.close()
		if remove_savegame and not self.started_from_map:
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
		SPSession._clear_caches()

	def run(self, ticks=1, seconds=None):
		"""
		Run the scheduler the given count of ticks or (in-game) seconds. Default is 1 tick,
		if seconds are passed, they will overwrite the tick count.
		"""
		if seconds:
			ticks = self.timer.get_ticks(seconds)

		while ticks > 0:
			Scheduler().tick(Scheduler().cur_tick + 1)
			ticks -= 1


# import helper functions here, so tests can import from tests.game directly
from tests.game.utils import create_map, new_settlement, settle # isort:skip


def new_session(mapgen=create_map, rng_seed=RANDOM_SEED, human_player=True, ai_players=0):
	"""
	Create a new session with a map, add one human player and a trader (it will crash
	otherwise). It returns both session and player to avoid making the function-based
	tests too verbose.
	"""
	session = SPTestSession(rng_seed=rng_seed)
	human_difficulty = DifficultySettings.DEFAULT_LEVEL
	ai_difficulty = DifficultySettings.EASY_LEVEL

	players = []
	if human_player:
		players.append({
			'id': 1,
			'name': 'foobar',
			'color': Color.get(1),
			'local': True,
			'ai': False,
			'difficulty': human_difficulty,
		})

	for i in range(ai_players):
		id = i + human_player + 1
		players.append({
			'id': id,
			'name': ('AI' + str(i)),
			'color': Color.get(id),
			'local': (id == 1),
			'ai': True,
			'difficulty': ai_difficulty,
		})

	session.load(mapgen(), players, ai_players > 0, True)
	return session, session.world.player


def load_session(savegame, rng_seed=RANDOM_SEED, is_map=False):
	"""
	Start a new session with the given savegame.
	"""
	session = SPTestSession(rng_seed=rng_seed)

	session.load(savegame, [], False, is_map)

	return session


def saveload(session):
	"""Save and load the game (game test version). Use like this:

	# For game tests
	session = saveload(session)
	"""
	fd, filename = tempfile.mkstemp()
	os.close(fd)
	assert session.save(savegamename=filename)
	session.end(keep_map=True)
	game_session = load_session(filename)
	Scheduler().before_ticking() # late init finish (not ticking already)
	return game_session


def game_test(timeout=15 * 60, mapgen=create_map, human_player=True, ai_players=0,
              manual_session=False, use_fixture=False):
	"""
	Decorator that is needed for each test in this package. setup/teardown of function
	based tests can't pass arguments to the test, or keep a reference somewhere.
	If a test fails, we need to reset the session under all circumstances, otherwise we
	break the rest of the tests. The global database reference has to be set each time too,
	unittests use this too, and we can't predict the order tests run (we should not rely
	on it anyway).
	"""

	def handler(signum, frame):
		raise Exception('Test run exceeded {:d}s time limit'.format(timeout))

	def deco(func):
		def wrapped(*args):
			if not manual_session and not use_fixture:
				s, p = new_session(mapgen=mapgen, human_player=human_player, ai_players=ai_players)
			elif use_fixture:
				path = os.path.join(TEST_FIXTURES_DIR, use_fixture + '.sqlite')
				if not os.path.exists(path):
					raise Exception('Savegame {} not found'.format(path))
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
				except Exception:
					pass
					# An error happened after cleanup after an error.
					# This is ok since cleanup is only defined to work when invariants are in place,
					# but the first error could have violated one.
					# Therefore only use failsafe cleanup:
				finally:
					SPTestSession.cleanup()

				timelimit.stop()
		return wrapped
	return deco
