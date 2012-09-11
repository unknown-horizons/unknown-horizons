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

from horizons.command.uioptions import AddToBuyList
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import RES, TIER

from tests.gui import gui_test, TestFinished
from tests.gui.helper import get_player_ship, move_ship
from tests.gui.scenarios.helper import (assert_win, var_eq, wait_and_close_logbook,
										settlement_res_stored_greater, settler_level_greater)


@gui_test(use_scenario='content/scenarios/tutorial_en', timeout=360)
def test_tutorial(gui):
	"""Test the tutorial scenario."""
	yield

	# FIXME disable disasters (this should be an option for a scenario)
	gui.session.world.disaster_manager.disabled = True

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

	# TODO do this with the gui (needs named buttons and a way to control the slider)
	player = gui.session.world.player
	tradepost = player.settlements[0].get_component(TradePostComponent)
	AddToBuyList(tradepost, RES.TOOLS, 30)(player)

	# Goal: Pavilion
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 40)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 5):
		yield

	gui.trigger('tab', 'button_12')
	gui.cursor_click(19, 16, 'left')

	# Goal: Next tier
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 43)

	# TODO adjust settler taxes

	# wait until settlers upgraded
	while not settler_level_greater(gui.session, TIER.SAILORS):
		yield

	# Goal: Farm
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 46)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 10):
		yield

	gui.trigger('tab_base', '1') # FIXME this sometimes fails
	gui.trigger('tab', 'button_02')
	gui.cursor_click(25, 12, 'left')
	
	# Goal: Fields
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 49)

	gui.trigger('tab_base', '1')

	# potato
	gui.trigger('tab', 'button_12')
	gui.cursor_click(23, 11, 'left')

	# pasture
	gui.trigger('tab', 'button_22')
	gui.cursor_click(21, 10, 'left')

	# Goal: Storage
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 52)

	# remove a tree to connect to farm
	gui.trigger('mainhud', 'destroy_tool')
	gui.cursor_click(21, 15, 'left')

	# roads
	gui.trigger('mainhud', 'build')
	gui.trigger('tab_base', '0')
	gui.trigger('tab', 'button_21')
	gui.cursor_click(21, 15, 'left', shift=True)
	gui.cursor_click(22, 15, 'left', shift=True)
	gui.cursor_click(23, 15, 'left', shift=True)
	gui.cursor_click(24, 15, 'left', shift=True)
	gui.cursor_click(24, 14, 'left', shift=True)
	gui.cursor_click(24, 14, 'right')
	
	# storage tent
	gui.trigger('tab', 'button_11')
	gui.cursor_click(21, 16, 'left')

	# Goal: Weaver
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 55)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 10):
		yield

	gui.trigger('tab_base', '1')
	gui.trigger('tab', 'button_21')
	gui.cursor_click(25, 14, 'left')

	# Goal: 50 inhabitants, positive balance
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 58)
	
	# more potatoe fields
	gui.trigger('tab_base', '1')
	gui.trigger('tab', 'button_12')
	gui.cursor_click(24, 9, 'left', shift=True)
	gui.cursor_click(27, 8, 'left', shift=True)
	gui.cursor_click(27, 11, 'left', shift=True)
	gui.cursor_click(27, 11, 'right')

	# lumberjack (more wood for upgrades)
	gui.trigger('tab_base', '0')
	gui.trigger('tab', 'button_03')
	gui.cursor_click(19, 18, 'left')

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 39):
		yield

	# tents
	gui.trigger('tab', 'button_01')
	gui.cursor_click(11, 14, 'left', shift=True)
	gui.cursor_click(11, 15, 'left', shift=True)
	gui.cursor_click(12, 17, 'left', shift=True)
	gui.cursor_click(11, 20, 'left', shift=True)
	gui.cursor_click(12, 22, 'left', shift=True)
	gui.cursor_click(14, 22, 'left', shift=True)
	gui.cursor_click(16, 22, 'left', shift=True)
	gui.cursor_click(18, 22, 'left', shift=True)
	gui.cursor_click(19, 20, 'left', shift=True)
	gui.cursor_click(22, 15, 'left', shift=True)
	gui.cursor_click(19, 20, 'right')

	# Goal: Won
	for _ in wait_and_close_logbook(gui): yield
	assert var_eq(gui.session, 'tutorial_progress', 61)

	for _ in assert_win(gui): yield
	yield TestFinished
