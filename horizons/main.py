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
   * session - horizons.session instance - check horizons/session.py for more information
   * connection - multiplayer game connection (not used yet)
   * ext_scheduler - horizons.extscheduler instance, used for non ingame timed events.
   * savegamemanager - horizons.savegamemanager instance.

   TUTORIAL:
   Continue to horizons.session for further ingame digging.
   """

import os
import os.path
import logging
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
from i18n import update_all_translations

def start(command_line_arguments):
	"""Starts the horizons.
	@param command_line_arguments: options object from optparse.OptionParser
									start_dev_map: (bool), if True, don't show menu but start the development map
									load_quicksave: (bool), if True, load the latest quicksave
									start_map: (string), start map with specified map name
									load_map: (string), load map with specified savegamename
									unstable_features: (bool), wether unstable features should be enabled
									debug: (bool), wether to enable debug messages
	"""
	global db, settings, fife, gui, session, connection, ext_scheduler, savegamemanager, \
		   action_sets, unstable_features, debug

	# set debugging level
	debug = command_line_arguments.debug

	#init db
	db = DbReader(':memory:')
	db("attach ? AS data", 'content/game.sqlite')
	db("attach ? AS settler", 'content/settler.sqlite')

	#init settings
	settings = Settings()
	settings.addCategorys('sound')
	settings.sound.setDefaults(enabled = True)
	settings.sound.setDefaults(volume_music = 0.2)
	settings.sound.setDefaults(volume_effects = 0.5)
	settings.addCategorys('network')
	settings.network.setDefaults(port = 62666, url_servers = 'http://master.unknown-horizons.org/servers', url_master = 'master.unknown-horizons.org', favorites = [])
	settings.addCategorys('language')
	settings.language.setDefaults(position='po', name='')
	settings.addCategorys('savegame')
	settings.savegame.setDefaults(savedquicksaves = 10, autosaveinterval = 10, savedautosaves = 10)

	# init gettext
	from gettext import translation, install
	if settings.language.name != '':
		trans = translation('unknownhorizons', settings.language.position, languages=[settings.language.name])
		trans.install(unicode=1)
	else:
		install('unknownhorizons', 'po', unicode=1)
	update_all_translations()

	# create client_id if necessary
	if settings.client_id is None:
		settings.client_id = "".join("-" if c in (8, 13, 18, 23) else random.choice("0123456789abcdef") for c in xrange(0, 36))


	# init game parts
	fife = Fife()
	ext_scheduler = ExtScheduler(fife.pump)
	fife.init()
	loader = ActionSetLoader('content/gfx/')
	action_sets = loader.load()
	mainlistener = MainListener()
	connection = None
	session = None
	savegamemanager = SavegameManager()
	gui = Menus()

	# parse command line:

	# set flag wether to enable unstable features
	unstable_features = command_line_arguments.unstable_features

	# start something according to commandline parameters
	if command_line_arguments.start_dev_map:
		# start the development map (it's the first one)
		first_map = gui.get_maps()[0][1]
		gui.load_game(first_map)
	elif command_line_arguments.start_map is not None:
		# start a map specified by user
		map_name = command_line_arguments.start_map
		maps = gui.get_maps()
		try:
			map_id = maps[1].index(map_name)
			gui.load_game(maps[0][map_id])
		except ValueError:
			print "Error: Cannot find map \"%s\"." % map_name
			import sys; sys.exit(1)
	elif command_line_arguments.load_map is not None:
		# load a game specified by user
		savegamename = command_line_arguments.load_map
		saves = savegamemanager.get_saves()
		try:
			save_id = saves[1].index(savegamename)
			gui.load_game(saves[0][save_id])
		except ValueError:
			print "Error: Cannot find savegame \"%s\"." % savegamename
			import sys; sys.exit(1)
	elif command_line_arguments.load_quicksave is not None:
		# load last quicksave
		save_files = savegamemanager.get_quicksaves()[0]
		save = save_files[len(save_files)-1]
		gui.load_game(save)


	else: # no commandline parameter, show main screen
		gui.show_main()

	fife.run()

def quit():
	"""Quits the game"""
	global fife
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


def start_multi():
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

	if os.path.isabs(savegamename):
		savegamefile = savegamename
	else: # is just basename
		savegamefile = savegamemanager.create_filename(savegamename)

	if os.path.exists(savegamefile):
		if not gui.show_popup(_("Confirmation for overwriting"),
				_("A savegame with the name \"%s\" already exists."+\
				"Should i overwrite it?")%savegamename,
				show_cancel_button = True):
			gui.save_game() # just reshow save screen on cancel.
			return

	try:
		session.save(savegamefile)
	except IOError: # invalid filename
		gui.show_popup(_("Invalid filename"), _("You entered an invalid filename."))
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
