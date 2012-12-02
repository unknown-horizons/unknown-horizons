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

import os
import shutil

import mock

from horizons.constants import PATHS
from tests.gui import gui_test, TEST_FIXTURES_DIR


@gui_test(timeout=60, cleanup_userdir=True)
def test_load_game(gui):
	"""Test loading a game from the mainmenu."""

	savegame = 'boatbuilder.sqlite'

	# copy fixture savegame into user dir, otherwise we'll just get a 'no savegames' popup
	source = os.path.join(TEST_FIXTURES_DIR, savegame)
	target_dir = os.path.join(PATHS.USER_DIR, 'save')
	shutil.copy(source, target_dir)

	def func1():
		gui.find('savegamelist').select(u'boatbuilder')

		with mock.patch('horizons.main.start_singleplayer') as start_mock:
			gui.trigger('load_game_window', 'okButton/action/__execute__')

			# we need to run the game for a bit, because start_singleplayer isn't
			# called right away, probably because load/save is a dialog
			gui.run(1)
			options = start_mock.call_args[0][0]

			assert options.game_identifier == os.path.join(target_dir, savegame)
		
	with gui.handler(func1):
		gui.trigger('menu', 'loadgameButton')


@gui_test(timeout=60)
def test_load_game_no_savegames(gui):
	"""Trying to load a game with no save games available will show a popup."""
	def func1():
		gui.trigger('popup_window', 'okButton/action/__execute__')
		
	with gui.handler(func1):
		gui.trigger('menu', 'loadgameButton')
