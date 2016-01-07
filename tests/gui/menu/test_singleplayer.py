# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

import mock

from tests.gui import gui_test


@gui_test()
def test_show_menu(gui):
	"""Test that the singleplayer page shows up and closes correctly."""
	gui.trigger('menu', 'single_button')
	gui.trigger('singleplayermenu', 'cancel')


def _start_game(gui):
	"""Starts the game from the menu and returns the game options used."""
	with mock.patch('horizons.main.start_singleplayer') as start_mock:
		gui.trigger('singleplayermenu', 'okay')

		return start_mock.call_args[0][0]


@gui_test()
def test_start_scenario(gui):
	"""Test starting a scenario."""
	gui.trigger('menu', 'single_button')
	gui.trigger('singleplayermenu', 'scenario')

	# trigger update of scenario infos
	gui.find('maplist').select('tutorial')
	gui.find('uni_langlist').select('English')

	options = _start_game(gui)
	assert options.is_scenario
	assert options.game_identifier.endswith('tutorial_en.yaml')


@gui_test()
def test_start_random_map(gui):
	"""Test starting a new random map."""
	gui.trigger('menu', 'single_button')
	gui.trigger('singleplayermenu', 'random')

	# disable pirates and disasters
	gui.trigger('singleplayermenu', 'lbl_pirates')
	gui.trigger('singleplayermenu', 'lbl_disasters')

	gui.find('ai_players').select('3')
	gui.find('resource_density_slider').slide(4)

	options = _start_game(gui)
	assert not options.is_scenario
	assert not options.pirate_enabled
	assert not options.disasters_enabled
	assert options.trader_enabled
	assert options.ai_players == 3
	assert options.natural_resource_multiplier == 2


@gui_test()
def test_start_map(gui):
	"""Test starting an existing map."""
	gui.trigger('menu', 'single_button')
	gui.trigger('singleplayermenu', 'free_maps')

	# trigger update of map info
	gui.find('maplist').select('development')

	gui.find('ai_players').select('1')

	# disable pirates and trader
	gui.trigger('singleplayermenu', 'lbl_pirates')
	gui.trigger('singleplayermenu', 'lbl_free_trader')

	options = _start_game(gui)
	assert options.game_identifier.endswith('development.sqlite')
	assert not options.is_scenario
	assert not options.pirate_enabled
	assert not options.trader_enabled
	assert options.disasters_enabled
	assert options.ai_players == 1
