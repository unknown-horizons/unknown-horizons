# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from fife import fife as fife_module

from horizons.util import ActionSetLoader, TileSetLoader, Color, parse_port
from horizons.util.uhdbaccessor import UhDbAccessor
from horizons.savegamemanager import SavegameManager
from horizons.gui import Gui
from horizons.extscheduler import ExtScheduler
from horizons.constants import PATHS, NETWORK
from horizons.network.networkinterface import NetworkInterface

# private module pointers of this module
class Modules(object):
	gui = None
	session = None
_modules = Modules()

def start(command_line_arguments):
	"""Starts the horizons.
	@param command_line_arguments: options object from optparse.OptionParser. see run_uh.py.
	"""
	global fife, db, debug, preloading
	# NOTE: globals are designwise the same thing as singletons. they don't look pretty.
	#       here, we only have globals that are either trivial, or only one instance may ever exist.

	from engine import Fife

	# handle commandline globals
	debug = command_line_arguments.debug

	if command_line_arguments.restore_settings:
		# just delete the file, Settings ctor will create a new one
		os.remove( PATHS.USER_CONFIG_FILE )

	if command_line_arguments.mp_master:
		try:
			mpieces = command_line_arguments.mp_master.partition(':')
			NETWORK.SERVER_ADDRESS = mpieces[0]
			# only change port if port is specified
			if len(mpieces[2]) > 0:
				NETWORK.SERVER_PORT = parse_port(mpieces[2], allow_zero=True)
		except ValueError:
			print _("Error: Invalid syntax in --mp-master commandline option. Port must be a number between 1 and 65535.")
			return False

	# init fife before mp_bind is parsed, since it's needed there
	fife = Fife()

	if command_line_arguments.mp_bind:
		try:
			mpieces = command_line_arguments.mp_bind.partition(':')
			NETWORK.CLIENT_ADDRESS = mpieces[0]
			fife.set_uh_setting("NetworkPort", parse_port(mpieces[2], allow_zero=True))
			print 'asdf', fife.get_uh_setting("NetworkPort2")
		except ValueError:
			print _("Error: Invalid syntax in --mp-bind commandline option. Port must be a number between 1 and 65535.")
			return False

	db = _create_db()

	# init game parts

	_init_gettext(fife)

	client_id = fife.get_uh_setting("ClientID")
	if client_id is None or len(client_id) == 0:
		# We need a new client id
		client_id = "".join("-" if c in (8, 13, 18, 23) else \
		                    random.choice("0123456789abcdef") for c in xrange(0, 36))
		from engine import UH_MODULE
		fife.settings.set(UH_MODULE, "ClientID", client_id)
		fife.settings.saveSettings()

	ExtScheduler.create_instance(fife.pump)
	fife.init()
	_modules.gui = Gui()
	SavegameManager.init()
	try:
		NetworkInterface.create_instance()
	except RuntimeError, e:
		headline = _(u"Failed to initialize networking.")
		descr = _(u"Networking couldn't be initialised with the current configuration.")
		advice = _(u"Check the data you entered in the Network section in the settings dialogue.")
		_modules.gui.show_error_popup(headline, descr, advice, unicode(e))

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
	elif command_line_arguments.start_specific_random_map is not None:
		startup_worked = _start_random_map(command_line_arguments.start_specific_random_map)
	elif command_line_arguments.start_map is not None:
		startup_worked = _start_map(command_line_arguments.start_map)
	elif command_line_arguments.start_scenario is not None:
		startup_worked = _start_map(command_line_arguments.start_scenario, True)
	elif command_line_arguments.start_campaign is not None:
		startup_worked = _start_campaign(command_line_arguments.start_campaign)
	elif command_line_arguments.load_map is not None:
		startup_worked = _load_map(command_line_arguments.load_map)
	elif command_line_arguments.load_quicksave is not None:
		startup_worked = _load_last_quicksave()
	elif command_line_arguments.stringpreview:
		startup_worked = _start_map("development_no_trees")
		from development.stringpreviewwidget import StringPreviewWidget
		StringPreviewWidget().show()
	else: # no commandline parameter, show main screen
		_modules.gui.show_main()
		preloading[0].start()

	if not startup_worked:
		# don't start main loop if startup failed
		return False

	fife.run()

def quit():
	"""Quits the game"""
	global fife
	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	preload_game_join(preloading)
	ExtScheduler.destroy_instance()
	fife.quit()

def start_singleplayer(map_file, playername="Player", playercolor=None, is_scenario=False, campaign={}):
	"""Starts a singleplayer game
	@param map_file: path to map file
	"""
	global fife, preloading, db
	preload_game_join(preloading)

	if playercolor is None: # this can't be a default parameter because of circular imports
			playercolor = Color[1]

	# remove cursor while loading
	fife.cursor.set(fife_module.CURSOR_NONE)
	fife.engine.pump()
	fife.cursor.set(fife_module.CURSOR_IMAGE, fife.default_cursor_image)

	# hide whatever is displayed before the game starts
	_modules.gui.hide()

	# destruct old session (right now, without waiting for gc)
	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	# start new session
	from spsession import SPSession
	_modules.session = SPSession(_modules.gui, db)
	players = [ { 'id' : 1, 'name' : playername, 'color' : playercolor, 'local' : True } ]
	try:
		_modules.session.load(map_file, players, is_scenario=is_scenario, campaign = campaign)
	except:
		import traceback
		print "Failed to load", map_file
		traceback.print_exc()
		if _modules.session is not None and _modules.session.is_alive:
			_modules.session.end()
		_modules.gui.show_main()
		headline = _(u"Failed to start/load the game")
		descr = _(u"The game you selected couldn't be started.") + \
		      _("The savegame might be broken or has been saved with an earlier version.")
		_modules.gui.show_error_popup(headline, descr)
		load_game()

def prepare_multiplayer(game):
	"""Starts a multiplayer game server
	TODO: acctual game data parameter passing
	"""
	global fife, preloading, db

	preload_game_join(preloading)

	# remove cursor while loading
	fife.cursor.set(fife_module.CURSOR_NONE)
	fife.engine.pump()
	fife.cursor.set(fife_module.CURSOR_IMAGE, fife.default_cursor_image)

	# hide whatever is displayed before the game starts
	_modules.gui.hide()

	# destruct old session (right now, without waiting for gc)
	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	# start new session
	from mpsession import MPSession
	# get random seed for game
	random = sum(game.get_uuid().uuid)
	_modules.session = MPSession(_modules.gui, db, NetworkInterface(), rng_seed=random)
	# NOTE: this data passing is only temporary, maybe use a player class/struct
	_modules.session.load("content/maps/" + game.get_map_name() + ".sqlite", \
	                      game.get_player_list())

def start_multiplayer(game):
	_modules.session.start()

def load_game(savegame = None, is_scenario = False, campaign = {}):
	"""Shows select savegame menu if savegame is none, then loads the game"""
	if savegame is None:
		savegame = _modules.gui.show_select_savegame(mode='load')
		if savegame is None:
			return # user aborted dialog
	_modules.gui.show_loading_screen()
#TODO
	start_singleplayer(savegame, is_scenario = is_scenario, campaign = campaign)


def _init_gettext(fife):
	from gettext import translation, install
	install('unknownhorizons', 'build/mo', unicode=True)
	fife.update_languages()



## GAME START FUNCTIONS

def _start_dev_map():
	# start the development map (it's the first one)
	first_map = SavegameManager.get_maps()[0][1]
	load_game(first_map)
	return True

def _start_map(map_name, is_scenario = False, campaign = {}):
	"""Start a map specified by user
	@return: bool, whether loading succeded"""
	maps = SavegameManager.get_available_scenarios() if is_scenario else SavegameManager.get_maps()
	map_file = None
	for i in xrange(0, len(maps[1])):
		# exact match
		if maps[1][i] == map_name:
			map_file = maps[0][i]
			break
		# check for partial match
		if maps[1][i].startswith(map_name):
			if map_file is not None:
				# multiple matches, collect all for output
				map_file += u'\n' + maps[0][i]
			else:
				map_file = maps[0][i]
	if map_file is None:
		print _("Error: Cannot find map \"%s\".") % map_name
		return False
	if len(map_file.splitlines()) > 1:
		print _("Error: Found multiple matches: ")
		for match in map_file.splitlines():
			print os.path.basename(match)
		return False
	load_game(map_file, is_scenario, campaign = campaign)
	return True

def _start_random_map(seed = None):
	from horizons.util import random_map
	start_singleplayer( random_map.generate_map(seed) )
	return True

def _start_campaign(campaign_name):
	"""Finds the first scenario in this campaign and
	loads it.
	@return: bool, whether loading succeded"""
	campaign = SavegameManager.get_campaign_info(name = campaign_name)
	scenarios = [sc.get('level') for sc in campaign.get('scenarios',[])]
	if not scenarios:
		return False
	return _start_map(scenarios[0], is_scenario = True, campaign = {'campaign_name': campaign_name, 'scenario_index': 0, 'scenario_name': scenarios[0]})

def _load_map(savegamename):
	"""Load a map specified by user
	@return: bool, whether loading succeded"""
	saves = SavegameManager.get_saves()
	map_file = None
	for i in xrange(0, len(saves[1])):
		# exact match
		if saves[1][i] == savegamename:
			map_file = saves[0][i]
			break
		# check for partial match
		if saves[1][i].startswith(savegamename):
			if map_file is not None:
				# multiple matches, collect all for output
				map_file += u'\n' + saves[0][i]
			else:
				map_file = saves[0][i]
	if map_file is None:
		print _("Error: Cannot find savegame \"%s\".") % savegamename
		return False
	if len(map_file.splitlines()) > 1:
		print _("Error: Found multiple matches: ")
		for match in map_file.splitlines():
			print os.path.basename(match)
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
	_db = UhDbAccessor(':memory:')
	_db("ATTACH ? AS data", 'content/game.sqlite')
	_db("ATTACH ? AS settler", 'content/settler.sqlite')
	_db("ATTACH ? AS balance", 'content/balance.sqlite')
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
		                      TileSetLoader.load,
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

def preload_game_join(preloading):
	"""Wait for preloading to finish.
	@param preloading: tuple: (Thread, Lock)"""
	# lock preloading
	preloading[1].acquire()
	# wait until it finished its current action
	if preloading[0].isAlive():
		preloading[0].join()
		assert not preloading[0].isAlive()
	else:
		try:
			preloading[1].release()
		except thread.error:
			pass # due to timing issues, the lock might be released already

