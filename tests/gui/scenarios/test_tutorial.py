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

from tests.gui import gui_test
from tests.gui.scenarios.helper import wait_and_close_logbook
from tests.gui.scenarios.tutorial_body import run_tutorial


class SlowWait:
	"""Advance the game at the normal test speed."""

	def __init__(self, gui):
		self.gui = gui

	def until(self, predicate):
		while not predicate():
			self.gui.run()

	def progress(self, goal, may_skip=()):
		# Wait for the logbook, then check the reached goal. A following goal may
		# have fired in the same tick (see tutorial_body), so accept those too.
		wait_and_close_logbook(self.gui)
		value = self.gui.session.scenario_eventhandler._scenario_variables['tutorial_progress']
		allowed = [goal] + list(may_skip)
		assert value in allowed, (value, allowed)


# Long: runs the scenario in real time. test_tutorial_fast covers the same steps
# for CI.
@pytest.mark.long
@gui_test(use_scenario='content/scenarios/tutorial_en', timeout=7 * 60)
def test_tutorial(gui):
	run_tutorial(gui, SlowWait(gui))
