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

from tests.gui import TestFinished, gui_test


@gui_test
def test_example(gui):
	"""
	Begins in main menu, starts a new single player game, checks the gold display,
	opens the game menu and cancels the game.
	"""
	yield # test needs to be a generator for now

	# Main menu
	main_menu = gui.find(name='menu')
	gui.trigger(main_menu, 'startSingle/action/default')

	# Single-player menu
	assert len(gui.active_widgets) == 1
	singleplayer_menu = gui.active_widgets[0]
	gui.trigger(singleplayer_menu, 'okay/action/default') # start a game

	# Hopefully we're ingame now
	assert len(gui.active_widgets) == 4
	gold_display = gui.find(name='status_gold')
	assert gold_display.findChild(name='gold_1').text == '30000'

	# Open game menu
	hud = gui.find(name='mainhud')
	gui.trigger(hud, 'gameMenuButton/action/default')
	game_menu = gui.find(name='menu')

	# Cancel current game
	def dialog():
		yield
		popup = gui.find(name='popup_window')
		gui.trigger(popup, 'okButton/action/__execute__')

	with gui.handler(dialog):
		gui.trigger(game_menu, 'quit/action/default')

	# Back at the main menu
	assert gui.find(name='menu')

	raise TestFinished
