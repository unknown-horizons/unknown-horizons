# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

"""This is the main game file, it used to store some global information and to handle
   the main menu, as well as to initialize new gamesessions. horizons.main provides some globals
   that can be used throughout the code just by importing 'horizons.main'. These are the
   globals:
   * db - the horizons.dbreader instance, used to retrieve data from the database.
   * settings - horizons.settings instance.
   * fife - if a game is running. horizons.fife provides the running engine instance.
   * gui - provides the currently active gui (only non ingame menus)
   * session - horizons.session instance - check game/session.py for more information
   * connection - multiplayer game connection (not used yet)
   * ext_scheduler - horizons.extscheduler instance, used for non ingame timed events.
   * savegamemanager - horizons.savegamemanager instance.

   TUTORIAL:
   Continue to horizons.session for further ingame digging.
   """

import re
import time
import os
import os.path
import glob
import shutil
import random

import engine
from util import Color, ActionSetLoader
from menus import Menus
from dbreader import DbReader
from engine import Fife
from settings import Settings
from session import Session
from gui.mainlistener import MainListener
from extscheduler import ExtScheduler
from savegamemanager import SavegameManager


def start():
	"""Starts the horizons.
	"""
	global db, settings, fife, gui, session, connection, ext_scheduler, savegamemanager, \
		   action_sets
	#init db
	db = DbReader(':memory:')
	db("attach ? AS data", 'content/game.sqlite')

	#init settings
	settings = Settings()
	settings.addCategorys('sound')
	settings.sound.setDefaults(enabled = True)
	settings.sound.setDefaults(volume_music = 1.0)
	settings.sound.setDefaults(volume_effects = 1.0)
	settings.addCategorys('network')
	settings.network.setDefaults(port = 62666, url_servers = 'http://master.unknown-horizons.org/servers', url_master = 'master.unknown-horizons.org', favorites = [])
	settings.addCategorys('savegame')
	settings.savegame.setDefaults(savedquicksaves = 10, autosaveinterval = 10, savedautosaves = 10)

	if settings.client_id is None:
		settings.client_id = "".join("-" if c in (8,13,18,23) else random.choice("0123456789abcdef") for c in xrange(0,36))

	savegamemanager = SavegameManager()

	fife = Fife()
	ext_scheduler = ExtScheduler(fife.pump)

	fife.init()
	loader = ActionSetLoader('content/gfx/')
	action_sets = loader.load()
	mainlistener = MainListener()
	connection = None
	session = None
	gui = Menus()

	gui.show_main()

	fife.run()

def quit():
	"""Quits the game"""
	global fife
	fife.cursor.set(engine.fife.CURSOR_NATIVE) #hack to get system cursor back
	fife.quit()


def start_singleplayer(map_file):
	"""Starts a singleplayer game"""
	global gui, session
	gui.show()

	fife.cursor.set(engine.fife.CURSOR_NONE)

	fife.engine.pump()

	fife.cursor.set(engine.fife.CURSOR_IMAGE, fife.default_cursor_image)

	gui.hide()

	if session is not None:
		session.end()
	session = Session()
	session.init_session()
	session.load(map_file, 'Arthur', Color()) # temp fix to display gold


def startMulti():
	"""Starts a multiplayer game server (dummy)

	This also starts the game for the game master
	"""
	pass

def save_game(savegamename):
	"""Saves a game
	@param savegamename: string with the filename or full path of the savegame file
	@return: bool, wether save was successfull
	"""
	global savegamemanager, session, gui

	if savegamename.startswith("/"):
		savegamefile = savegamename
	else:
		savegamefile = savegamemanager.create_filename(savegamename)

	if os.path.exists(savegamefile):
		if not gui.show_popup("Confirmation for overwriting",
													"A savegame with the name \"%s\" already exists. Should i overwrite it?"%savegamename,
													show_cancel_button = True):
			gui.save_game()
			return

	try:
		session.save(savegamefile)
	except IOError, e: # invalid filename
		gui.show_popup("Invalid filename", "You entered an invalid filename.")
		gui.hide()
		gui.save_game()
		return False

	return True


# NOTE: this code wasn't maintained and is broken now.
#def start_multiplayer(savegamefile):
#	"""Starts a new multiplayer game
#	@param savegamefile: sqlite database file containing the savegame
#	"""
#	global gui, fife
#	gui.show()
#	fife.engine.pump()
#
#	session = Session()
#	session.load(savegamefile)
#	returnGame()
