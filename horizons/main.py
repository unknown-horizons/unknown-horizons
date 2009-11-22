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
   * fife - if a game is running. horizons.fife provides the running engine instance.
   * session - horizons.session instance - check horizons/session.py for more information

   TUTORIAL:
   Continue to horizons.session for further ingame digging.
   """

import os
import os.path
import random
import threading
import thread # for thread.error raised by threading.Lock.release

import fife as fife_module

from util import ActionSetLoader, DbReader
from savegamemanager import SavegameManager
from i18n import update_all_translations
from horizons.gui import Gui
from horizons.settings import Settings
from extscheduler import ExtScheduler

# private module pointers of this module
class Modules(object):
	gui = None
	session = None
_modules = Modules()

def start(command_line_arguments):
	"""Starts the horizons.
	@param command_line_arguments: options object from optparse.OptionParser. see run_uh.py.
	"""
	global fife, db, unstable_features, debug, preloading
	# NOTE: globals are designwise the same thing as singletons. they don't look pretty.
	#       here, we only have globals that are either trivial, or only one instance may ever exist.

	from engine import Fife

	# set commandline globals
	debug = command_line_arguments.debug
	unstable_features = command_line_arguments.unstable_features

	db = _create_db()

	Settings.create_instance(db)
	Settings().set_defaults()

	_init_gettext()

	# create random client_id if necessary
	if Settings().client_id is None:
		Settings().client_id = "".join("-" if c in (8, 13, 18, 23) else \
		                               random.choice("0123456789abcdef") for c in xrange(0, 36))

	# init game parts
	fife = Fife(Settings())
	ExtScheduler.create_instance(fife.pump)
	fife.init()
	_modules.gui = Gui()
	SavegameManager.init()

	# for preloading game data while in main screen
	preload_lock = threading.Lock()
	preload_thread = threading.Thread(target=preload_game_data, args=(preload_lock,))
	preloading = (preload_thread, preload_lock)

	# start something according to commandline parameters

	startup_worked = True
	if command_line_arguments.start_dev_map:
		startup_worked = _start_dev_map()
	elif command_line_arguments.start_random_map:
		startup_worked = _start_random_map()
	elif command_line_arguments.start_map is not None:
		startup_worked = _start_map(command_line_arguments.start_map)
	elif command_line_arguments.load_map is not None:
		startup_worked = _load_map(command_line_arguments.load_map)
	elif command_line_arguments.load_quicksave is not None:
		startup_worked = _load_last_quicksave()
	else: # no commandline parameter, show main screen
		_modules.gui.show_main()
		preloading[0].start()

	if not startup_worked:
		# don't start main loop if startup failed
		return

	fife.run()

def quit():
	"""Quits the game"""
	global fife
	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	ExtScheduler.destroy_instance()
	fife.quit()

def start_singleplayer(map_file, game_data={}):
	"""Starts a singleplayer game
	@param map_file: path to map file
	@param game_data: dict, contains data about the game (playername, etc.)"""
	global fife, preloading, db
	_modules.gui.show()

	# lock preloading
	preloading[1].acquire()
	# wait until it finished it's current action
	if preloading[0].isAlive():
		preloading[0].join()
		assert not preloading[0].isAlive()
	else:
		try:
			preloading[1].release()
		except thread.error:
			pass # due to timing issues, the lock might be released already

	# remove cursor while loading
	fife.cursor.set(fife_module.CURSOR_NONE)
	fife.engine.pump()
	fife.cursor.set(fife_module.CURSOR_IMAGE, fife.default_cursor_image)

	_modules.gui.hide()

	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	from session import Session
	_modules.session = Session(_modules.gui, db)
	_modules.session.init_session()
	_modules.session.load(map_file, **game_data)

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
	if savegamename is None:
		savegamename = _modules.gui.show_select_savegame(mode='save')
		if savegamename is None:
			return False # user aborted dialog
		savegamename = SavegameManager.create_filename(savegamename)

	assert os.path.isabs(savegamename)
	try:
		_modules.session.save(savegamename)
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


def _init_gettext():
	from gettext import translation, install
	settings = Settings()
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
	first_map = SavegameManager.get_maps()[0][1]
	load_game(first_map)
	return True

def _start_map(map_name):
	"""Start a map specified by user
	@return: bool, whether loading succeded"""
	maps = SavegameManager.get_maps()
	map_file = None
	try:
		map_id = maps[1].index(map_name)
		map_file = maps[0][map_id]
	except ValueError:
		print _("Error: Cannot find map \"%s\".") % map_name
		return False
	load_game(map_file)
	return True

def _start_random_map():
	from horizons.util import random_map
	start_singleplayer( random_map.generate_map() )
	return True

def _load_map(savegamename):
	"""Load a map specified by user
	@return: bool, whether loading succeded"""
	saves = SavegameManager.get_saves()
	map_file = None
	try:
		save_id = saves[1].index(savegamename)
		map_file = saves[0][save_id]
	except ValueError:
		print _("Error: Cannot find savegame \"%s\".") % savegamename
		return False
	load_game(map_file)
	return True

def _load_last_quicksave():
	"""Load last quicksave
	@return: bool, whether loading succeded"""
	save_files = SavegameManager.get_quicksaves()[0]
	save = None
	try:
		save = save_files[len(save_files)-1]
	except KeyError:
		print _("Error: No quicksave found.")
		return False
	load_game(save)
	return True

def _create_db():
	"""Returns a dbreader instance, that is connected to the main game data dbfiles.
	NOTE: This data is read_only, so there are no concurrency issues"""
	_db = DbReader(':memory:')
	_db("attach ? AS data", 'content/game.sqlite')
	_db("attach ? AS settler", 'content/settler.sqlite')
	_db("attach ? AS balance", 'content/balance.sqlite')
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
		preload_functions = [ ActionSetLoader.load, \
		                      Callback(Entities.load_grounds, mydb), \
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
	except Exception, e:
		log.warning("Exception occured in preloading thread: %s", e)
	finally:
		if lock.locked():
			lock.release()

