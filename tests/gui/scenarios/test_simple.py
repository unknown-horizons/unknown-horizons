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


from tests.gui import gui_test, TestFinished
from tests.gui.helper import get_player_ship, move_ship
from tests.gui.scenarios.helper import assert_win, assert_defeat, assert_goal_reached

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
	ship = get_player_ship(gui.session)
	for _ in move_ship(ship, (7, 3)): yield

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
