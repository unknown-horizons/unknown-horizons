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
from tests.utils import mark_flaky


@mark_flaky
@gui_test(use_dev_map=True, timeout=60)
def test_settings_dialog_crash(gui):
	"""Opening&closing the settings dialog in two different games crashes."""

	# open pause menu
	gui.trigger('mainhud/gameMenuButton')

	# open & close settings
	gui.trigger('menu/settingsLink')
	gui.trigger('settings_window/okButton')

	# open pause menu, quit session
	def func1():
		gui.trigger('popup_window/okButton')

	with gui.handler(func1):
		gui.trigger('menu/closeButton')

	# start a new game (development map)
	gui.trigger('menu/single_button')
	gui.trigger('singleplayermenu/free_maps')
	gui.find('maplist').select('development')
	gui.trigger('singleplayermenu/okay')

	# open pause menu
	gui.trigger('mainhud/gameMenuButton')

	# open & close settings
	gui.trigger('menu/settingsLink')
	gui.trigger('settings_window/okButton')  # this crashes


@gui_test(timeout=60)
def test_settings_dialog_crash2(gui):
	# open settings in main menu
	gui.trigger('menu/settings_button')
	gui.trigger('settings_window/cancelButton')

	# start game
	gui.trigger('menu/single_button')
	gui.trigger('singleplayermenu/free_maps')
	gui.trigger('singleplayermenu/okay')

	gui.press_key(gui.Key.ESCAPE)
	# open & close settings
	gui.trigger('menu/settingsLink')
	gui.press_key(gui.Key.ESCAPE)
