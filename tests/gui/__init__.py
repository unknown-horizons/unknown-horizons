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

"""
How GUI tests are run:

A test marked with the `gui_test` decorator will be collected by nose.
When this test is run, it will launch the game in a subprocess, passing it the
dotted path to the test (along with other options), similar to this code:

	def test_example():
		returncode = subprocess.call(['python', 'run_uh.py', '--gui-test',
									  'tests.gui.minimap'])
		if returncode != 0:
			assert False

	def minimap(gui):
		yield
		menu = gui.find(name='mainmenu')
		yield TestFinished

When the game is run with --gui-test, an instance of `TestRunner` will load
the test and install a callback function in the engine's mainloop. Each call
the test will be further exhausted:

	def callback():
		value = minimap.next()
		if value == TestFinished:
			# Test ends
"""

import os
import shutil
import subprocess
import sys
import tempfile
from functools import wraps

from nose.plugins import Plugin

from tests import RANDOM_SEED
from tests.gui.helper import GuiHelper
from tests.utils import Timer

# path where test savegames are stored (tests/gui/ingame/fixtures/)
TEST_FIXTURES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ingame', 'fixtures')

# Used by the test to signal that's it's finished.
# Needed to distinguish between the original test and other generators used
# for dialogs.
TestFinished = 'finished'

class TestFailed(Exception): pass


TEST_USER_DIR = None

def setup_package():
	"""Create a temporary directory to use as user directory (settings, savegames etc.)
	while the tests are running."""
	global TEST_USER_DIR
	TEST_USER_DIR = tempfile.mkdtemp()


def teardown_package():
	"""Delete the user directory."""
	global TEST_USER_DIR
	shutil.rmtree(TEST_USER_DIR)
	TEST_USER_DIR = None


def recreate_userdir():
	"""Cleanup user directory by deleting the old and using a new path.

	Some tests may modify the user directory, e.g. by saving games, we need to
	revert these changes."""
	global TEST_USER_DIR
	shutil.rmtree(TEST_USER_DIR)
	TEST_USER_DIR = tempfile.mkdtemp()


class GuiTestPlugin(Plugin):
	"""This plugin is used to improve the test failure display for gui tests.

	Because nose runs in a different process than the real test, we cannot easily
	show the traceback as if the exception occured here. The real traceback will
	be used as message in an `TestFailed` exception, which we capture here and
	remove the traceback (from the TestFailed raise) entirely, leaving us just
	with the exception.

	This:

		------------------------
		Traceback (most recent call last):
			File "/path/to/nose/case.py", line 197, in runTest
				self.test(*self.arg)
			File "/path/to/tests/gui/__init__.py", line 273, in wrapped
				raise TestFailed("\n\n" + error)
		TestFailed:

		[Real traceback]

	Becomes:

		------------------------
		TestFailed:

		[Real traceback]
	"""
	name = 'guitest'
	enabled = True

	def configure(self, options, conf):
		pass

	def formatError(self, test, err):
		exc_type, value, traceback = err
		if exc_type == TestFailed:
			traceback = None

		return exc_type, value, traceback


class TestRunner(object):
	"""Manages test execution.

	Tests have to be generators. With generators, we can give control back to the
	engine anytime we want and easily continue at that point later.
	Letting the engine run is important, because otherwise no timer will be
	continued and for example a production will never finish.

	Dialogs need to be handled slightly different. Their execution results in a
	separate call to the engine's mainloop, in turn, this would call the `_tick`
	method and attempt to continue the generator (which is still running).

	Therefore, a new generator has to be installed to handle dialogs. Handlers are
	hold in list used as stack - only the last added handler will be continued
	until it has finished.
	"""
	__test__ = False

	def __init__(self, engine, test_path):
		self._engine = engine
		self._gui_handlers = []

		self._filter_traceback()
		test = self._load_test(test_path)
		test_gen = test(GuiHelper(self._engine.pychan, self))
		self._gui_handlers.append(test_gen)
		self._start()

	def _filter_traceback(self):
		"""Remove test internals from exception tracebacks.

		Makes them shorter and easier to read. The last trace of internals is
		the call of `TestRunner._tick`
		"""
		def skip_internals(func):
			def wrapped(exctype, value, tb):
				while tb and 'TestRunner' not in tb.tb_frame.f_globals:
					tb = tb.tb_next
				tb = tb.tb_next
				func(exctype, value, tb)
			return wrapped

		sys.excepthook = skip_internals(sys.excepthook)

	def _load_test(self, test_name):
		"""Import test from dotted path, e.g.:

			tests.gui.test_example.example
		"""
		path, name = test_name.rsplit('.', 1)
		__import__(path)
		module = sys.modules[path]
		test_function = getattr(module, name)

		# __original__ is the real test function that was
		# decorated with `gui_test`
		return test_function.__original__

	def _start(self):
		self._engine.pump.append(self._tick)

	def _stop(self):
		self._engine.pump.remove(self._tick)
		self._engine.breakLoop(0)

	def _tick(self):
		"""Continue test execution.

		This function will be called by the engine's mainloop each frame.
		"""
		try:
			# continue execution of current gui handler
			value = self._gui_handlers[-1].next()
			if value == TestFinished:
				self._stop()
		except StopIteration:
			# if we end up here, it means that either
			#   - a dialog handler has finished its execution (all fine) or
			#   - the test has finished without signaling it (this might be on purpose)
			#
			# TODO issue a warning if this was the test itself
			pass


def gui_test(use_dev_map=False, use_fixture=None, ai_players=0, timeout=15 * 60, cleanup_userdir=False):
	"""Magic nose integration.

	use_dev_map		-	starts the game with --start-dev-map
	use_fixture		-	starts the game with --load-map=fixture_name
	ai_players		-	starts the game with --ai_players=<number>
	timeout			-	test will be stopped after X seconds passed (0 = disabled)
	cleanup_userdir	-	whether the userdir should be cleaned after the test

	Each GUI test is run in a new process. In case of an error, stderr will be
	printed. That way it will appear in the nose failure listing.
	"""
	def deco(func):
		@wraps(func)
		def wrapped():
			test_name = '%s.%s' % (func.__module__, func.__name__)

			# when running under coverage, enable it for subprocesses too
			if os.environ.get('RUNCOV'):
				executable = ['coverage', 'run']
			else:
				executable = [sys.executable]

			args = executable + ['run_uh.py', '--sp-seed', str(RANDOM_SEED), '--gui-test', test_name]
			if use_fixture:
				path = os.path.join(TEST_FIXTURES_DIR, use_fixture + '.sqlite')
				if not os.path.exists(path):
					raise Exception('Savegame %s not found' % path)
				args.extend(['--load-map', path])
			elif use_dev_map:
				args.append('--start-dev-map')

			if ai_players:
				args.extend(['--ai-players', str(ai_players)])

			try:
				# if nose does not capture stdout, then most likely someone wants to
				# use a debugger (he passed -s at the cmdline). In that case, we will
				# redirect stdout/stderr from the gui-test process to the testrunner
				# process.
				sys.stdout.fileno()
				stdout = sys.stdout
				stderr = sys.stderr
				nose_captured = False
			except AttributeError:
				# if nose captures stdout, we can't redirect to sys.stdout, as that was
				# replaced by StringIO. Instead we capture it and return the data at the
				# end.
				stdout = subprocess.PIPE
				stderr = subprocess.PIPE
				nose_captured = True

			# Activate fail-fast, this way the game will stop running when for example the
			# savegame could not be loaded (instead of showing an error popup)
			env = os.environ.copy()
			env['FAIL_FAST'] = '1'
			env['UH_USER_DIR'] = TEST_USER_DIR

			# Start game
			proc = subprocess.Popen(args, stdout=stdout, stderr=stderr, env=env)

			def handler(signum, frame):
				proc.kill()
				raise TestFailed('\n\nTest run exceeded %ds time limit' % timeout)

			timelimit = Timer(handler)
			timelimit.start(timeout)

			stdout, stderr = proc.communicate()
			if proc.returncode != 0:
				if nose_captured:
					if stdout:
						print stdout
					if cleanup_userdir:
						recreate_userdir()
					if not 'Traceback' in stderr:
						stderr += '\nNo usable error output received, possibly a segfault.'
					raise TestFailed('\n\n' + stderr)
				else:
					if cleanup_userdir:
						recreate_userdir()
					raise TestFailed()

		# we need to store the original function, otherwise the new process will execute
		# this decorator, thus spawning a new process..
		wrapped.__original__ = func
		wrapped.gui = True # mark as gui for test selection
		return wrapped

	return deco

gui_test.__test__ = False

# FIXME GUI tests still don't work in parallel, this is needed for game/unit tests to work
_multiprocess_can_split_ = True
