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

import os

from horizons.constants import EDITOR, GROUND, PATHS
from tests.gui import gui_test
from tests.utils import mark_flaky

editor_test = gui_test(additional_cmdline=["--edit-map", "development"])


@editor_test
def test_place_tiles(gui):
	"""Place different tiles with different tile sizes."""

	gui.trigger('editor_settings/water')
	gui.cursor_click(27, 36, 'left')
	gui.cursor_click(27, 37, 'left')
	gui.cursor_click(27, 38, 'left')

	gui.trigger('editor_settings/size_2')
	gui.trigger('editor_settings/sand')
	gui.cursor_click(34, 34, 'left')

	gui.trigger('editor_settings/size_3')
	gui.trigger('editor_settings/default_land')
	gui.cursor_click(34, 27, 'left')

	# Map edge and largest brush size
	gui.trigger('editor_settings/size_{}'.format(EDITOR.MAX_BRUSH_SIZE))
	gui.cursor_click(-8, 78, 'left')


@editor_test
def test_save_map(gui):
	"""Save a map in the editor."""

	# FIXME escape doesn't work
	#gui.press_key(gui.Key.ESCAPE)
	gui.trigger('mainhud/gameMenuButton')

	def func1():
		gui.find('savegamefile').write('test_map')
		gui.trigger('load_game_window/okButton')

	with gui.handler(func1):
		gui.trigger('menu/button_images/savegameButton')

	assert os.path.exists(os.path.join(PATHS.USER_MAPS_DIR, "test_map.sqlite"))


@editor_test
def test_drag_mouse(gui):
	"""Test that tiles are placed while dragging the mouse."""
	# TODO This is a really simple demonstration of mouse drag support in tests.
	# TODO We should add better tests to show that the tile algorithm really works.

	gui.trigger('editor_settings/water')
	gui.cursor_drag((30, 30), (30, 37), 'left')

	# quick check if the mouse drag had any effect on the map
	for y in range(30, 36):
		tile = gui.session.world.full_map[(30, y)]
		assert (tile.id, tile.shape, tile.rotation + 45) == GROUND.DEEP_WATER_SOUTH
