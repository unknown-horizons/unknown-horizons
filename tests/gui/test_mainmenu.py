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

from horizons.constants import PATHS
from tests.gui import TestFinished, gui_test, TEST_FIXTURES_DIR


@gui_test(timeout=60)
def test_support(gui):
	def func():
		yield
		gui.trigger('support_window', 'okButton/action/__execute__')
	
	with gui.handler(func):
		gui.trigger('menu', 'dead_link/action/default')

	yield TestFinished


@gui_test(timeout=60)
def test_credits(gui):
	def func():
		yield
		gui.trigger('credits_window', 'okButton/action/__execute__')
	
	with gui.handler(func):
		gui.trigger('menu', 'creditsLink/action/default')

	yield TestFinished


@gui_test(timeout=60)
def test_help(gui):
	def func():
		yield
		gui.trigger('help_window', 'okButton/action/__execute__')
		
	with gui.handler(func):
		gui.trigger('menu', 'helpLink/action/default')

	yield TestFinished


# NOTE doesn't work when running under xvfb (no screen resolutions detected)
"""
@gui_test(timeout=60)
def test_settings(gui):
	gui.trigger('menu', 'settingsLink/action/default')
	gui.trigger('settings_window', 'cancelButton/action/default')

	yield TestFinished
"""


@gui_test(timeout=60)
def test_multiplayer(gui):
	gui.trigger('menu', 'startMulti/action/default')
	yield # TODO find out why it fails without yield
	gui.trigger('menu', 'cancel/action/default')

	yield TestFinished


@gui_test(timeout=60)
def test_singleplayer(gui):
	gui.trigger('menu', 'startSingle/action/default')
	gui.trigger('menu', 'cancel/action/default')
	
	yield TestFinished


@gui_test(timeout=60, cleanup_userdir=True)
def test_load_game(gui):
	# copy fixture savegame into user dir, otherwise we'll just get a 'no savegames' popup
	source = os.path.join(TEST_FIXTURES_DIR, 'boatbuilder.sqlite')
	target_dir = os.path.join(PATHS.USER_DIR, 'save')
	shutil.copy(source, target_dir)

	def func():
		yield
		gui.trigger('load_game_window', 'cancelButton/action/__execute__')
		
	with gui.handler(func):
		gui.trigger('menu', 'loadgameButton/action/default')
	
	yield TestFinished
