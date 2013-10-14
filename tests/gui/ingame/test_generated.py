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

import itertools

from tests.gui import gui_test
from tests.gui.helper import get_player_ship


@gui_test(use_dev_map=True, timeout=120)
def test_build_a_settlement(gui):
	"""
	Build a settlement. Generated with gui logger.
	"""

	ship = get_player_ship(gui.session)

	gui.select([ship])

	# Move ship
	gui.cursor_click(57, 0, 'right')

	# Wait for ship to arrive
	while (ship.position.x, ship.position.y) != (57, 0):
		gui.run()

	gui.trigger('content', 'found_settlement')

	# Place warehouse
	gui.cursor_click(56, 3, 'left')
	assert gui.session.world.settlements

	# Select buildmenu
	gui.trigger('mainhud', 'build')

	# Select fisher
	gui.trigger('content', 'button_33')

	# Place fisher
	gui.cursor_click(52, 3, 'left')

	# Select path
	gui.trigger('content', 'button_21')

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
	gui.trigger('content', 'button_03')
	gui.cursor_click(52, 6, 'left')

	# Build main square
	gui.trigger('content', 'button_02')
	gui.cursor_click(53, 11, 'left')

	# Select path
	gui.trigger('content', 'button_21')

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
	gui.trigger('content', 'button_01')
	gui.cursor_click(58, 9, 'left')

	# Build a tent
	gui.trigger('content', 'button_01')
	gui.cursor_click(58, 7, 'left')

	# Build a tent
	gui.trigger('content', 'button_01')
	gui.cursor_click(58, 5, 'left')


@gui_test(use_dev_map=True, timeout=120)
def test_buildingtool(gui):
	"""
	Trigger different buildingtool highlights
	"""

	ship = get_player_ship(gui.session)

	gui.select([ship])

	# Move ship
	gui.cursor_click(57, 0, 'right')

	# Wait for ship to arrive
	while (ship.position.x, ship.position.y) != (57, 0):
		gui.run()

	gui.trigger('content', 'found_settlement')

	def build_at(target):
		# build while moving around cursor beforehand
		OFFSETS = [ 0, 1, -1, 2, -2, 5, -5, 20, -20 ] # don't add more, takes long enough already
		for off_x, off_y in itertools.product( OFFSETS, repeat=2 ):
			# will trigger preview_build of BuildingTool
			gui.cursor_move( target[0]+off_x, target[1]+off_y )
		gui.cursor_click(target[0], target[1], 'left')

	# Place warehouse
	build_at( (56, 3) )
	assert gui.session.world.settlements

	# Select buildmenu
	gui.trigger('mainhud', 'build')

	# Select fisher
	gui.trigger('content', 'button_33')

	# Place fisher
	build_at( (52, 3) )


	# Build lumberjack
	gui.trigger('content', 'button_03')
	build_at( (52, 6) )

	# Build main square
	gui.trigger('content', 'button_02')
	build_at( (53, 11) )

	# Select path
	gui.trigger('content', 'button_21')

	# Build some paths
	for i in xrange(6, 13):
		build_at( (57, i) )
	gui.cursor_click(54, 7, 'right') # cancel

	# Build a tent
	gui.trigger('content', 'button_01')
	build_at( (58, 7) )

	# Select pavilion (tent highlights)
	gui.trigger('content', 'button_12')
	build_at( (58, 5) )

	# Build a tent (pavilion highlights)
	gui.trigger('content', 'button_01')
	build_at( (58, 9) )
