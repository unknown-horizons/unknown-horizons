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
import shutil
from unittest import mock

from horizons.savegamemanager import SavegameManager
from tests.gui import TEST_FIXTURES_DIR, gui_test


def _copy_savegame(filename='boatbuilder'):
	"""Copy fixture savegame into user dir."""
	source = os.path.join(TEST_FIXTURES_DIR, filename + '.sqlite')
	shutil.copy(source, SavegameManager.savegame_dir)


@gui_test(timeout=60, cleanup_userdir=True)
def test_load_game(gui):
	"""Test loading a game from the mainmenu."""

	# need to put a savegame otherwise we just get an error popup
	_copy_savegame()

	def func1():
		gui.find('savegamelist').select('boatbuilder')

		with mock.patch('horizons.main.start_singleplayer') as start_mock:
			gui.trigger('load_game_window/okButton')

			# we need to run the game for a bit, because start_singleplayer isn't
			# called right away, probably because load/save is a dialog
			gui.run(1)
			options = start_mock.call_args[0][0]

			assert options.game_identifier == SavegameManager.create_filename('boatbuilder')

	with gui.handler(func1):
		gui.trigger('menu/load_button')


@gui_test(timeout=60)
def test_load_game_no_savegames(gui):
	"""Trying to load a game with no save games available will show a popup."""
	def func1():
		gui.trigger('popup_window/okButton')

	with gui.handler(func1):
		gui.trigger('menu/load_button')


@gui_test(timeout=60, use_dev_map=True, cleanup_userdir=True)
def test_save_game_new_file(gui):
	"""Test saving a game."""

	# FIXME escape doesn't work
	#gui.press_key(gui.Key.ESCAPE)
	gui.trigger('mainhud/gameMenuButton')

	def func1():
		gui.find('savegamefile').write('testsave')
		gui.trigger('load_game_window/okButton')

	with gui.handler(func1):
		gui.trigger('menu/button_images/savegameButton')

	assert os.path.exists(SavegameManager.create_filename('testsave'))


@gui_test(timeout=60, use_dev_map=True, cleanup_userdir=True)
def test_save_game_override(gui):
	"""Test saving a game."""

	_copy_savegame()
	old_size = os.path.getsize(SavegameManager.create_filename('boatbuilder'))

	# FIXME escape doesn't work
	#gui.press_key(gui.Key.ESCAPE)
	gui.trigger('mainhud/gameMenuButton')

	def func1():
		gui.find('savegamelist').select('boatbuilder')

		# handle "do you want to override file" popup
		def func2():
			gui.trigger('popup_window/okButton')

		with gui.handler(func2):
			gui.trigger('load_game_window/okButton')

	with gui.handler(func1):
		gui.trigger('menu/button_images/savegameButton')

	assert os.path.exists(SavegameManager.create_filename('boatbuilder'))
	new_size = os.path.getsize(SavegameManager.create_filename('boatbuilder'))
	assert old_size != new_size


@gui_test(timeout=60, cleanup_userdir=True)
def test_delete_game(gui):
	"""Test deleting a savegame."""

	_copy_savegame('boatbuilder')
	_copy_savegame('ai_settlement')
	assert os.path.exists(SavegameManager.create_filename('boatbuilder'))
	assert os.path.exists(SavegameManager.create_filename('ai_settlement'))

	def confirm_deletion():
		def close_dialog():
			gui.trigger('load_game_window/cancelButton')

		with gui.handler(close_dialog):
			gui.trigger('popup_window/okButton')

	def func1():
		gui.find('savegamelist').select('boatbuilder')

		with gui.handler(confirm_deletion):
			gui.trigger('load_game_window/deleteButton')

	with gui.handler(func1):
		gui.trigger('menu/load_button')

	assert not os.path.exists(SavegameManager.create_filename('boatbuilder'))
	assert os.path.exists(SavegameManager.create_filename('ai_settlement'))


@gui_test(timeout=60, cleanup_userdir=True)
def test_delete_game_abort(gui):
	"""Try to delete a game, but abort when ask for confirmation."""

	_copy_savegame('boatbuilder')
	assert os.path.exists(SavegameManager.create_filename('boatbuilder'))

	def confirm_deletion():
		def close_dialog():
			gui.trigger('load_game_window/cancelButton')

		with gui.handler(close_dialog):
			gui.trigger('popup_window/cancelButton')

	def func1():
		gui.find('savegamelist').select('boatbuilder')

		with gui.handler(confirm_deletion):
			gui.trigger('load_game_window/deleteButton')

	with gui.handler(func1):
		gui.trigger('menu/load_button')

	assert os.path.exists(SavegameManager.create_filename('boatbuilder'))
