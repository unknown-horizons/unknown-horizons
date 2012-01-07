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

from tests.gui import gui_test, TestFinished


@gui_test(use_dev_map=True)
def test_select_ship(gui):
	"""
	Select a ship.
	"""
	yield # test needs to be a generator for now

	assert gui.find('tab_base') is None

	# Find player's ship
	player_ship = None
	for ship in gui.session.world.ships:
		if ship.owner == gui.session.world.player:
			player_ship = ship
			break

	gui.select([player_ship])
	assert gui.find('overview_trade_ship')

	raise TestFinished
