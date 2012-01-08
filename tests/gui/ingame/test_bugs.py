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
from tests.gui import TestFinished, gui_test


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
		gui.cursor_press_button(x, y, 'left')
		gui.cursor_release_button(x, y, 'left')
	"""

	gui.select([ship])

	yield TestFinished
