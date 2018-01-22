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

import functools
import os
import subprocess
import sys

import pytest

from horizons.network import enet
from horizons.network.networkinterface import NetworkInterface
from tests.gui import gui_test

pytestmark = pytest.mark.skipif(enet is None, reason='No enet bindings available')


@pytest.fixture(autouse=True)
def master_server():
	"""
	Start our own master server for the multiplayer test because the official one is probably
	too old.
	"""
	args = [sys.executable, "run_server.py", "-p", "2002", "localhost"]
	process = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
	yield
	process.terminate()


mpmenu_test = functools.partial(gui_test, additional_cmdline=["--mp-master", "localhost:2002"])


@mpmenu_test()
def test_show_menu(gui):
	"""Test that the multiplayer page shows up and closes correctly."""
	gui.trigger('menu/multi_button')
	gui.trigger('multiplayermenu/cancel')


@mpmenu_test()
def test_games_list(gui):
	"""Test refreshing of active games list."""
	# TODO add some games so this test does something more useful

	gui.trigger('menu/multi_button')

	gui.trigger('multiplayermenu/refresh')


@mpmenu_test()
def test_create_game(gui):
	"""Create a game, join the lobby, change player details, send chat message."""
	gui.trigger('menu/multi_button')

	games = NetworkInterface().get_active_games()
	assert len(games) == 0

	# create a game and enter lobby
	gui.trigger('multiplayermenu/create')
	gui.find('maplist').select('quattro')
	gui.find('playerlimit').select(2)
	gui.trigger('multiplayer_creategame/create')

	games = NetworkInterface().get_active_games()
	assert len(games) == 1

	# send a chat message
	gui.find('chatTextField').write('Text').enter()

	# change player color (click on color)
	gui.trigger('multiplayer_gamelobby/pcolor_' + NetworkInterface().get_client_name())
	gui.trigger('set_player_details_dialog_window/cyan')
	gui.trigger('set_player_details_dialog_window/okButton')

	gui.run(1)
	# change player name (click on name)
	gui.trigger('multiplayer_gamelobby/pname_' + NetworkInterface().get_client_name())
	gui.find('set_player_details_dialog_window/playername').write('Darkwing')
	gui.trigger('set_player_details_dialog_window/okButton')

	# run some time to wait for the server's acknowledgment of the new name
	gui.run(2)
	assert NetworkInterface().get_client_name() == 'Darkwing'

	gui.trigger('multiplayer_gamelobby/cancel')

	games = NetworkInterface().get_active_games()
	assert len(games) == 0
