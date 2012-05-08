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
from horizons.constants import UNITS
from tests.gui.helper import get_player_ship

from tests.gui import gui_test, TestFinished

@gui_test(use_dev_map=True, timeout=60)
def test_select_ship(gui):
	"""
	Select a ship.
	"""
	yield # test needs to be a generator for now

	assert gui.find('tab_base') is None

	# Find player's ship
	player_ship = get_player_ship(gui.session)

	gui.select([player_ship])
	assert gui.find('overview_trade_ship')

	yield TestFinished

@gui_test(use_dev_map=True, timeout=60)
def test_selectmultitab(gui):
	"""
	Select two frigates and delete them.
	"""
	yield # test needs to be a generator for now

	assert gui.find('tab_base') is None

	player = gui.session.world.player
	def create_ship(type):
		return CreateUnit(player.worldid, type, *gui.session.world.get_random_possible_ship_position().to_tuple())(issuer=player)

	ships = [create_ship(UNITS.FRIGATE), create_ship(UNITS.FRIGATE)]
	gui.select(ships)
	assert gui.find('overview_select_multi')
	for _ in gui.run(seconds=0.1):
		yield

	gui.press_key(gui.Key.DELETE)
	assert gui.find('tab_base') is None
	for _ in gui.run(seconds=0.1):
		yield

	yield TestFinished


@gui_test(use_dev_map=True, timeout=120)
def test_selection_groups(gui):
	"""Check group selection using ctrl-NUM"""
	ship = get_player_ship(gui.session)
	gui.select([ship])

	# make first group
	gui.press_key(gui.Key.NUM_1, ctrl=True)

	gui.select( [] )
	assert len(gui.session.selected_instances) == 0

	# check group
	gui.press_key(gui.Key.NUM_1)
	assert iter(gui.session.selected_instances).next() is ship

	gui.cursor_click(59, 1, 'right')
	while (ship.position.x, ship.position.y) != (59, 1):
		yield

	# Found settlement
	gui.trigger('overview_trade_ship', 'found_settlement/action/default')

	gui.cursor_click(56, 3, 'left')

	gui.trigger('mainhud', 'build/action/default')

	wh = gui.session.world.player.settlements[0].warehouse

	gui.select( [wh] )
	gui.press_key(gui.Key.NUM_2, ctrl=True)

	# check group again
	gui.press_key(gui.Key.NUM_1)
	assert len(gui.session.selected_instances) == 1 and \
	       iter(gui.session.selected_instances).next() is ship

	# now other one
	gui.press_key(gui.Key.NUM_2)
	assert len(gui.session.selected_instances) == 1 and \
	       iter(gui.session.selected_instances).next() is wh

	# check group still once again
	gui.press_key(gui.Key.NUM_1)
	assert len(gui.session.selected_instances) == 1 and \
	       iter(gui.session.selected_instances).next() is ship

	# no group
	gui.press_key(gui.Key.NUM_3)
	assert len(gui.session.selected_instances) == 0

	yield TestFinished
