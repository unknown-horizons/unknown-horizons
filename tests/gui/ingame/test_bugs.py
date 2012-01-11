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
from horizons.constants import UNITS, GAME_SPEED
from tests.gui import TestFinished, gui_test
from tests.gui.helper import get_player_ship


@gui_test(use_dev_map=True)
def test_ticket_1352(gui):
	"""
	Clicking on a frigate crashes the game.
	"""
	yield # test needs to be a generator for now

	player = gui.session.world.player
	ship = CreateUnit(player.worldid, UNITS.FRIGATE, 68, 10)(player)
	x, y = ship.position.x, ship.position.y

	gui.session.view.center(x, y)

	"""
	# low-level selection
	# disabled because it is difficult to select the ship
	with gui.cursor_map_coords():
		gui.cursor_move(x, y)
		gui.cursor_click(x, y, 'left')
	"""

	gui.select([ship])

	yield TestFinished


@gui_test(use_dev_map=True, ai_players=3)
def test_ticket_1368(gui):
	"""
	Selecting a warehouse from an ai player crashes.

	Test runs faster with 3 AI players, because a new settlement is
	founded earlier. It is still pretty slow, but let's care about
	speed later.
	"""
	yield # test needs to be a generator for now

	gui.session.speed_set(GAME_SPEED.TICK_RATES[-1])

	# Wait until ai has settled down
	world = gui.session.world
	while not world.settlements:
		yield

	ai_warehouse = world.settlements[0].warehouse
	gui.select([ai_warehouse])

	yield TestFinished


@gui_test(use_fixture='ai_settlement')
def test_ticket_1369(gui):
	"""
	Ship tab closed when moving away from another player's warehouse after trading.
	"""
	yield

	ship = get_player_ship(gui.session)
	gui.select([ship])

	with gui.cursor_map_coords():
		# move ship near foreign warehouse and wait for it to arrive
		gui.cursor_click(68, 23, 'right')
		while (ship.position.x, ship.position.y) != (68, 23):
			yield

		# click trade button
		c = gui.find(name='overview_trade_ship')
		gui.trigger(c, 'trade/action/default')

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
