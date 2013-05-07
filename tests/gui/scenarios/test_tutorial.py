# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

from horizons.constants import RES, TIER

from tests.gui import gui_test
from tests.gui.helper import get_player_ship, move_ship
from tests.gui.scenarios.helper import (assert_win, var_eq, wait_and_close_logbook,
										settlement_res_stored_greater, settler_level_greater)


@gui_test(use_scenario='content/scenarios/tutorial_en', timeout=360)
def test_tutorial(gui):
	"""Test the tutorial scenario."""

	# FIXME disable disasters (this should be an option for a scenario)
	gui.session.world.disaster_manager.disabled = True

	def assert_progress(progress):
		wait_and_close_logbook(gui)
		assert var_eq(gui.session, 'tutorial_progress', progress)

	# Tutorial start
	assert_progress(16)

	# Goal: Build warehouse
	ship = get_player_ship(gui.session)
	gui.select([ship])
	move_ship(gui, ship, (11, 1))

	gui.trigger('overview_trade_ship', 'found_settlement')
	gui.cursor_click(11, 6, 'left')

	# Goal: Build a lumberjack
	assert_progress(19)

	# lumberjack (2)
	gui.trigger('mainhud', 'build')
	gui.trigger('tab', 'button_03')
	gui.cursor_click(8, 10, 'left', shift=True)
	gui.cursor_click(13, 10, 'left')
	gui.cursor_click(13, 10, 'right')

	# plant some extra trees around the lumberjacks
	gui.trigger('tab', 'button_13')
	gui.cursor_drag((6, 13), (15, 8), 'left')

	# roads (no dragging to trigger the 'you can drag roads' hint)
	gui.trigger('tab', 'button_21')
	gui.cursor_multi_click((10, 8), (10, 9), (10, 10), (11, 10))

	# Goal: Build hunter and fisher
	assert_progress(22)

	# fisher
	gui.trigger('tab', 'button_33')
	gui.cursor_click(13, 6, 'left')

	# hunter
	gui.trigger('tab', 'button_23')
	gui.cursor_click(8, 8, 'left')

	# Goal: Mainsquare
	assert_progress(25)

	gui.trigger('tab', 'button_02')
	gui.cursor_click(15, 18, 'left')

	# Goal: first tent
	assert_progress(28)

	# roads
	gui.trigger('tab', 'button_21')
	gui.cursor_drag((13, 15), (20, 15), 'left')
	gui.cursor_click(20, 15, 'right')

	# tent
	gui.trigger('tab', 'button_01')
	gui.cursor_click(13, 13, 'left')

	# Goal: 4 tents
	assert_progress(31)

	gui.trigger('tab', 'button_01')
	gui.cursor_multi_click((15, 13), (17, 13), (19, 13))

	# Goal: Build a signal fire
	assert_progress(34)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 5):
		gui.run()

	gui.trigger('tab', 'button_22')
	gui.cursor_click(9, 5, 'left')

	# Goal: Trading
	assert_progress(37)

	# Buy tools from the trader (put the resource on the buy list)
	gui.cursor_click(11, 6, 'left')
	gui.trigger('tab_base', '2')
	gui.trigger('buysellmenu/slot_0', 'button', mouse='left')
	gui.trigger('select_trade_resource', 'resource_%d' % RES.TOOLS)
	gui.find('buysellmenu/slot_0/slider').slide(30)

	# Goal: Pavilion
	assert_progress(40)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 5):
		gui.run()

	gui.trigger('mainhud', 'build')
	gui.trigger('tab', 'button_12')
	gui.cursor_click(19, 16, 'left')

	# Goal: Next tier
	assert_progress(43)

	# Adjust settler taxes (using mainsquare)
	gui.cursor_click(16, 18, 'left')
	gui.trigger('tab_base', '1')
	gui.find('tax_slider').slide(0)
	gui.trigger('mainhud', 'build')

	# wait until settlers upgraded
	while not settler_level_greater(gui.session, TIER.SAILORS):
		gui.run()

	# Goal: Farm
	assert_progress(46)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 10):
		gui.run()

	gui.trigger('tab_base', '1') # FIXME this sometimes fails
	gui.trigger('tab', 'button_02')
	gui.cursor_click(25, 12, 'left')

	# Goal: Fields
	assert_progress(49)

	gui.trigger('tab_base', '1')

	# potato
	gui.trigger('tab', 'button_12')
	gui.cursor_click(23, 11, 'left')

	# pasture
	gui.trigger('tab', 'button_22')
	gui.cursor_click(21, 10, 'left')

	# Goal: Storage
	assert_progress(52)

	# remove a tree to connect to farm
	gui.trigger('mainhud', 'destroy_tool')
	gui.cursor_click(21, 15, 'left')

	# roads
	gui.trigger('mainhud', 'build')
	gui.trigger('tab_base', '0')
	gui.trigger('tab', 'button_21')
	gui.cursor_drag((21, 15), (24, 14), 'left')
	gui.cursor_click(24, 14, 'right')

	# storage tent
	gui.trigger('tab', 'button_11')
	gui.cursor_click(21, 16, 'left')

	# Goal: Weaver
	assert_progress(55)

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 10):
		gui.run()

	gui.trigger('tab_base', '1')
	gui.trigger('tab', 'button_21')
	gui.cursor_click(25, 14, 'left')

	# Goal: 50 inhabitants, positive balance
	assert_progress(58)

	# more potato fields
	gui.trigger('tab_base', '1')
	gui.trigger('tab', 'button_12')
	gui.cursor_multi_click((24, 9), (27, 8), (27, 11))

	# lumberjack (more wood for upgrades)
	gui.trigger('tab_base', '0')
	gui.trigger('tab', 'button_03')
	gui.cursor_click(19, 18, 'left')

	# wait until we have enough boards
	while not settlement_res_stored_greater(gui.session, RES.BOARDS, 39):
		gui.run()

	# tents
	gui.trigger('tab', 'button_01')
	gui.cursor_multi_click(
		(11, 14), (11, 15), (12, 17), (11, 20),
		(12, 22), (14, 22), (16, 22), (18, 22),
		(19, 20), (22, 15)
	)

	# Goal: Won
	assert_progress(61)

	assert_win(gui)
