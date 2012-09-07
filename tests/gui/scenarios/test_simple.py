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

from horizons.command.unit import Act
from horizons.scenario import ACTIONS

from tests.gui import gui_test, TestFinished
from tests.gui.helper import get_player_ship
from tests.gui.scenarios.helper import assert_win, assert_defeat, assert_goal_reached


# Patch scenario actions for easier detection

def do_win(session):
	session._scenariotest_won = True

def do_lose(session):
	session._scenariotest_lose = True

def goal_reached(session, goal):
	if hasattr(session, '_scenariotest_goals'):
		session._scenariotest_goals.append(goal)
	else:
		session._scenariotest_goals = [goal]

ACTIONS.get('win').func_code = do_win.func_code
ACTIONS.get('lose').func_code = do_lose.func_code
ACTIONS.get('goal_reached').func_code = goal_reached.func_code


# Example tests

@gui_test(use_scenario='tests/gui/scenarios/win', timeout=10)
def test_win(gui):
	"""Simple test that detects a win in a game."""
	yield

	for _ in assert_win(gui): yield
	yield TestFinished


@gui_test(use_scenario='tests/gui/scenarios/defeat', timeout=10)
def test_defeat(gui):
	"""Simple test that detects a defeat in a game."""
	yield

	for _ in assert_defeat(gui): yield
	yield TestFinished


@gui_test(use_scenario='tests/gui/scenarios/mission1', timeout=30)
def test_mission1(gui):
	"""Sample mission which requires multiple buildings to win."""
	yield

	# Move ship to coast
	target = (7, 3)
	player = gui.session.world.player
	ship = get_player_ship(gui.session)
	Act(ship, *target)(player)

	while (ship.position.x, ship.position.y) != target:
		yield

	# Build warehouse
	gui.select([ship])
	gui.trigger('overview_trade_ship', 'found_settlement')
	gui.cursor_click(10, 5, 'left')
	for _ in assert_goal_reached(gui, 'warehouse'): yield

	# Build main square
	gui.trigger('mainhud', 'build')
	gui.trigger('tab', 'button_02')
	gui.cursor_click(9, 11, 'left')
	for _ in assert_goal_reached(gui, 'mainsquare'): yield

	# Build fisher
	gui.trigger('tab', 'button_33')
	gui.cursor_click(7, 7, 'left')

	for _ in assert_win(gui): yield

	yield TestFinished
