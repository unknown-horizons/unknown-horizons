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

from horizons.constants import RES

from tests.gui import gui_test, TestFinished
from tests.gui.helper import get_player_ship, move_ship
from tests.gui.scenarios.helper import (assert_win, var_eq, wait_and_close_logbook,
										settlement_res_stored_greater)


@gui_test(use_scenario='content/scenarios/tutorial_en', timeout=60)
def test_tutorial(gui):
	"""Test the tutorial scenario."""
	yield

	# Tutorial start
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 16)

	# Goal: Build warehouse
	ship = get_player_ship(gui.session)
	for _ in move_ship(ship, (11, 1)): yield

	gui.select([ship])
	gui.trigger('overview_trade_ship', 'found_settlement')
	gui.cursor_click(11, 6, 'left')

	# Goal: Build a lumberjack
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 19)

	# lumberjack
	gui.trigger('mainhud', 'build')
	gui.trigger('tab', 'button_03')
	gui.cursor_click(8, 10, 'left')

	# roads
	gui.trigger('tab', 'button_21')
	gui.cursor_click(10, 8, 'left', shift=True)
	gui.cursor_click(10, 9, 'left', shift=True)
	gui.cursor_click(10, 10, 'left', shift=True)
	gui.cursor_click(10, 11, 'right')

	# Goal: Build hunter and fisher
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 22)

	# fisher
	gui.trigger('tab', 'button_33')
	gui.cursor_click(13, 6, 'left')

	# hunter
	gui.trigger('tab', 'button_23')
	gui.cursor_click(8, 8, 'left')
	
	# Goal: Mainsquare
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 25)

	gui.trigger('tab', 'button_02')
	gui.cursor_click(15, 18, 'left')

	# Goal: first tent
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 28)

	# roads
	gui.trigger('tab', 'button_21')
	gui.cursor_click(13, 15, 'left', shift=True)
	gui.cursor_click(14, 15, 'left', shift=True)
	gui.cursor_click(15, 15, 'left', shift=True)
	gui.cursor_click(16, 15, 'left', shift=True)
	gui.cursor_click(17, 15, 'left', shift=True)
	gui.cursor_click(18, 15, 'left', shift=True)
	gui.cursor_click(19, 15, 'left', shift=True)
	gui.cursor_click(20, 15, 'left', shift=True)
	gui.cursor_click(20, 15, 'right')

	# tent
	gui.trigger('tab', 'button_01')
	gui.cursor_click(13, 13, 'left')

	# Goal: 4 tents
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 31)

	gui.trigger('tab', 'button_01')
	gui.cursor_click(15, 13, 'left', shift=True)
	gui.cursor_click(17, 13, 'left', shift=True)
	gui.cursor_click(19, 13, 'left', shift=True)
	gui.cursor_click(19, 13, 'right')

	# Goal: Build a signal fire
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 34)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 5):
		yield

	gui.trigger('tab', 'button_22')
	gui.cursor_click(9, 5, 'left')

	# Goal: Trading
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 37)

	#for _ in assert_win(gui): yield
	yield TestFinished
