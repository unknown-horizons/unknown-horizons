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

"""This is the main game file. It has grown over the years from a collection of global
variables (sic!) to something holding mainly the main gui and game session, as well as
a reference to the engine object (fife).
The functions below are used to start different kinds of games.

TUTORIAL:
Continue to horizons.session for further ingame digging.
"""

import os
import sys
import os.path
import random
import json
import time
import traceback
import threading
import thread # for thread.error raised by threading.Lock.release
import shutil

from fife import fife as fife_module

import horizons.globals

from horizons.savegamemanager import SavegameManager
from horizons.gui import Gui
from horizons.extscheduler import ExtScheduler
from horizons.constants import AI, GAME, PATHS, NETWORK, SINGLEPLAYER, GAME_SPEED
from horizons.network.networkinterface import NetworkInterface
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.loaders.tilesetloader import TileSetLoader
from horizons.util.startgameoptions import StartGameOptions
from horizons.util.python import parse_port
from horizons.util.python.callback import Callback
from horizons.util.uhdbaccessor import UhDbAccessor


# private module pointers of this module
class Modules(object):
	gui = None
	session = None
_modules = Modules()

# used to save a reference to the string previewer to ensure it is not removed by
# garbage collection
__string_previewer = None

command_line_arguments = None

def start(_command_line_arguments):
	"""Starts the horizons. Will drop you to the main menu.
	@param _command_line_arguments: options object from optparse.OptionParser. see run_uh.py.
	"""
	global debug, preloading, command_line_arguments
	command_line_arguments = _command_line_arguments
	# NOTE: globals are designwise the same thing as singletons. they don't look pretty.
	#       here, we only have globals that are either trivial, or only one instance may ever exist.

	from engine import Fife

	# handle commandline globals
	debug = command_line_arguments.debug

	if command_line_arguments.enable_atlases:
		# check if atlas files are outdated
		if atlases_need_rebuild():
			print "Atlases have to be rebuild."

	if command_line_arguments.restore_settings:
		# just delete the file, Settings ctor will create a new one
		os.remove( PATHS.USER_CONFIG_FILE )

	if command_line_arguments.mp_master:
		try:
			mpieces = command_line_arguments.mp_master.partition(':')
			NETWORK.SERVER_ADDRESS = mpieces[0]
			# only change port if port is specified
			if mpieces[2]:
				NETWORK.SERVER_PORT = parse_port(mpieces[2])
		except ValueError:
			print "Error: Invalid syntax in --mp-master commandline option. Port must be a number between 1 and 65535."
			return False

	if command_line_arguments.generate_minimap: # we've been called as subprocess to generate a map preview
		from horizons.gui.mainmenu.singleplayer import MapPreview
		MapPreview.generate_minimap( * json.loads(
		  command_line_arguments.generate_minimap
		  ) )
		sys.exit(0)

	# init fife before mp_bind is parsed, since it's needed there
	horizons.globals.fife = Fife()

	if debug: # also True if a specific module is logged (but not 'fife')
		if not (command_line_arguments.debug_module
		        and 'fife' not in command_line_arguments.debug_module):
			horizons.globals.fife._log.lm.setLogToPrompt(True)
		# After the next FIFE release, we should use this instead which is possible as of r3960:
		# horizons.globals.fife._log.logToPrompt = True

		if command_line_arguments.debug_log_only:
			# This is a workaround to not show fife logs in the shell even if
			# (due to the way the fife logger works) these logs will not be
			# redirected to the UH logfile and instead written to a file fife.log
			# in the current directory. See #1782 for background information.
			horizons.globals.fife._log.lm.setLogToPrompt(False)
			horizons.globals.fife._log.lm.setLogToFile(True)
			# same as above applies here, use property after next FIFE release

	if command_line_arguments.mp_bind:
		try:
			mpieces = command_line_arguments.mp_bind.partition(':')
			NETWORK.CLIENT_ADDRESS = mpieces[0]
			horizons.globals.fife.set_uh_setting("NetworkPort", parse_port(mpieces[2]))
		except ValueError:
			print "Error: Invalid syntax in --mp-bind commandline option. Port must be a number between 1 and 65535."
			return False

	if command_line_arguments.ai_highlights:
		AI.HIGHLIGHT_PLANS = True
	if command_line_arguments.ai_combat_highlights:
		AI.HIGHLIGHT_COMBAT = True
	if command_line_arguments.human_ai:
		AI.HUMAN_AI = True

	# set MAX_TICKS
	if command_line_arguments.max_ticks:
		GAME.MAX_TICKS = command_line_arguments.max_ticks

	horizons.globals.db = _create_main_db()

	# init game parts

	# Install gui logger, needs to be done before instantiating Gui, otherwise we miss
	# the events of the main menu buttons
	if command_line_arguments.log_gui:
		if command_line_arguments.gui_test:
			raise Exception("Logging gui interactions doesn't work when running tests.")
		try:
			from tests.gui.logger import setup_gui_logger
			setup_gui_logger()
		except ImportError:
			traceback.print_exc()
			print
			print "Gui logging requires code that is only present in the repository and is not being installed."
			return False

	# GUI tests always run with sound disabled and SDL (so they can run under xvfb).
	# Needs to be done before engine is initialized.
	if command_line_arguments.gui_test:
		horizons.globals.fife.engine.getSettings().setRenderBackend('SDL')
		horizons.globals.fife.set_fife_setting('PlaySounds', False)

	ExtScheduler.create_instance(horizons.globals.fife.pump)
	horizons.globals.fife.init()
	_modules.gui = Gui()
	SavegameManager.init()

	from horizons.entities import Entities
	Entities.load(horizons.globals.db, load_now=False) # create all references

	# for preloading game data while in main screen
	preload_lock = threading.Lock()
	preload_thread = threading.Thread(target=preload_game_data, args=(preload_lock,))
	preloading = (preload_thread, preload_lock)

	# Singleplayer seed needs to be changed before startup.
	if command_line_arguments.sp_seed:
		SINGLEPLAYER.SEED = command_line_arguments.sp_seed

	# start something according to commandline parameters
	startup_worked = True
	if command_line_arguments.start_dev_map:
		startup_worked = _start_map('development', command_line_arguments.ai_players,
			force_player_id=command_line_arguments.force_player_id, is_map=True)
	elif command_line_arguments.start_random_map:
		startup_worked = _start_random_map(command_line_arguments.ai_players, force_player_id=command_line_arguments.force_player_id)
	elif command_line_arguments.start_specific_random_map is not None:
		startup_worked = _start_random_map(command_line_arguments.ai_players,
			seed=command_line_arguments.start_specific_random_map, force_player_id=command_line_arguments.force_player_id)
	elif command_line_arguments.start_map is not None:
		startup_worked = _start_map(command_line_arguments.start_map, command_line_arguments.ai_players,
			force_player_id=command_line_arguments.force_player_id, is_map=True)
	elif command_line_arguments.start_scenario is not None:
		startup_worked = _start_map(command_line_arguments.start_scenario, 0, True, force_player_id=command_line_arguments.force_player_id)
	elif command_line_arguments.start_campaign is not None:
		startup_worked = _start_campaign(command_line_arguments.start_campaign, command_line_arguments.force_player_id)
	elif command_line_arguments.load_map is not None:
		startup_worked = _load_cmd_map(command_line_arguments.load_map, command_line_arguments.ai_players,
			command_line_arguments.force_player_id)
	elif command_line_arguments.load_quicksave is not None:
		startup_worked = _load_last_quicksave()
	elif command_line_arguments.edit_map is not None:
		startup_worked = edit_map(command_line_arguments.edit_map)
	elif command_line_arguments.stringpreview:
		tiny = [ i for i in SavegameManager.get_maps()[0] if 'tiny' in i ]
		if not tiny:
			tiny = SavegameManager.get_map()[0]
		startup_worked = _start_map(tiny[0], ai_players=0, trader_enabled=False, pirate_enabled=False,
			force_player_id=command_line_arguments.force_player_id, is_map=True)
		from development.stringpreviewwidget import StringPreviewWidget
		__string_previewer = StringPreviewWidget(_modules.session)
		__string_previewer.show()
	elif command_line_arguments.create_mp_game:
		_modules.gui.show()
		_modules.gui.show_multi()  # TODO
		_modules.gui.create_default_mp_game()
	elif command_line_arguments.join_mp_game:
		_modules.gui.show()
		_modules.gui.show_multi()  # TODO
		_modules.gui.join_mp_game()
	else: # no commandline parameter, show main screen

		# initalize update checker
		if not command_line_arguments.gui_test:
			from horizons.util.checkupdates import UpdateInfo, check_for_updates, show_new_version_hint
			update_info = UpdateInfo()
			update_check_thread = threading.Thread(target=check_for_updates, args=(update_info,))
			update_check_thread.start()
			def update_info_handler(info):
				if info.status == UpdateInfo.UNINITIALISED:
					ExtScheduler().add_new_object(Callback(update_info_handler, info), info)
				elif info.status == UpdateInfo.READY:
					show_new_version_hint(_modules.gui, info)
				elif info.status == UpdateInfo.INVALID:
					pass # couldn't retrieve file or nothing relevant in there

			update_info_handler(update_info) # schedules checks by itself

		_modules.gui.show()
		if not command_line_arguments.nopreload:
			preloading[0].start()

	if not startup_worked:
		# don't start main loop if startup failed
		return False

	if command_line_arguments.gamespeed is not None:
		if _modules.session is None:
			print "You can only set the speed via command line in combination with a game start parameter such as --start-map, etc."
			return False
		_modules.session.speed_set(GAME_SPEED.TICKS_PER_SECOND*command_line_arguments.gamespeed)

	if command_line_arguments.gui_test:
		from tests.gui import TestRunner
		TestRunner(horizons.globals.fife, command_line_arguments.gui_test)

	if command_line_arguments.interactive_shell:
		from horizons.util import interactive_shell
		interactive_shell.start(horizons.globals.fife)

	horizons.globals.fife.run()

def quit():
	"""Quits the game"""
	horizons.globals.fife.quit()

def start_singleplayer(options):
	"""Starts a singleplayer game."""
	global preloading
	preload_game_join(preloading)

	# remove cursor while loading
	horizons.globals.fife.cursor.set(fife_module.CURSOR_NONE)
	horizons.globals.fife.engine.pump()
	horizons.globals.fife.set_cursor_image('default')

	# destruct old session (right now, without waiting for gc)
	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	# start new session
	from spsession import SPSession
	_modules.session = SPSession(_modules.gui, horizons.globals.db)

	from horizons.scenario import InvalidScenarioFileFormat # would create import loop at top
	try:
		_modules.session.load(options)
	except InvalidScenarioFileFormat:
		raise
	except Exception:
		# don't catch errors when we should fail fast (used by tests)
		if os.environ.get('FAIL_FAST', False):
			raise
		print "Failed to load", options.game_identifier
		traceback.print_exc()
		if _modules.session is not None and _modules.session.is_alive:
			try:
				_modules.session.end()
			except Exception:
				print
				traceback.print_exc()
				print "Additionally to failing when loading, cleanup afterwards also failed"
		_modules.gui.show()
		headline = _(u"Failed to start/load the game")
		descr = _(u"The game you selected could not be started.") + u" " +\
		        _("The savegame might be broken or has been saved with an earlier version.")
		_modules.gui.show_error_popup(headline, descr)
		_modules.gui.load_game()

def prepare_multiplayer(game, trader_enabled=True, pirate_enabled=True, natural_resource_multiplier=1):
	"""Starts a multiplayer game server
	TODO: actual game data parameter passing
	"""
	global preloading

	preload_game_join(preloading)

	# remove cursor while loading
	horizons.globals.fife.cursor.set(fife_module.CURSOR_NONE)
	horizons.globals.fife.engine.pump()
	horizons.globals.fife.set_cursor_image('default')

	# destruct old session (right now, without waiting for gc)
	if _modules.session is not None and _modules.session.is_alive:
		_modules.session.end()
	# start new session
	from mpsession import MPSession
	# get random seed for game
	uuid = game.get_uuid()
	random = sum([ int(uuid[i : i + 2], 16) for i in range(0, len(uuid), 2) ])
	_modules.session = MPSession(_modules.gui, horizons.globals.db, NetworkInterface(), rng_seed=random)

	# NOTE: this data passing is only temporary, maybe use a player class/struct
	if game.is_savegame():
		map_file = SavegameManager.get_multiplayersave_map(game.get_map_name())
	else:
		map_file = SavegameManager.get_map(game.get_map_name())

	options = StartGameOptions.create_start_multiplayer(map_file, game.get_player_list(), not game.is_savegame())
	_modules.session.load(options)

def start_multiplayer(game):
	_modules.session.start()

## GAME START FUNCTIONS
def _start_map(map_name, ai_players=0, is_scenario=False, campaign=None,
               pirate_enabled=True, trader_enabled=True, force_player_id=None, is_map=False):
	"""Start a map specified by user
	@param map_name: name of map or path to map
	@return: bool, whether loading succeded"""
	if is_scenario:
		savegames = SavegameManager.get_available_scenarios(locales=True)
	else:
		savegames = SavegameManager.get_maps()
	map_file = _find_matching_map(map_name, savegames)
	if not map_file:
		return False

	_modules.gui.show_loading_screen()
	options = StartGameOptions.create_start_singleplayer(map_file, is_scenario, campaign,
		ai_players, trader_enabled, pirate_enabled, force_player_id, is_map)
	start_singleplayer(options)
	return True

def _start_random_map(ai_players, seed=None, force_player_id=None):
	options = StartGameOptions.create_start_random_map(ai_players, seed, force_player_id)
	start_singleplayer(options)
	return True

def _start_campaign(campaign_name, force_player_id):
	"""Finds the first scenario in this campaign and loads it.
	@return: bool, whether loading succeded"""
	if os.path.exists(campaign_name):
		# a file was specified. In order to make sure everything works properly,
		# we need to copy the file over to the UH campaign directory.
		# This is not very clean, but it's safe.

		if not campaign_name.endswith(".yaml"):
			print 'Error: campaign filenames have to end in ".yaml".'
			return False

		# check if the user specified a file in the UH campaign dir
		campaign_basename = os.path.basename( campaign_name )
		path_in_campaign_dir = os.path.join(SavegameManager.campaigns_dir, campaign_basename)
		if not (os.path.exists(path_in_campaign_dir) and
		        os.path.samefile(campaign_name, path_in_campaign_dir)):
			#xgettext:python-format
			string = _("Due to technical reasons, the campaign file will be copied to the UH campaign directory ({path}).").format(path=SavegameManager.campaigns_dir)
			string += "\n"
			string += _("This means that changes in the file you specified will not apply to the game directly.")
			#xgettext:python-format
			string += _("To see the changes, either always start UH with the current arguments or edit the file {filename}.").format(filename=path_in_campaign_dir)
			print string

			shutil.copy(campaign_name, SavegameManager.campaigns_dir)
		# use campaign file name below
		campaign_name = os.path.splitext( campaign_basename )[0]

	campaign = SavegameManager.get_campaign_info(name=campaign_name)
	if not campaign:
		print u"Error: Cannot find campaign '{name}'.".format(name=campaign_name)
		return False

	scenarios = [sc.get('level') for sc in campaign.get('scenarios',[])]
	if not scenarios:
		return False

	savegames = SavegameManager.get_available_scenarios(locales=True)
	scenario_file = _find_matching_map(scenarios[0], savegames)
	if not scenario_file:
		return False

	_modules.gui.show_loading_screen()
	options = StartGameOptions.create_start_campaign(scenario_file,
		{'campaign_name': campaign_name, 'scenario_index': 0, 'scenario_name': scenarios[0]},
		force_player_id)
	start_singleplayer(options)
	return True

def _load_cmd_map(savegame, ai_players, force_player_id=None):
	"""Load a map specified by user.
	@param savegame: either the displayname of a savegame or a path to a savegame
	@return: bool, whether loading succeded"""
	# first check for partial or exact matches in the normal savegame list
	savegames = SavegameManager.get_saves()
	map_file = _find_matching_map(savegame, savegames)
	if not map_file:
		return False

	_modules.gui.show_loading_screen()
	options = StartGameOptions.create_load_game(map_file, force_player_id)
	start_singleplayer(options)
	return True

def _find_matching_map(name_or_path, savegames):
	"""*name_or_path* is either a map/savegame name or path to a map/savegame file."""
	game_language = horizons.globals.fife.get_locale()
	# now we have "_en.yaml" which is set to language_extension variable
	language_extension = '_' + game_language + '.' + SavegameManager.scenario_extension
	map_file = None
	for filename, name in zip(*savegames):
		if name in (name_or_path, name_or_path + language_extension):
			# exact match or "tutorial" matching "tutorial_en.yaml"
			return filename
		if name.startswith(name_or_path): # check for partial match
			if map_file is not None:
				# multiple matches, collect all for output
				map_file += u'\n' + filename
			else:
				map_file = filename
	if map_file is not None:
		if len(map_file.splitlines()) > 1:
			print "Error: Found multiple matches:"
			for name_or_path in map_file.splitlines():
				print os.path.basename(name_or_path)
			return
		else:
			return map_file
	else: # not a savegame, check for path to file or fail
		if os.path.exists(name_or_path):
			return name_or_path
		else:
			print u"Error: Cannot find savegame or map '{name}'.".format(name=name_or_path)
			return

def _load_last_quicksave(session=None, force_player_id=None):
	"""Load last quicksave
	@param session: value of session
	@return: bool, whether loading succeded"""
	save_files = SavegameManager.get_quicksaves()[0]
	if session is not None:
		if not save_files:
			session.gui.show_popup(_("No quicksaves found"),
			                       _("You need to quicksave before you can quickload."))
			return False
		else:
			session.ingame_gui.on_escape() # close widgets that might be open
	else:
		if not save_files:
			print "Error: No quicksave found."
			return False

	save = max(save_files)
	_modules.gui.show_loading_screen()
	options = StartGameOptions.create_load_game(save, force_player_id)
	start_singleplayer(options)
	return True

def edit_map(map_name):
	"""
	Start editing the specified map.
	
	@param map_name: name of map or path to map
	@return: bool, whether loading succeeded
	"""

	map_file = _find_matching_map(map_name, SavegameManager.get_maps())
	if not map_file:
		return False
	options = StartGameOptions.create_editor_load(map_file)
	start_singleplayer(options)

	from horizons.editor.worldeditor import WorldEditor
	_modules.session.world_editor = WorldEditor(_modules.session.world)
	return True

def _create_main_db():
	"""Returns a dbreader instance, that is connected to the main game data dbfiles.
	NOTE: This data is read_only, so there are no concurrency issues"""
	_db = UhDbAccessor(':memory:')
	for i in PATHS.DB_FILES:
		f = open(i, "r")
		sql = "BEGIN TRANSACTION;" + f.read() + "COMMIT;"
		_db.execute_script(sql)
	return _db

def preload_game_data(lock):
	"""Preloads game data.
	Keeps releasing and acquiring lock, runs until lock can't be acquired."""
	try:
		import logging
		from horizons.entities import Entities
		log = logging.getLogger("preload")
		mydb = _create_main_db() # create own db reader instance, since it's not thread-safe
		preload_functions = [ ActionSetLoader.load,
		                      TileSetLoader.load,
		                      Callback(Entities.load_grounds, mydb, load_now=True),
		                      Callback(Entities.load_buildings, mydb, load_now=True),
		                      Callback(Entities.load_units, load_now=True) ]
		for f in preload_functions:
			if not lock.acquire(False):
				break
			log.debug("Preload: %s", f)
			f()
			log.debug("Preload: %s is done", f)
			lock.release()
		log.debug("Preloading done.")
	except Exception as e:
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

def atlases_need_rebuild():
	# date of atlases
	atlas_date = time.ctime(os.path.getmtime(PATHS.ACTION_SETS_DIRECTORY + "/atlas/animals.png"))

	for folder in PATHS.ATLAS_SOURCE_DIRECTORIES:
		for path, subdirs, files in os.walk(PATHS.ACTION_SETS_DIRECTORY + folder):
			for name in files:
				file_path = os.path.join(path, name)
				if time.ctime(os.path.getmtime(file_path)) > atlas_date:
					return True
	return False
