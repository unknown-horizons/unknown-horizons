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

from horizons.command.building import Tear
from horizons.command.unit import CreateUnit
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, RES, UNITS
from horizons.messaging import ResourceProduced
from horizons.world.production.producer import Producer
from tests.gui import gui_test
from tests.gui.helper import found_settlement, get_player_ship, move_ship


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1352(gui):
	"""
	Clicking on a frigate crashes the game.
	"""

	player = gui.session.world.player
	ship = CreateUnit(player.worldid, UNITS.FRIGATE, 68, 10)(player)
	x, y = ship.position.x, ship.position.y

	gui.session.view.center(x, y)

	"""
	# low-level selection
	# disabled because it is difficult to select the ship
	gui.cursor_move(x, y)
	gui.cursor_click(x, y, 'left')
	"""

	gui.select([ship])


@gui_test(use_dev_map=True, ai_players=3, timeout=120)
def test_ticket_1368(gui):
	"""
	Selecting a warehouse from an ai player crashes.

	Test runs faster with 3 AI players, because a new settlement is
	founded earlier. It is still pretty slow, but let's care about
	speed later.
	"""

	# Wait until ai has settled down
	world = gui.session.world
	while not world.settlements:
		gui.run()

	ai_warehouse = world.settlements[0].warehouse
	gui.select([ai_warehouse])


@gui_test(use_fixture='ai_settlement', timeout=60)
def test_ticket_1369(gui):
	"""
	Ship tab closed when moving away from another player's warehouse after trading.
	"""

	ship = get_player_ship(gui.session)
	gui.select([ship])

	# ally players so they can trade
	world = gui.session.world
	for player in world.players:
		if player is not ship.owner:
			world.diplomacy.add_ally_pair(ship.owner, player)

	# move ship near foreign warehouse and wait for it to arrive
	move_ship(gui, ship, (68, 23))

	# click trade button
	gui.trigger('overview_trade_ship/trade')

	# trade widget visible
	assert gui.find(name='buy_sell_goods')

	# move ship away from warehouse
	move_ship(gui, ship, (77, 17))

	# trade widget should not be visible anymore
# For now, the trade widget will stay visible.
#	assert gui.find(name='buy_sell_goods') is None

	# but the ship overview should be
	assert gui.find(name='buy_sell_goods')
#	assert gui.find(name='overview_trade_ship')


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1362(gui):
	"""
	Saving a game, loading it again and attempting to save it again will crash.
	"""

	gui.press_key(gui.Key.F5)	# quicksave
	gui.run(seconds=2)

	gui.press_key(gui.Key.F9)	# quickload
	while gui.find(name='loadingscreen'):
		gui.run()

	def func():
		# test for error popup
		assert gui.find(name='popup_window') is None

	# quicksave
	with gui.handler(func):
		gui.press_key(gui.Key.F5)


@gui_test(use_fixture='plain', timeout=120)
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

	found_settlement(gui, (59, 1), (56, 3))

	# Build lumberjack
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_03')
	gui.cursor_click(52, 7, 'left')

	# Select lumberjack
	gui.cursor_click(52, 7, 'left')

	# Open build related tab
	gui.trigger('tab_base/1')

	# Select tree
	gui.trigger('overview_buildrelated/build17')

	# Plant a tree (without uninterrupted building)
	gui.cursor_click(49, 6, 'left')
	assert gui.find(name='overview_buildrelated')

	# Select tree again and plant it with uninterrupted building
	gui.trigger('overview_buildrelated/build17')
	gui.cursor_click(49, 7, 'left', shift=True)

	# Tab should still be there
	assert gui.find(name='overview_buildrelated')


@gui_test(use_fixture='fife_exception_not_found', timeout=60)
def test_ticket_1447(gui):
	"""
	Clicking on a sequence of buildings may make fife throw an exception.
	"""

	lumberjack = gui.session.world.islands[0].ground_map[(23, 63)].object
	assert lumberjack.id == BUILDINGS.LUMBERJACK

	fisher = gui.session.world.islands[0].ground_map[(20, 67)].object
	assert fisher.id == BUILDINGS.FISHER

	warehouse = gui.session.world.islands[0].ground_map[(18, 63)].object
	assert warehouse.id == BUILDINGS.WAREHOUSE

	gui.cursor_click(20, 67, 'left')
	gui.run()

	gui.cursor_click(23, 63, 'left')
	gui.run()

	gui.cursor_click(18, 63, 'left')
	gui.run()


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1515(gui):
	"""
	Unable to select an unowned resource deposit.
	"""

	gui.cursor_click(6, 17, 'left')


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1520(gui):
	"""
	Crash when completing build after outlined/related buildings were removed.
	"""

	found_settlement(gui, (8, 2), (10, 6))

	ground_map = gui.session.world.islands[0].ground_map

	# Build a tent
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_01')
	gui.cursor_click(7, 9, 'left')

	assert ground_map[(7, 9)].object.id == BUILDINGS.RESIDENTIAL

	# Start building a mainsquare (not releasing left mouse button)
	gui.trigger('tab/button_02')
	gui.cursor_move(13, 11)
	gui.cursor_press_button(13, 11, 'left')

	# remove tent
	Tear(ground_map[(7, 9)].object).execute(gui.session)

	# release mouse button, finish build
	gui.cursor_release_button(13, 11, 'left')


@gui_test(use_dev_map=True, timeout=120)
def test_ticket_1509(gui):
	"""
	Crash when quickly switching between tent tabs.
	"""

	found_settlement(gui, (8, 2), (10, 6))

	# Build a tent
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_01')
	gui.cursor_click(7, 10, 'left')

	# Select tent
	gui.cursor_click(7, 10, 'left')

	# quickly switch between tabs
	gui.trigger('tab_base/1')
	gui.run()
	gui.trigger('tab_base/0')
	gui.run()
	gui.trigger('tab_base/1')


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1526(gui):
	"""
	Multiselection with Ctrl crashes on many combinations.
	"""

	# Select main square and then boat builder
	gui.cursor_click(52, 12, 'left')
	gui.cursor_click(64, 10, 'left', ctrl=True)

	# Select same building twice
	gui.cursor_click(52, 12, 'left')
	gui.cursor_click(52, 12, 'left', ctrl=True)


@gui_test(use_fixture='plain', timeout=120)
def test_pavilion_build_crash_built_via_settler_related_tab(gui):
	"""
	"""

	found_settlement(gui, (59, 1), (56, 3))

	# Build settler
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_01')
	gui.cursor_click(52, 7, 'left')

	# Select settler
	gui.cursor_click(52, 7, 'left')

	# Open build related tab
	gui.trigger('tab_base/1')

	# Select pavilion
	gui.trigger('overview_buildrelated/build5')

	# Plant it
	gui.cursor_click(49, 6, 'left')

	# if we survive until here, the bug hasn't happened


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1848(gui):
	"""Settlement production overview crashes if ships were produced"""

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Build huker
	gui.cursor_click(64, 10, 'left')
	gui.trigger('tab_base/1')
	gui.trigger('boatbuilder_showcase/ok_0')

	# Wait until production ends
	producer = boatbuilder.get_component(Producer)
	while producer.get_productions():
		gui.run()

	gui.cursor_click(51, 13, 'left')
	gui.trigger('tab_account/show_production_overview')


@gui_test(use_fixture='plain')
def test_ticket_1948(gui):
	"""Triggers a crash that happens when building a storage tent on the border of the settlement"""
	# Units cannot be selected right now, you need to do it this way. This is almost
	# the same as selecting it with the mouse
	ship = get_player_ship(gui.session)
	gui.select([ship])
	found_settlement(gui, (59, 1), (56, 3))

	# Select storage tent
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_11')
	# Build storage at the border of the settlement
	gui.cursor_click(37, 20, 'left')


@gui_test(use_fixture='fife_exception_not_found', timeout=60)
def test_ticket_2117(gui):
	"""Changing language with active production overview tab crashes game"""

	# Select lumberjack to open production tab
	gui.cursor_click(23, 63, 'left')

	# Open settings
	gui.trigger('mainhud/gameMenuButton')
	gui.trigger('menu/button_images/settingsLink')

	# Change language (to anything not system default)
	gui.trigger('settings_window/game_settings_right')
	gui.find('uni_language').select(u'English')
	gui.trigger('settings_window/okButton')


@gui_test(use_dev_map=True)
def test_ticket_2419(gui):
	"""Game crashes when setting speed to zero and pressing pause twice"""

	gui.session.speed_set(0)
	gui.press_key(gui.Key.P)
	gui.press_key(gui.Key.P)


@gui_test(use_dev_map=True)
def test_ticket_2475(gui):
	"""Game crashes when two resources are produced in the same tick and the production
	finished icon is about to be shown."""

	# speed up animation to trigger bug earlier
	gui.session.ingame_gui.production_finished_icon_manager.animation_duration = 1

	ship = get_player_ship(gui.session)
	gui.select([ship])
	settlement = found_settlement(gui, (13, 64), (17, 62))

	# Place a lumberjack
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_03')
	gui.cursor_click(18, 57, 'left', shift=True)

	lumberjack = settlement.buildings_by_id[BUILDINGS.LUMBERJACK][0]
	storage = lumberjack.get_component(StorageComponent)
	producer = lumberjack.get_component(Producer)

	storage.inventory.alter(RES.BOARDS, 5)

	producer.on_production_finished({RES.BOARDS: 1})
	producer.on_production_finished({RES.BOARDS: 1})


@gui_test(use_dev_map=True)
def test_ticket_2500(gui):
	"""Game crashes when exiting the game while the building tool is still active."""

	ship = get_player_ship(gui.session)
	gui.select([ship])
	settlement = found_settlement(gui, (13, 64), (17, 62))

	# Select lumberjack
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_03')

	# Quit game via pause menu
	gui.press_key(gui.Key.P)

	def dialog():
		gui.trigger('popup_window/okButton')

	with gui.handler(dialog):
		gui.trigger('menu/quit')
