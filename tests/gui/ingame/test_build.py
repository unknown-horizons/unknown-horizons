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
from horizons.constants import GAME_SPEED
from horizons.gui.mousetools.buildingtool import BuildingTool 
from horizons.gui.mousetools.cursortool import CursorTool
from tests.gui import TestFinished, gui_test


def get_player_ship(session):
	for ship in session.world.ships:
		if ship.owner == session.world.player:
			return ship
	return None


@gui_test(use_dev_map=True)
def test_found_settlement(gui):
	"""
	Found a settlement.
	"""
	yield # test needs to be a generator for now

	player = gui.session.world.player
	target = (68, 10)
	gui.session.view.center(*target)

	assert len(player.settlements) == 0

	ship = get_player_ship(gui.session)
	Act(ship, *target)(player)

	# wait until ship arrives
	# FIXME speed game up, don't want to wait too long for the ship
	gui.session.speed_set(GAME_SPEED.TICK_RATES[-1])
	while (ship.position.x, ship.position.y) != target:
		yield
	gui.session.speed_set(GAME_SPEED.TICK_RATES[0])

	gui.select([ship])
	c = gui.find(name='overview_trade_ship')
	gui.trigger(c, 'found_settlement/action/default')

	assert isinstance(gui.cursor, BuildingTool)
	with gui.cursor_map_coords():
		gui.cursor_move(64, 12)
		gui.cursor_click(64, 12, 'left')

	assert isinstance(gui.cursor, CursorTool)
	assert len(player.settlements) == 1

	yield TestFinished
