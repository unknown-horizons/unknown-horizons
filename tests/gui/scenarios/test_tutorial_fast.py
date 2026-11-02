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

"""Fast end-to-end run of the tutorial scenario.

Same steps as ``test_tutorial``, but waits are driven by ``tests.gui.fastforward``
instead of the engine frame rate, so simulation-heavy waits run at CPU speed.
The late game (many buildings/inhabitants/AI) is far slower than the early game
and dominates the runtime.
"""

import pytest

from tests.gui import gui_test
from tests.gui.fastforward import fast_forward
from tests.gui.scenarios.tutorial_body import StopTutorial, run_tutorial


class FastWait:
	"""Advance game time with ``fast_forward`` instead of real time."""

	def __init__(self, gui):
		self.gui = gui

	def _current(self):
		return self.gui.session.scenario_eventhandler._scenario_variables['tutorial_progress']

	def until(self, predicate, max_ticks=2000000):
		# fast_forward stops as soon as the predicate holds: no overshoot.
		if predicate():
			return
		done = fast_forward(max_ticks, stop=predicate)
		if done >= max_ticks:
			raise AssertionError('Waiting exceeded {} game ticks'.format(max_ticks))
		# Let pending UI/event callbacks settle.
		self.gui.run()

	def progress(self, goal, may_skip=()):
		allowed = [goal] + list(may_skip)
		self.until(lambda: self._current() in allowed)
		# Close the logbook so it cannot block later clicks.
		for _ in range(50):
			if self.gui.find('captains_log'):
				self.gui.trigger('captains_log/okButton')
				break
			self.gui.run()


# Stop goal of the short run: late enough to cover both regressions (goal 34
# boards/tents and the goal 43 -> 46 cascade), early enough to stay cheap.
SHORT_STOP_GOAL = 45


@pytest.mark.long
@gui_test(use_scenario='content/scenarios/tutorial_en', timeout=25 * 60)
def test_tutorial_fast(gui):
	run_tutorial(gui, FastWait(gui))


@gui_test(use_scenario='content/scenarios/tutorial_en', timeout=10 * 60)
def test_tutorial_fast_short(gui):
	"""Subset of the tutorial up to the goal 43 -> 46 cascade.

	Stops at the tier goal (43), which normally fires together with the farm goal
	(46). Cheap per-PR end-to-end check covering both fixes.
	"""
	try:
		run_tutorial(gui, FastWait(gui), stop_goal=SHORT_STOP_GOAL)
	except StopTutorial:
		pass
	else:
		raise AssertionError('short run did not reach goal {}'.format(SHORT_STOP_GOAL))
