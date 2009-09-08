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
   the main menu, as well as to initialize new gamesessions.
	 <deprecated>horizons.main provides some globals
   that can be used throughout the code just by importing 'horizons.main'. These are the
   globals:</deprecated>. Use getters now! (see below)
   * db - the horizons.dbreader instance, used to retrieve data from the database.
   * settings - horizons.settings instance.
   * fife - if a game is running. horizons.fife provides the running engine instance.
   * gui - provides the currently active gui (only non ingame menus)
   * session - horizons.session instance - check horizons/session.py for more information
   * connection - multiplayer game connection (not used yet)
   * ext_scheduler - horizons.extscheduler instance, used for non ingame timed events.

   TUTORIAL:
   Continue to horizons.session for further ingame digging.
   """

import os
import os.path
import random

import fife as fife_module

from util import Color, ActionSetLoader, DbReader
from savegamemanager import SavegameManager
from i18n import update_all_translations

## GETTERS

def get_world():
	return _modules.session.world

def get_db():
	return _modules.db

def get_view():
	return _modules.session.view

def get_ingame_gui():
	return _modules.session.ingame_gui

def get_gui():
	global gui
	return gui

##
class Modules(object):
	db = None
	settings = None
	connection = None
	mainlistener = None

_modules = Modules()

def start(command_line_arguments):
	"""Starts the horizons.
	@param command_line_arguments: options object from optparse.OptionParser. see run_uh.py.
	"""
	global gui, fife, db, session, connection, ext_scheduler, settings, \
	       unstable_features, debug

	from horizons.gui import Gui
	from engine import Fife
	from horizons.gui.keylisteners import MainListener
	from extscheduler import ExtScheduler
	from settings import Settings

	# set commandline globals
	debug = command_line_arguments.debug
	unstable_features = command_line_arguments.unstable_features

	#init db
	db = DbReader(':memory:')
	db("attach ? AS data", 'content/game.sqlite')
	db("attach ? AS settler", 'content/settler.sqlite')
	_modules.db = db

	#init settings
	settings = Settings(db)
	settings.set_defaults()

	# init gettext
	_init_gettext(settings)

	# create client_id if necessary
	if settings.client_id is None:
		settings.client_id = "".join("-" if c in (8, 13, 18, 23) else random.choice("0123456789abcdef") for c in xrange(0, 36))

	# init game parts
	fife = Fife()
	ExtScheduler.create_instance(fife.pump)
	fife.init()
	ActionSetLoader.load('content/gfx/')
	_modules.mainlistener = MainListener()
	gui = Gui()
	SavegameManager.init()
	session = None

	# start something according to commandline parameters
	if command_line_arguments.start_dev_map:
		_start_dev_map()
	elif command_line_arguments.start_map is not None:
		_start_map(command_line_arguments.start_map)
	elif command_line_arguments.load_map is not None:
		_load_map(command_line_arguments.load_map)
	elif command_line_arguments.load_quicksave is not None:
		_load_last_quicksave()
	else: # no commandline parameter, show main screen
		gui.show_main()

	fife.run()

def quit():
	"""Quits the game"""
	global fife
	fife.quit()

def start_singleplayer(map_file):
	"""Starts a singleplayer game"""
	global session, gui, fife
	gui.show()

	# remove cursor while loading
	fife.cursor.set(fife_module.CURSOR_NONE)
	fife.engine.pump()
	fife.cursor.set(fife_module.CURSOR_IMAGE, fife.default_cursor_image)

	gui.hide()

	if session is not None:
		session.end()
	from session import Session
	session = Session(gui)
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
	@return: bool, whether save was successfull
	"""
	global gui, session
	if os.path.isabs(savegamename):
		savegamefile = savegamename
	else: # is just basename
		savegamefile = SavegameManager.create_filename(savegamename)

	if os.path.exists(savegamefile):
		if not gui.show_popup(_("Confirmation for overwriting"),
				_("A savegame with the name \"%s\" already exists. Should i overwrite it?") % \
		    savegamename, show_cancel_button = True):
			gui.save_game() # just reshow save screen on cancel.
			return

	try:
		session.save(savegamefile)
	except IOError: # invalid filename
		gui.show_popup(_("Invalid filename"), _("You entered an invalid filename."))
		gui.hide()
		gui.save_game() # re-show dialog
		return False

	return True


def _set_default_settings(settings):
	settings.addCategories('sound')
	settings.sound.setDefaults(enabled = True)
	settings.sound.setDefaults(volume_music = 0.2)
	settings.sound.setDefaults(volume_effects = 0.5)
	settings.addCategories('network')
	settings.network.setDefaults(port = 62666, url_servers = 'http://master.unknown-horizons.org/servers', url_master = 'master.unknown-horizons.org', favorites = [])
	settings.addCategories('language')
	settings.language.setDefaults(position='po', name='')
	settings.addCategories('savegame')
	settings.savegame.setDefaults(savedquicksaves = 10, autosaveinterval = 10, savedautosaves = 10)


def _init_gettext(settings):
	from gettext import translation, install
	if settings.language.name != '':
		try:
			trans = translation('unknownhorizons', settings.language.position, languages=[settings.language.name])
			trans.install(unicode=1)
		except IOError:
			print _("Configured language %(lang)s at %(place)s could not be loaded") % {'lang': settings.language.name, 'place': settings.language.position}
			install('unknownhorizons', 'po', unicode=1)
			settings.language.name = ''
	else:
		install('unknownhorizons', 'po', unicode=1)
	update_all_translations()



## GAME START FUNCTIONS

def _start_dev_map():
	# start the development map (it's the first one)
	first_map = get_gui().get_maps()[0][1]
	gui.load_game(first_map)

def _start_map(map_name):
	# start a map specified by user
	maps = get_gui().get_maps()
	try:
		map_id = maps[1].index(map_name)
		get_gui().load_game(maps[0][map_id])
	except ValueError:
		print "Error: Cannot find map \"%s\"." % map_name
		import sys; sys.exit(1)

def _load_map(savegamename):
	# load a game specified by user
	saves = SavegameManager.get_saves()
	try:
		save_id = saves[1].index(savegamename)
		get_gui().load_game(saves[0][save_id])
	except ValueError:
		print "Error: Cannot find savegame \"%s\"." % savegamename
		import sys; sys.exit(1)

def _load_last_quicksave():
	# load last quicksave
	save_files = SavegameManager.get_quicksaves()[0]
	save = save_files[len(save_files)-1]
	get_gui().load_game(save)
