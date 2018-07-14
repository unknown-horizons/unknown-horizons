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

"""This is the main game file. It has grown over the years from a collection of global
variables (sic!) to something holding mainly the main gui and game session, as well as
a reference to the engine object (fife).
The functions below are used to start different kinds of games.

TUTORIAL:
Continue to horizons.session for further ingame digging.
"""


import json
import logging
import os
import os.path
import sys
import threading
import traceback
from typing import TYPE_CHECKING, Optional

from fife import fife as fife_module

import horizons.globals
from horizons.constants import AI, GAME, GAME_SPEED, GFX, NETWORK, PATHS, SINGLEPLAYER, VERSION
from horizons.extscheduler import ExtScheduler
from horizons.gui import Gui
from horizons.i18n import gettext as T
from horizons.messaging import LoadingProgress
from horizons.network.networkinterface import NetworkInterface
from horizons.savegamemanager import SavegameManager
from horizons.util.atlasloading import generate_atlases
from horizons.util.checkupdates import setup_async_update_check
from horizons.util.preloader import PreloadingThread
from horizons.util.python import parse_port
from horizons.util.python.callback import Callback
from horizons.util.savegameaccessor import SavegameAccessor
from horizons.util.startgameoptions import StartGameOptions
from horizons.util.uhdbaccessor import UhDbAccessor

if TYPE_CHECKING:
	from horizons.session import Session
	from development.stringpreviewwidget import StringPreviewWidget

"""
Following are a list of global variables. Their scope is this module.
Since this is not a class, in each function where these variables are
referenced, they need to be declared with 'global' keyword.

See: http://python-textbok.readthedocs.io/en/1.0/Variables_and_Scope.html
"""
gui = None # type: Optional[Gui]
session = None # type: Optional[Session]

# used to save a reference to the string previewer to ensure it is not removed by
# garbage collection
__string_previewer = None # type: Optional[StringPreviewWidget]

command_line_arguments = None

preloader = None # type: PreloadingThread


def start(_command_line_arguments):
	"""Starts the horizons. Will drop you to the main menu.
	@param _command_line_arguments: options object from optparse.OptionParser. see run_uh.py.
	"""
	global debug, preloader, command_line_arguments, gui, session
	command_line_arguments = _command_line_arguments
	# NOTE: globals are designwise the same thing as singletons. they don't look pretty.
	#       here, we only have globals that are either trivial, or only one instance may ever exist.

	from .engine import Fife

	# handle commandline globals
	debug = command_line_arguments.debug

	if command_line_arguments.restore_settings:
		# just delete the file, Settings ctor will create a new one
		os.remove(PATHS.USER_CONFIG_FILE)

	if command_line_arguments.mp_master:
		try:
			mpieces = command_line_arguments.mp_master.partition(':')
			NETWORK.SERVER_ADDRESS = mpieces[0]
			# only change port if port is specified
			if mpieces[2]:
				NETWORK.SERVER_PORT = parse_port(mpieces[2])
		except ValueError:
			print("Error: Invalid syntax in --mp-master commandline option. Port must be a number between 1 and 65535.")
			return False

	# init fife before mp_bind is parsed, since it's needed there
	horizons.globals.fife = Fife()

	if command_line_arguments.generate_minimap: # we've been called as subprocess to generate a map preview
		from horizons.gui.modules.singleplayermenu import generate_random_minimap
		generate_random_minimap(* json.loads(
		  command_line_arguments.generate_minimap
		  ))
		sys.exit(0)

	if debug: # also True if a specific module is logged (but not 'fife')
		setup_debug_mode(command_line_arguments)

	if horizons.globals.fife.get_uh_setting("DebugLog"):
		set_debug_log(True, startup=True)

	if command_line_arguments.mp_bind:
		try:
			mpieces = command_line_arguments.mp_bind.partition(':')
			NETWORK.CLIENT_ADDRESS = mpieces[0]
			horizons.globals.fife.set_uh_setting("NetworkPort", parse_port(mpieces[2]))
		except ValueError:
			print("Error: Invalid syntax in --mp-bind commandline option. Port must be a number between 1 and 65535.")
			return False

	setup_AI_settings(command_line_arguments)

	# set MAX_TICKS
	if command_line_arguments.max_ticks:
		GAME.MAX_TICKS = command_line_arguments.max_ticks

	# Setup atlases
	if (command_line_arguments.atlas_generation
	    and not command_line_arguments.gui_test
	    and VERSION.IS_DEV_VERSION
	    and horizons.globals.fife.get_uh_setting('AtlasesEnabled')
	    and horizons.globals.fife.get_uh_setting('AtlasGenerationEnabled')):
		generate_atlases()

	if not VERSION.IS_DEV_VERSION and horizons.globals.fife.get_uh_setting('AtlasesEnabled'):
		GFX.USE_ATLASES = True
		PATHS.DB_FILES = PATHS.DB_FILES + (PATHS.ATLAS_DB_PATH, )

	# init game parts

	if not setup_gui_logger(command_line_arguments):
		return False

	# Check if the no-audio flag has been set.
	if command_line_arguments.no_audio:
		horizons.globals.fife.set_fife_setting('PlaySounds', False)

	# GUI tests always run with sound disabled and SDL (so they can run under xvfb).
	# Needs to be done before engine is initialized.
	if command_line_arguments.gui_test:
		horizons.globals.fife.engine.getSettings().setRenderBackend('SDL')
		horizons.globals.fife.set_fife_setting('PlaySounds', False)

	ExtScheduler.create_instance(horizons.globals.fife.pump)
	horizons.globals.fife.init()

	horizons.globals.db = _create_main_db()
	gui = Gui()
	SavegameManager.init()
	horizons.globals.fife.init_animation_loader(GFX.USE_ATLASES)

	from horizons.entities import Entities
	Entities.load(horizons.globals.db, load_now=False) # create all references

	# for preloading game data while in main screen
	preloader = PreloadingThread()

	# Singleplayer seed needs to be changed before startup.
	if command_line_arguments.sp_seed:
		SINGLEPLAYER.SEED = command_line_arguments.sp_seed
	SINGLEPLAYER.FREEZE_PROTECTION = command_line_arguments.freeze_protection

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
	elif command_line_arguments.load_game is not None:
		startup_worked = _load_cmd_map(command_line_arguments.load_game, command_line_arguments.ai_players,
			command_line_arguments.force_player_id)
	elif command_line_arguments.load_quicksave is not None:
		startup_worked = _load_last_quicksave()
	elif command_line_arguments.edit_map is not None:
		startup_worked = edit_map(command_line_arguments.edit_map)
	elif command_line_arguments.edit_game_map is not None:
		startup_worked = edit_game_map(command_line_arguments.edit_game_map)
	elif command_line_arguments.stringpreview:
		tiny = [i for i in SavegameManager.get_maps()[0] if 'tiny' in i]
		if not tiny:
			tiny = SavegameManager.get_map()[0]
		startup_worked = _start_map(tiny[0], ai_players=0, trader_enabled=False, pirate_enabled=False,
			force_player_id=command_line_arguments.force_player_id, is_map=True)
		from development.stringpreviewwidget import StringPreviewWidget
		__string_previewer = StringPreviewWidget(session)
		__string_previewer.show()
	elif command_line_arguments.create_mp_game:
		gui.show_main()
		gui.windows.open(gui.multiplayermenu)
		gui.multiplayermenu._create_game()
		gui.windows._windows[-1].act()
	elif command_line_arguments.join_mp_game:
		gui.show_main()
		gui.windows.open(gui.multiplayermenu)
		gui.multiplayermenu._join_game()
	else: # no commandline parameter, show main screen

		# initialize update checker
		if not command_line_arguments.gui_test:
			setup_async_update_check()

		gui.show_main()
		if not command_line_arguments.nopreload:
			preloader.start()

	if not startup_worked:
		# don't start main loop if startup failed
		return False

	if command_line_arguments.gamespeed is not None:
		if session is None:
			print("You can only set the speed via command line in combination with a game start parameter such as --start-map, etc.")
			return False
		session.speed_set(GAME_SPEED.TICKS_PER_SECOND * command_line_arguments.gamespeed)

	if command_line_arguments.gui_test:
		from tests.gui import TestRunner
		TestRunner(horizons.globals.fife, command_line_arguments.gui_test)

	horizons.globals.fife.run()
	return True


def setup_AI_settings(command_line_arguments):
	if command_line_arguments.ai_highlights:
		AI.HIGHLIGHT_PLANS = True
	if command_line_arguments.ai_combat_highlights:
		AI.HIGHLIGHT_COMBAT = True
	if command_line_arguments.human_ai:
		AI.HUMAN_AI = True


def setup_debug_mode(command_line_arguments):
	if not (command_line_arguments.debug_module
	        and 'fife' not in command_line_arguments.debug_module):
		horizons.globals.fife._log.logToPrompt = True

	if command_line_arguments.debug_log_only:
		# This is a workaround to not show fife logs in the shell even if
		# (due to the way the fife logger works) these logs will not be
		# redirected to the UH logfile and instead written to a file fife.log
		# in the current directory. See #1782 for background information.
		horizons.globals.fife._log.logToPrompt = False
		horizons.globals.fife._log.logToFile = True


def setup_gui_logger(command_line_arguments):
	"""
	Install gui logger, needs to be done before instantiating Gui, otherwise we miss
	the events of the main menu buttons
	"""
	if command_line_arguments.log_gui:
		if command_line_arguments.gui_test:
			raise Exception("Logging gui interactions doesn't work when running tests.")
		try:
			from tests.gui.logger import setup_gui_logger
			setup_gui_logger()
		except ImportError:
			traceback.print_exc()
			print()
			print("Gui logging requires code that is only present in the repository and is not being installed.")
			return False
	return True


def quit():
	"""Quits the game"""
	global preloader
	preloader.wait_for_finish()
	horizons.globals.fife.quit()


def quit_session():
	"""Quits the current game."""
	global gui, session
	session = None
	gui.show_main()


def start_singleplayer(options):
	"""Starts a singleplayer game."""
	global gui, session, preloader
	gui.show_loading_screen()

	LoadingProgress.broadcast(None, 'load_objects')
	preloader.wait_for_finish()

	# remove cursor while loading
	horizons.globals.fife.cursor.set(fife_module.CURSOR_NONE)
	horizons.globals.fife.engine.pump()
	horizons.globals.fife.set_cursor_image('default')

	# destruct old session (right now, without waiting for gc)
	if session is not None and session.is_alive:
		session.end()

	if options.is_editor:
		from horizons.editor.session import EditorSession as session_class
	else:
		from horizons.spsession import SPSession as session_class

	# start new session
	session = session_class(horizons.globals.db)

	from horizons.scenario import InvalidScenarioFileFormat # would create import loop at top
	from horizons.util.savegameaccessor import MapFileNotFound
	from horizons.util.savegameupgrader import SavegameTooOld
	try:
		session.load(options)
		gui.close_all()
	except InvalidScenarioFileFormat:
		raise
	except (MapFileNotFound, SavegameTooOld, Exception):
		gui.close_all()
		# don't catch errors when we should fail fast (used by tests)
		if os.environ.get('FAIL_FAST', False):
			raise
		print("Failed to load", options.game_identifier)
		traceback.print_exc()
		if session is not None and session.is_alive:
			try:
				session.end()
			except Exception:
				print()
				traceback.print_exc()
				print("Additionally to failing when loading, cleanup afterwards also failed")
		gui.show_main()
		headline = T("Failed to start/load the game")
		descr = T("The game you selected could not be started.") + " " + \
		        T("The savegame might be broken or has been saved with an earlier version.")
		gui.open_error_popup(headline, descr)
		gui.load_game()
	return session


def prepare_multiplayer(game, trader_enabled=True, pirate_enabled=True, natural_resource_multiplier=1):
	"""Starts a multiplayer game server
	TODO: actual game data parameter passing
	"""
	global gui, session, preloader
	gui.show_loading_screen()

	preloader.wait_for_finish()

	# remove cursor while loading
	horizons.globals.fife.cursor.set(fife_module.CURSOR_NONE)
	horizons.globals.fife.engine.pump()
	horizons.globals.fife.set_cursor_image('default')

	# destruct old session (right now, without waiting for gc)
	if session is not None and session.is_alive:
		session.end()
	# start new session
	from horizons.mpsession import MPSession
	# get random seed for game
	uuid = game.uuid
	random = sum([int(uuid[i: i + 2], 16) for i in range(0, len(uuid), 2)])
	session = MPSession(horizons.globals.db, NetworkInterface(), rng_seed=random)

	# NOTE: this data passing is only temporary, maybe use a player class/struct
	if game.is_savegame:
		map_file = SavegameManager.get_multiplayersave_map(game.map_name)
	else:
		map_file = SavegameManager.get_map(game.map_name)

	options = StartGameOptions.create_start_multiplayer(map_file, game.get_player_list(), not game.is_savegame)
	session.load(options)


def start_multiplayer(game):
	global gui, session
	gui.close_all()
	session.start()


## GAME START FUNCTIONS
def _start_map(map_name, ai_players=0, is_scenario=False,
               pirate_enabled=True, trader_enabled=True, force_player_id=None, is_map=False):
	"""Start a map specified by user
	@param map_name: name of map or path to map
	@return: bool, whether loading succeeded"""
	if is_scenario:
		map_file = _find_scenario(map_name, SavegameManager.get_available_scenarios(locales=True))
	else:
		map_file = _find_map(map_name, SavegameManager.get_maps())

	if not map_file:
		return False

	options = StartGameOptions.create_start_singleplayer(map_file, is_scenario,
		ai_players, trader_enabled, pirate_enabled, force_player_id, is_map)
	start_singleplayer(options)
	return True


def _start_random_map(ai_players, seed=None, force_player_id=None):
	options = StartGameOptions.create_start_random_map(ai_players, seed, force_player_id)
	start_singleplayer(options)
	return True


def _load_cmd_map(savegame, ai_players, force_player_id=None):
	"""Load a map specified by user.
	@param savegame: either the displayname of a savegame or a path to a savegame
	@return: bool, whether loading succeeded"""
	# first check for partial or exact matches in the normal savegame list
	savegames = SavegameManager.get_saves()
	map_file = _find_map(savegame, savegames)
	if not map_file:
		return False

	options = StartGameOptions.create_load_game(map_file, force_player_id)
	start_singleplayer(options)
	return True


def _find_scenario(name_or_path, scenario_db):
	"""Find a scenario by name or path specified by user.
	@param name_or_path: scenario name or path to thereof
	@param scenario_db: defaultdict of the format:
	{ <scenario name> : [ (<locale 1>, <path 1>), (<locale 2>, <path 2>), ... ] }
	@return: path to the scenario file as string"""
	game_language = horizons.globals.fife.get_locale()

	# extract name and game_language locale from the path if in correct format
	if os.path.exists(name_or_path) and name_or_path.endswith(".yaml") and "_" in os.path.basename(name_or_path):
		name, game_language = os.path.splitext(os.path.basename(name_or_path))[0].split("_")
	# name_or_path may be a custom scenario path without specified locale
	elif os.path.exists(name_or_path) and name_or_path.endswith(".yaml"):
		return name_or_path
	elif not os.path.exists(name_or_path) and name_or_path.endswith(".yaml"):
		print("Error: name or path '{name}' does not exist.".format(name=name_or_path))
		return
	# assume name_or_path is a scenario name if no extension was specified
	else:
		name = name_or_path

	# check if name is a valid scenario name
	if name not in scenario_db:
		print("Error: scenario '{name}' not in scenario database.".format(name=name))
		return

	# check if name is ambiguous
	found_names = [test_name for test_name in scenario_db if test_name.startswith(name)]
	if len(found_names) > 1:
		print("Error: search for scenario '{name}' returned multiple results.".format(name=name))
		print("\n".join(found_names))
		return

	# get path to scenario by name and game_language locale
	try:
		path_to_scenario = dict(scenario_db[name])[game_language]
		return path_to_scenario
	except KeyError:
		print("Error: could not find scenario '{name}' in scenario database. The locale '{locale}' may be wrong.".format(name=name, locale=game_language))


def _find_map(name_or_path, map_db):
	"""Find a map by name or path specified by user.
	@param name_or_path: map name or path to thereof
	@param map_db: tuple of the format: ( (<map path 1>, <map path 2>, ...), [ <map 1>, <map 2>, ...] )
	@return: path to the map file as string"""

	# map look-up with given valid path
	if os.path.exists(name_or_path) and name_or_path.endswith(".sqlite"):
		return name_or_path
	elif not os.path.exists(name_or_path) and name_or_path.endswith(".sqlite"):
		print("Error: name or path '{name}' does not exist.".format(name=name_or_path))
		return
	# assume name_or_path is a map name if no extension specified
	else:
		if name_or_path not in map_db[1]:
			print("Error: map '{name}' not in map database.".format(name=name_or_path))
			return
		for path, name in zip(*map_db):
			if name == name_or_path:
				return path


def _load_last_quicksave(currentSession=None, force_player_id=None):
	"""Load last quicksave
	@param currentSession: value of currentSession
	@return: bool, whether loading succeeded"""
	save_files = SavegameManager.get_quicksaves()[0]
	if currentSession is not None:
		if not save_files:
			currentSession.ingame_gui.open_popup(T("No quicksaves found"),
			                                       T("You need to quicksave before you can quickload."))
			return False
	else:
		if not save_files:
			print("Error: No quicksave found.")
			return False

	save = max(save_files)
	options = StartGameOptions.create_load_game(save, force_player_id)
	start_singleplayer(options)
	return True


def _edit_map(map_file):
	"""
	Start editing the specified map file.

	@param map_file: path to the map file or a list of random island strings
	@return: bool, whether loading succeeded
	"""
	if not map_file:
		return False

	options = StartGameOptions.create_editor_load(map_file)
	start_singleplayer(options)
	return True


def edit_map(map_name):
	"""
	Start editing the map file specified by the name.

	@param map_name: name of map or path to map
	@return: bool, whether loading succeeded
	"""
	return _edit_map(_find_map(map_name, SavegameManager.get_maps()))


def edit_game_map(saved_game_name):
	"""
	Start editing the specified map.

	@param map_name: name of map or path to map
	@return: bool, whether loading succeeded
	"""
	saved_games = SavegameManager.get_saves()
	saved_game_path = _find_map(saved_game_name, saved_games)
	if not saved_game_path:
		return False

	accessor = SavegameAccessor(saved_game_path, False)
	map_name = accessor.map_name
	accessor.close()
	if isinstance(map_name, list):
		# a random map represented by a list of island strings
		return _edit_map(map_name)
	return edit_map(map_name)


def _create_main_db():
	"""Returns a dbreader instance, that is connected to the main game data dbfiles.
	NOTE: This data is read_only, so there are no concurrency issues."""
	_db = UhDbAccessor(':memory:')
	for i in PATHS.DB_FILES:
		with open(i, "r") as f:
			sql = "BEGIN TRANSACTION;" + f.read() + "COMMIT;"
		_db.execute_script(sql)
	return _db


def set_debug_log(enabled, startup=False):
	"""
	@param enabled: boolean if logging should be enabled
	@param startup: True if on startup to apply settings. Won't show popup
	"""
	global gui, command_line_arguments

	options = command_line_arguments

	if enabled: # enable logging
		if options.debug:
			# log file is already set up, just make sure everything is logged
			logging.getLogger().setLevel(logging.DEBUG)
		else: # set up all anew
			class Data:
				debug = False
				debug_log_only = True
				logfile = None
				debug_module = []
			# use setup call reference, see run_uh.py
			options.setup_debugging(Data)
			options.debug = True

		if not startup:
			headline = T("Logging enabled")
			msg = T("Logs are written to {directory}.").format(directory=PATHS.LOG_DIR)
			# Let the ext scheduler show the popup, so that all other settings can be saved and validated
			ExtScheduler().add_new_object(Callback(gui.open_popup, headline, msg), None)

	else: #disable logging
		logging.getLogger().setLevel(logging.WARNING)
		# keep debug flag in options so to not reenable it fully twice
		# on reenable, only the level will be reset
