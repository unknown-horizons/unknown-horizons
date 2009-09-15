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
   globals:</deprecated>.
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
import threading

import fife as fife_module

from util import Color, ActionSetLoader, DbReader
from savegamemanager import SavegameManager
from i18n import update_all_translations
from horizons.gui import Gui

# private module pointers of this module
class Modules(object):
	gui = None
_modules = Modules()

def start(command_line_arguments):
	"""Starts the horizons.
	@param command_line_arguments: options object from optparse.OptionParser. see run_uh.py.
	"""
	global fife, db, session, connection, ext_scheduler, settings, \
	       unstable_features, debug, preloading

	from engine import Fife
	from extscheduler import ExtScheduler
	from settings import Settings

	# set commandline globals
	debug = command_line_arguments.debug
	unstable_features = command_line_arguments.unstable_features

	#init db
	db = _create_db()

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
	_modules.gui = Gui()
	SavegameManager.init()
	session = None

	# for preloading game data while in main screen
	preload_lock = threading.Lock()
	preload_thread = threading.Thread(target=preload_game_data, args=(preload_lock,))
	preloading = (preload_thread, preload_lock)

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
		_modules.gui.show_main()
		preloading[0].start()

	fife.run()

def quit():
	"""Quits the game"""
	global fife
	fife.quit()

def start_singleplayer(map_file, game_data={}):
	"""Starts a singleplayer game
	@param map_file: path to map file
	@param game_data: dict, contains data about the game (playername, etc.)"""
	global session, fife, preloading, db
	_modules.gui.show()

	# lock preloading
	preloading[1].acquire()
	# wait until it finished it's current action
	if preloading[0].isAlive():
		preloading[0].join()
		assert not preloading[0].isAlive()
	else:
		preloading[1].release()

	# remove cursor while loading
	fife.cursor.set(fife_module.CURSOR_NONE)
	fife.engine.pump()
	fife.cursor.set(fife_module.CURSOR_IMAGE, fife.default_cursor_image)

	_modules.gui.hide()

	if session is not None:
		session.end()
	from session import Session
	session = Session(_modules.gui, db)
	session.init_session()
	if ('playername' in game_data) and ('playercolor' in game_data):
		session.load(map_file, playername, playercolor)
	else:
		session.load(map_file)

def start_multi():
	"""Starts a multiplayer game server (dummy)

	This also starts the game for the game master
	"""
	pass

def save_game(savegamename=None):
	"""Saves a game
	@param savegamename: string with the full path of the savegame file or None to let user pick one
	@return: bool, whether save was successfull
	"""
	global session
	if savegamename is None:
		savegamename = _modules.gui.show_select_savegame(mode='save')
		if savegamename is None:
			return False # user aborted dialog
		savegamename = SavegameManager.create_filename(savegamename)

	assert os.path.isabs(savegamename)
	try:
		session.save(savegamename)
	except IOError: # usually invalid filename
		_modules.gui.show_popup(_("Invalid filename"), _("You entered an invalid filename."))
		_modules.gui.hide()
		return save_game() # re-show dialog

	return True

def load_game(savegame = None):
	"""Shows select savegame menu if savegame is none, then loads the game"""
	if savegame is None:
		savegame = _modules.gui.show_select_savegame(mode='load')
		if savegame is None:
			return # user aborted dialog
	_modules.gui.show_loading_screen()
	start_singleplayer(savegame)

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
	first_map = _modules.gui.get_maps()[0][1]
	load_game(first_map)

def _start_map(map_name):
	# start a map specified by user
	maps = Gui.get_maps()
	try:
		map_id = maps[1].index(map_name)
		load_game(maps[0][map_id])
	except ValueError:
		print "Error: Cannot find map \"%s\"." % map_name
		import sys; sys.exit(1)

def _load_map(savegamename):
	# load a game specified by user
	saves = SavegameManager.get_saves()
	try:
		save_id = saves[1].index(savegamename)
		load_game(saves[0][save_id])
	except ValueError:
		print "Error: Cannot find savegame \"%s\"." % savegamename
		import sys; sys.exit(1)

def _load_last_quicksave():
	# load last quicksave
	save_files = SavegameManager.get_quicksaves()[0]
	try:
		save = save_files[len(save_files)-1]
	except KeyError:
		print "Error: No quicksave found."
		import sys; sys.exit(1)
	load_game(save)

def _create_db():
	_db = DbReader(':memory:')
	_db("attach ? AS data", 'content/game.sqlite')
	_db("attach ? AS settler", 'content/settler.sqlite')
	return _db

def preload_game_data(lock):
	"""Preloads game data.
	Keeps releasing and acquiring lock, runs until lock can't be acquired."""
	try:
		import logging
		from horizons.entities import Entities
		from horizons.util import Callback
		log = logging.getLogger("preload")
		mydb = _create_db() # create own db reader instance, since it's not thread-safe
		preload_functions = [ Callback(Entities.load_grounds, mydb), \
		                      Callback(Entities.load_buildings, mydb), \
		                      Callback(Entities.load_units, mydb) ]
		for f in preload_functions:
			if not lock.acquire(False):
				break
			log.debug("Preload: %s", f)
			f()
			log.debug("Preload: %s is done", f)
			lock.release()
		log.debug("Preloading done.")
	finally:
		if lock.locked():
			lock.release()

