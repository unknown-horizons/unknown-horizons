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

"""
How GUI tests are run:

A test marked with the `gui_test` decorator will be collected by pytest.
When this test is run, it will launch the game in a subprocess, passing it the
dotted path to the test (along with other options), similar to this code:

	def test_example():
		returncode = subprocess.call(['python3', 'run_uh.py', '--gui-test',
		                              'tests.gui.minimap'])
		if returncode != 0:
			assert False

	def minimap(gui):
		menu = gui.find(name='mainmenu')
"""

import importlib
import os
import sys
import traceback

import pytest

from tests import RANDOM_SEED
from tests.gui import cooperative
from tests.gui.helper import GuiHelper

# path where test savegames are stored (tests/gui/ingame/fixtures/)
TEST_FIXTURES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ingame', 'fixtures')


class TestRunner:
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
	def __init__(self, engine, test_path):
		self._engine = engine

		self._custom_setup()
		#self._filter_traceback()
		test = self._load_test(test_path)
		testlet = cooperative.spawn(test, GuiHelper(self._engine.pychan, self))
		testlet.link(self._stop_test)
		self._start()

	def _stop_test(self, green):
		self._stop()

	def _custom_setup(self):
		"""Change build menu to 'per tier' for tests."""
		import horizons.globals
		from horizons.gui.tabs import BuildTab
		horizons.globals.fife.set_uh_setting("Buildstyle", BuildTab.layout_per_tier_index)

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
		module = importlib.import_module(path)
		return getattr(module, name)

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
			cooperative.schedule()
		except Exception:
			traceback.print_exc()
			sys.exit(1)


# Marker for a gui test. Decorate a function and optionally pass the following
# keyword arguments.
#
# use_dev_map     - starts the game with --start-dev-map
# use_fixture     - starts the game with --load-game=fixture_name
# use_scenario    - starts the game with --start-scenario=scenario_name
# ai_players      - starts the game with --ai_players=<number>
# timeout         - test will be stopped after X seconds passed (0 = disabled)
#
# Example:
#
#   @gui_test(use_dev_map=True, timeout=5)
#   def test_something(gui):
#       gui.run()
#
gui_test = pytest.mark.gui_test
