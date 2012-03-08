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

from horizons.command.unit import CreateUnit
from horizons.command.building import Tear
from horizons.constants import UNITS, BUILDINGS
from tests.gui import TestFinished, gui_test
from tests.gui.helper import get_player_ship


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1352(gui):
	"""
	Clicking on a frigate crashes the game.
	"""
	yield # test needs to be a generator for now

	player = gui.session.world.player
	ship = CreateUnit(player.worldid, UNITS.FRIGATE_CLASS, 68, 10)(player)
	x, y = ship.position.x, ship.position.y

	gui.session.view.center(x, y)

	"""
	# low-level selection
	# disabled because it is difficult to select the ship
	gui.cursor_move(x, y)
	gui.cursor_click(x, y, 'left')
	"""

	gui.select([ship])

	yield TestFinished


@gui_test(use_dev_map=True, ai_players=3, timeout=120)
def test_ticket_1368(gui):
	"""
	Selecting a warehouse from an ai player crashes.

	Test runs faster with 3 AI players, because a new settlement is
	founded earlier. It is still pretty slow, but let's care about
	speed later.
	"""
	yield # test needs to be a generator for now

	# Wait until ai has settled down
	world = gui.session.world
	while not world.settlements:
		yield

	ai_warehouse = world.settlements[0].warehouse
	gui.select([ai_warehouse])

	yield TestFinished


@gui_test(use_fixture='ai_settlement', timeout=60)
def test_ticket_1369(gui):
	"""
	Ship tab closed when moving away from another player's warehouse after trading.
	"""
	yield

	ship = get_player_ship(gui.session)
	gui.select([ship])

	# ally players so they can trade
	world = gui.session.world
	for player in world.players:
		if player is not ship.owner:
			world.diplomacy.add_ally_pair( ship.owner, player )

	# move ship near foreign warehouse and wait for it to arrive
	gui.cursor_click(68, 23, 'right')
	while (ship.position.x, ship.position.y) != (68, 23):
		yield

	# click trade button
	gui.trigger('overview_trade_ship', 'trade/action/default')

	# trade widget visible
	assert gui.find(name='buy_sell_goods')

	# move ship away from warehouse
	gui.cursor_click(77, 17, 'right')
	while (ship.position.x, ship.position.y) != (77, 17):
		yield

	# trade widget should not be visible anymore
	assert gui.find(name='buy_sell_goods') is None

	# but the ship overview should be
	assert gui.find(name='overview_trade_ship')

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1362(gui):
	"""
	Saving a game, loading it again and attempting to save it again will crash.
	"""
	yield

	gui.press_key(gui.Key.F5)	# quicksave
	for i in gui.run(seconds=2):
		yield

	gui.press_key(gui.Key.F9)	# quickload
	while gui.find(name='loadingscreen'):
		yield

	def func():
		yield
		# test for error popup
		assert gui.find(name='popup_window') is None

	# quicksave
	with gui.handler(func):
		gui.press_key(gui.Key.F5)

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1371(gui):
	"""
	Build related tab becomes invisible.

	 * use uninterrupted building (press shift)
	 * click on lumberjack
	 * click on the 'build related' tab
	 * click on the tree
	 * build a tree

     => tab itself is invisible, but buttons for choosing it aren't
	"""
	yield

	ship = get_player_ship(gui.session)
	gui.select([ship])

	gui.cursor_click(59, 1, 'right')
	while (ship.position.x, ship.position.y) != (59, 1):
		yield

	# Found settlement
	gui.trigger('overview_trade_ship', 'found_settlement/action/default')

	gui.cursor_click(56, 3, 'left')

	gui.trigger('mainhud', 'build/action/default')

	# Build lumberjack
	gui.trigger('tab', 'button_5/action/default')
	gui.cursor_click(52, 7, 'left')

	# Select lumberjack
	gui.cursor_click(52, 7, 'left')

	# Open build related tab
	gui.trigger('tab_base', '1/action/default')

	# Select tree
	gui.trigger('farm_overview_buildrelated', 'build17/action/default')

	# Plant a tree (without uninterrupted building)
	gui.cursor_click(49, 6, 'left')
	assert gui.find(name='farm_overview_buildrelated')

	# Select tree again and plant it with uninterrupted building
	gui.trigger('farm_overview_buildrelated', 'build17/action/default')
	gui.cursor_click(49, 7, 'left', shift=True)

	# Tab should still be there
	assert gui.find(name='farm_overview_buildrelated')

	yield TestFinished

@gui_test(use_fixture='fife_exception_not_found', timeout=60)
def test_ticket_1447(gui):
	"""
	Clicking on a sequence of buildings may make fife throw an exception.
	"""
	yield

	lumberjack = gui.session.world.islands[0].ground_map[(23, 63)].object
	assert(lumberjack.id == BUILDINGS.LUMBERJACK_CLASS)

	fisher = gui.session.world.islands[0].ground_map[(20, 67)].object
	assert(fisher.id == BUILDINGS.FISHERMAN_CLASS)

	warehouse = gui.session.world.islands[0].ground_map[(18, 63)].object
	assert(warehouse.id == BUILDINGS.WAREHOUSE_CLASS)

	gui.cursor_click(20, 67, 'left')
	yield

	gui.cursor_click(23, 63, 'left')
	yield

	gui.cursor_click(18, 63, 'left')
	yield # this could crash the game

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1515(gui):
	"""
	Unable to select an unowned resource deposit.
	"""
	yield # test needs to be a generator for now

	gui.cursor_click(6, 17, 'left')

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1520(gui):
	"""
	Crash when completing build after outlined/related buildings were removed.
	"""
	yield

	ship = get_player_ship(gui.session)
	gui.select([ship])

	gui.cursor_click(8, 2, 'right')
	while (ship.position.x, ship.position.y) != (8, 2):
		yield

	# Found a settlement
	gui.trigger('overview_trade_ship', 'found_settlement/action/default')
	gui.cursor_click(10, 6, 'left')

	ground_map = gui.session.world.islands[0].ground_map

	# Build a tent
	gui.trigger('mainhud', 'build/action/default')
	gui.trigger('tab', 'button_1/action/default')
	gui.cursor_click(7, 9, 'left')

	assert ground_map[(7, 9)].object.id == BUILDINGS.RESIDENTIAL_CLASS

	# Start building a mainsquare (not releasing left mouse button)
	gui.trigger('tab', 'button_3/action/default')
	gui.cursor_move(13, 11)
	gui.cursor_press_button(13, 11, 'left')

	# remove tent
	Tear( ground_map[(7, 9)].object ).execute(gui.session)

	# release mouse button, finish build
	gui.cursor_release_button(13, 11, 'left')

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1509(gui):
	"""
	Crash when quickly switching between tent tabs.
	"""
	yield

	ship = get_player_ship(gui.session)
	gui.select([ship])

	gui.cursor_click(8, 2, 'right')
	while (ship.position.x, ship.position.y) != (8, 2):
		yield

	# Found a settlement
	gui.trigger('overview_trade_ship', 'found_settlement/action/default')
	gui.cursor_click(10, 6, 'left')

	# Build a tent
	gui.trigger('mainhud', 'build/action/default')
	gui.trigger('tab', 'button_1/action/default')
	gui.cursor_click(7, 10, 'left')

	# Select tent
	gui.cursor_click(7, 10, 'left')

	# quickly switch between tabs
	gui.trigger('tab_base', '1/action/default')
	yield
	gui.trigger('tab_base', '0/action/default')
	yield
	gui.trigger('tab_base', '1/action/default')

	yield TestFinished


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1526(gui):
	"""
	Multiselection with Ctrl crashes on many combinations.
	"""
	yield

	# Select main square and then boat builder
	gui.cursor_click(52, 12, 'left')
	gui.cursor_click(64, 10, 'left', ctrl=True)

	# Select same building twice
	gui.cursor_click(52, 12, 'left')
	gui.cursor_click(52, 12, 'left', ctrl=True)

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_pavilion_build_crash_built_via_settler_related_tab(gui):
	"""
	"""
	yield

	ship = get_player_ship(gui.session)
	gui.select([ship])

	gui.cursor_click(59, 1, 'right')
	while (ship.position.x, ship.position.y) != (59, 1):
		yield

	# Found settlement
	gui.trigger('overview_trade_ship', 'found_settlement/action/default')

	gui.cursor_click(56, 3, 'left')

	gui.trigger('mainhud', 'build/action/default')

	# Build settler
	gui.trigger('tab', 'button_1/action/default')
	gui.cursor_click(52, 7, 'left')

	# Select settler
	gui.cursor_click(52, 7, 'left')

	# Open build related tab
	gui.trigger('tab_base', '1/action/default')

	# Select pavilion
	gui.trigger('farm_overview_buildrelated', 'build5/action/default')

	# Plant it
	gui.cursor_click(49, 6, 'left')

	# if we survive until here, the bug hasn't happened
	yield TestFinished
