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

from tests.gui import gui_test
from tests.gui.helper import found_settlement


@gui_test(use_dev_map=True)
def test_tearing(gui):
	found_settlement(gui, (11, 1), (11, 6))

	# remove some trees
	gui.trigger('mainhud/destroy_tool')
	gui.cursor_drag((5, 7), (11, 16), 'left')

	# build 4 tents
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_01')
	gui.cursor_drag((7, 9), (10, 12), 'left')

	# try to remove an area that includes the tents, some trees and
	# the warehouse
	gui.trigger('mainhud/destroy_tool')
	gui.cursor_drag((5, 15), (15, 3), 'left')


@gui_test(use_dev_map=True)
def test_pipette(gui):
	found_settlement(gui, (11, 1), (11, 6))

	# select mountain, can not be build
	gui.press_key(gui.Key.O)
	gui.cursor_click(6, 18, 'left')
	assert not gui.find('place_building')

	# build signal fire
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_22')
	gui.cursor_click(7, 7, 'left')

	# activate pipette, select signal fire, place it next to the other
	gui.press_key(gui.Key.O)
	gui.cursor_click(7, 7, 'left')
	gui.cursor_click(6, 7, 'left')

	# select signal fire, check if it's actually there
	gui.cursor_click(6, 7, 'left')
	assert gui.find('overview_signalfire')
