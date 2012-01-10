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


def get_player_ship(session):
	for ship in session.world.ships:
		if ship.owner == session.world.player:
			return ship
	return None


@gui_test(use_dev_map=True)
def test_build_a_settlement(gui):
	"""
	Build a settlement. Generated with gui logger.
	"""
	yield # test needs to be a generator for now

	player = gui.session.world.player
	ship = get_player_ship(gui.session)

	gui.select([ship])

	with gui.cursor_map_coords():
		# Move ship
		gui.cursor_click(57, 0, 'right')

		# Wait for ship to arrive
		for i in gui.run(seconds=7): yield

		c = gui.find(name='overview_trade_ship')
		gui.trigger(c, 'found_settlement/action/default')

		# Place warehouse
		gui.cursor_click(56, 3, 'left')

		# Select buildmenu
		c = gui.find(name='mainhud')
		gui.trigger(c, 'build/action/default')

		# Select fisher
		c = gui.find(name='tab')
		gui.trigger(c, 'button_26/action/default')

		# Place fisher
		gui.cursor_click(52, 3, 'left')
		# TODO find out why we have to cancel the current operation, this does
		# not behave like normal gameplay
		gui.cursor_click(52, 3, 'right')	# cancel

		# Select path
		c = gui.find(name='tab')
		gui.trigger(c, 'button_21/action/default')

		# Build some paths
		# Has to be one by one, no mouse drag support yet
		gui.cursor_click(52, 5, 'left')
		gui.cursor_click(53, 5, 'left')
		gui.cursor_click(54, 5, 'left')
		gui.cursor_click(55, 5, 'left')
		gui.cursor_click(56, 5, 'left')
		gui.cursor_click(57, 5, 'left')
		gui.cursor_click(54, 7, 'right')	# cancel

		# Build lumberjack
		c = gui.find(name='tab')
		gui.trigger(c, 'button_5/action/default')

		gui.cursor_click(52, 6, 'left')
		gui.cursor_click(52, 6, 'right')	# cancel

		# Build main square
		c = gui.find(name='tab')
		gui.trigger(c, 'button_3/action/default')

		gui.cursor_click(53, 11, 'left')
		gui.cursor_click(53, 11, 'right')	# cancel

		# Select path
		c = gui.find(name='tab')
		gui.trigger(c, 'button_21/action/default')

		# Build some paths
		gui.cursor_click(57, 6, 'left')
		gui.cursor_click(57, 7, 'left')
		gui.cursor_click(57, 8, 'left')
		gui.cursor_click(57, 9, 'left')
		gui.cursor_click(57, 10, 'left')
		gui.cursor_click(57, 11, 'left')
		gui.cursor_click(57, 12, 'left')
		gui.cursor_click(57, 13, 'right')	# cancel

		# Build a tent
		c = gui.find(name='tab')
		gui.trigger(c, 'button_1/action/default')

		gui.cursor_click(58, 9, 'left')
		gui.cursor_click(58, 9, 'right')	# cancel

		# Build a tent
		c = gui.find(name='tab')
		gui.trigger(c, 'button_1/action/default')

		gui.cursor_click(58, 7, 'left')
		gui.cursor_click(58, 7, 'right')	# cancel

		# Build a tent
		c = gui.find(name='tab')
		gui.trigger(c, 'button_1/action/default')

		gui.cursor_click(58, 5, 'left')
		gui.cursor_click(58, 5, 'right')	# cancel

	yield TestFinished
