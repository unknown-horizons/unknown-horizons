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

from horizons.scenario import ACTIONS

from tests.gui import gui_test, TestFinished


# Patch scenario actions for easier detection

def do_win(session):
	session._scenariotest_won = True

def do_lose(session):
	session._scenariotest_lose = True

ACTIONS.get('win').func_code = do_win.func_code
ACTIONS.get('lose').func_code = do_lose.func_code


# Example tests

@gui_test(use_scenario='tests/gui/scenarios/win', timeout=10)
def test_win(gui):
	"""Simple test that detects a win in a game."""
	while True:
		if getattr(gui.session, '_scenariotest_won', False):
			break
		yield

	yield TestFinished


@gui_test(use_scenario='tests/gui/scenarios/defeat', timeout=10)
def test_defeat(gui):
	"""Simple test that detects a defeat in a game."""
	while True:
		if getattr(gui.session, '_scenariotest_lose', False):
			break
		yield

	yield TestFinished
