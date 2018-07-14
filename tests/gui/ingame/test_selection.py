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

from horizons.command.unit import CreateUnit
from horizons.constants import UNITS
from tests.gui import gui_test
from tests.gui.helper import get_player_ship


@gui_test(use_dev_map=True, timeout=60)
def test_select_ship(gui):
	"""
	Select a ship.
	"""

	assert gui.find('overview_trade_ship')

	gui.press_key(gui.Key.NUM_0)
	assert gui.find('tab_base') is None

	# Find player's ship
	player_ship = get_player_ship(gui.session)

	gui.select([player_ship])
	assert gui.find('overview_trade_ship')


@gui_test(use_dev_map=True, timeout=60)
def test_selectmultitab(gui):
	"""
	Select two frigates and delete them.
	"""

	gui.press_key(gui.Key.NUM_0)
	assert gui.find('tab_base') is None

	player = gui.session.world.player
	def create_ship(type):
		position = gui.session.world.get_random_possible_ship_position()
		unit = CreateUnit(player.worldid, type, *position.to_tuple())(issuer=player)
		gui.run(seconds=0.1)
		return unit

	ships = [create_ship(UNITS.FRIGATE), create_ship(UNITS.FRIGATE)]
	gui.select(ships)
	assert gui.find('overview_select_multi')
	gui.run(seconds=0.1)

	def func():
		assert gui.find('popup_window') is not None
		gui.trigger('popup_window/okButton')

	with gui.handler(func):
		gui.press_key(gui.Key.DELETE)

	assert gui.find('tab_base') is None
	gui.run(seconds=0.1)


@gui_test(use_fixture='plain', timeout=120)
def test_selection_groups(gui):
	"""Check group selection using ctrl-NUM"""

	# Starting a new game assigns player ship to group 1
	ship = get_player_ship(gui.session)
	assert gui.session.selected_instances == {ship}

	gui.select([ship])

	# make first group
	gui.press_key(gui.Key.NUM_2, ctrl=True)

	gui.select([])
	assert not gui.session.selected_instances

	# check group
	gui.press_key(gui.Key.NUM_2)
	assert next(iter(gui.session.selected_instances)) is ship

	gui.cursor_click(59, 1, 'right')
	while (ship.position.x, ship.position.y) != (59, 1):
		gui.run()

	# Found settlement
	gui.trigger('overview_trade_ship/found_settlement')

	gui.cursor_click(56, 3, 'left')

	gui.trigger('mainhud/build')

	wh = gui.session.world.player.settlements[0].warehouse

	gui.select([wh])
	gui.press_key(gui.Key.NUM_3, ctrl=True)

	# check group again
	gui.press_key(gui.Key.NUM_2)
	assert len(gui.session.selected_instances) == 1
	assert next(iter(gui.session.selected_instances)) is ship

	# now other one
	gui.press_key(gui.Key.NUM_3)
	assert len(gui.session.selected_instances) == 1
	assert next(iter(gui.session.selected_instances)) is wh

	# check group still once again
	gui.press_key(gui.Key.NUM_2)
	assert len(gui.session.selected_instances) == 1
	assert next(iter(gui.session.selected_instances)) is ship

	# no group
	gui.press_key(gui.Key.NUM_0)
	assert not gui.session.selected_instances
