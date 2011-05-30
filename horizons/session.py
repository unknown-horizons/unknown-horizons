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

import os
import os.path
import logging

import horizons.main

from horizons.gui.ingamegui import IngameGui
from horizons.gui.mousetools import SelectionTool
from horizons.gui.keylisteners import IngameKeyListener
from horizons.gui.mousetools import TearingTool
from horizons.timer import Timer
from horizons.scheduler import Scheduler
from horizons.extscheduler import ExtScheduler
from horizons.view import View
from horizons.world import World
from horizons.entities import Entities
from horizons.util import WorldObject, NamedObject, LivingObject, livingProperty, SavegameAccessor
from horizons.savegamemanager import SavegameManager
from horizons.scenario import ScenarioEventHandler
from horizons.constants import GAME_SPEED

class Session(LivingObject):
	"""Session class represents the games main ingame view and controls cameras and map loading.

	This is the most important class if you are going to hack on Unknown Horizons, it provides most of
	the important ingame variables.
	Here's a small list of commonly used attributes:
	* manager - horizons.manager instance. Used to execute commands that need to be tick,
				synchronized check the class for more information.
	* scheduler - horizons.scheduler instance. Used to execute timed events that do not effect
	              network games but rather control the local simulation.
	* view - horizons.view instance. Used to control the ingame camera.
	* ingame_gui - horizons.gui.ingame_gui instance. Used to controll the ingame gui.
	* cursor - horizons.gui.{navigation/cursor/selection/building}tool instance. Used to controll
			   mouse events, check the classes for more info.
	* selected_instances - Set that holds the currently selected instances (building, units).
	* world - horizons.world instance of the currently running horizons. Stores islands, players,
	          for later access.

	TUTORIAL:
	For further digging you should now be checking out the load() function.
	"""
	timer = livingProperty()
	manager = livingProperty()
	view = livingProperty()
	ingame_gui = livingProperty()
	keylistener = livingProperty()
	cursor = livingProperty()
	world = livingProperty()
	scenario_eventhandler = livingProperty()

	log = logging.getLogger('session')

	def __init__(self, gui, db):
		super(Session, self).__init__()
		self.log.debug("Initing session")
		self.gui = gui # main gui, not ingame gui
		self.db = db # main db for game data (game.sqlite)
		# this saves how often the current game has been saved
		self.savecounter = 0
		self.is_alive = True

		WorldObject.reset()
		NamedObject.reset()

		#game
		self.random = self.create_rng()
		self.timer = Timer()
		Scheduler.create_instance(self.timer)
		self.manager = self.create_manager()
		self.view = View(self, (15, 15))
		Entities.load(self.db)
		self.scenario_eventhandler = ScenarioEventHandler(self) # dummy handler with no events
		self.campaign = {}

		#GUI
		self.gui.session = self
		self.ingame_gui = IngameGui(self, self.gui)
		self.keylistener = IngameKeyListener(self)
		self.display_speed()

		self.selected_instances = set()
		self.selection_groups = [set()] * 10 # List of sets that holds the player assigned unit groups.

	def start(self):
		"""Acctually starts the game."""
		self.timer.activate()

	def create_manager(self):
		"""Returns instance of command manager (currently MPManager or SPManager)"""
		raise NotImplementedError

	def create_rng(self):
		"""Returns a RNG (random number generator). Must support the python random.Random interface"""
		raise NotImplementedError

	def end(self):
		self.log.debug("Ending session")
		self.is_alive = False

		self.gui.session = None

		Scheduler().rem_all_classinst_calls(self)
		ExtScheduler().rem_all_classinst_calls(self)

		if horizons.main.fife.get_fife_setting("PlaySounds"):
			for emitter in horizons.main.fife.emitter['ambient'][:]:
				emitter.stop()
				horizons.main.fife.emitter['ambient'].remove(emitter)
			horizons.main.fife.emitter['effects'].stop()
			horizons.main.fife.emitter['speech'].stop()
		self.cursor = None
		self.world = None
		self.keylistener = None
		self.ingame_gui = None
		self.view = None
		self.manager = None
		self.timer = None
		self.scenario_eventhandler = None
		Scheduler.destroy_instance()

		self.selected_instances = None
		self.selection_groups = None

	def destroy_tool(self):
		"""Initiate the destroy tool"""
		if not hasattr(self.cursor, 'tear_tool_active') or \
			 not self.cursor.tear_tool_active:
			self.cursor = TearingTool(self)
			self.ingame_gui.hide_menu()

	def autosave(self):
		raise NotImplementedError
	def quicksave(self):
		raise NotImplementedError
	def quickload(self):
		raise NotImplementedError
	def save(self, savegame):
		raise NotImplementedError

	def load(self, savegame, players, is_scenario=False, campaign={}):
		"""Loads a map.
		@param savegame: path to the savegame database.
		@param players: iterable of dictionaries containing id, name, color and local
		@param is_scenario: Bool whether the loaded map is a scenario or not
		"""
		if is_scenario:
			# savegame is a yaml file, that contains reference to actual map file
			self.scenario_eventhandler = ScenarioEventHandler(self, savegame)
			savegame = os.path.join(SavegameManager.maps_dir, \
			                        self.scenario_eventhandler.get_map_file())
		self.campaign = campaign

		self.log.debug("Session: Loading from %s", savegame)
		savegame_db = SavegameAccessor(savegame) # Initialize new dbreader
		try:
			# load how often the game has been saved (used to know the difference between
			# a loaded and a new game)
			self.savecounter = SavegameManager.get_metadata(savegame)['savecounter']
		except KeyError:
			self.savecounter = 0

		self.world = World(self) # Load horizons.world module (check horizons/world/__init__.py)
		self.world._init(savegame_db)
		self.view.load(savegame_db) # load view
		if not self.is_game_loaded():
			# NOTE: this must be sorted before iteration, cause there is no defined order for
			#       iterating a dict, and it must happen in the same order for mp games.
			for i in sorted(players):
				self.world.setup_player(i['id'], i['name'], i['color'], i['local'])
			center = self.world.init_new_world()
			self.view.center(center[0], center[1])
		else:
			# try to load scenario data
			self.scenario_eventhandler.load(savegame_db)
		self.manager.load(savegame_db) # load the manager (there might me old scheduled ticks).
		self.world.init_fish_indexer() # now the fish should exist
		self.ingame_gui.load(savegame_db) # load the old gui positions and stuff

		for instance_id in savegame_db("SELECT id FROM selected WHERE `group` IS NULL"): # Set old selected instance
			obj = WorldObject.get_object_by_id(instance_id[0])
			self.selected_instances.add(obj)
			obj.select()
		for group in xrange(len(self.selection_groups)): # load user defined unit groups
			for instance_id in savegame_db("SELECT id FROM selected WHERE `group` = ?", group):
				self.selection_groups[group].add(WorldObject.get_object_by_id(instance_id[0]))

		# cursor has to be inited last, else player interacts with a not inited world with it.
		self.cursor = SelectionTool(self)
		self.cursor.apply_select() # Set cursor correctly, menus might need to be opened.

		assert hasattr(self.world, "player"), 'Error: there is no human player'
		"""
		TUTORIAL:
		From here on you should digg into the classes that are loaded above, especially the world class.
		(horizons/world/__init__.py). It's where the magic happens and all buildings and units are loaded.
		"""

	def speed_set(self, ticks):
		"""Set game speed to ticks ticks per second"""
		raise NotImplementedError

	def display_speed(self):
		text = u''
		tps = self.timer.ticks_per_second
		if tps == 0: # pause
			text = u'0x'
		elif tps == GAME_SPEED.TICKS_PER_SECOND: # normal speed, 1x
			pass # display nothing
		else:
			text = unicode(tps/GAME_SPEED.TICKS_PER_SECOND) + u'x' # 2x, 4x, ...
		self.ingame_gui.display_game_speed(text)

	def speed_up(self):
		if self.timer.ticks_per_second in GAME_SPEED.TICK_RATES:
			i = GAME_SPEED.TICK_RATES.index(self.timer.ticks_per_second)
			if i + 1 < len(GAME_SPEED.TICK_RATES):
				self.speed_set(GAME_SPEED.TICK_RATES[i + 1])
		else:
			self.speed_set(GAME_SPEED.TICK_RATES[0])

	def speed_down(self):
		if self.timer.ticks_per_second in GAME_SPEED.TICK_RATES:
			i = GAME_SPEED.TICK_RATES.index(self.timer.ticks_per_second)
			if i > 0:
				self.speed_set(GAME_SPEED.TICK_RATES[i - 1])
		else:
			self.speed_set(GAME_SPEED.TICK_RATES[0])

	_pause_stack = 0 # this saves the level of pausing
	# e.g. if two dialogs are displayed, that pause the game,
	# unpause needs to be called twice to unpause the game. cf. #876
	def speed_pause(self):
		self.log.debug("Session: Pausing")
		self._pause_stack += 1
		if not self.speed_is_paused():
			self.paused_ticks_per_second = self.timer.ticks_per_second
			self.speed_set(0)

	def speed_unpause(self):
		self.log.debug("Session: Unpausing")
		if self.speed_is_paused():
			self._pause_stack -= 1
			if self._pause_stack == 0:
				self.speed_set(self.paused_ticks_per_second)

	def speed_toggle_pause(self):
		if self.speed_is_paused():
			self.speed_unpause()
		else:
			self.speed_pause()

	def speed_is_paused(self):
		return (self.timer.ticks_per_second == 0)

	def is_game_loaded(self):
		"""Checks if the current game is a new one, or a loaded one.
		@return: True if game is loaded, else False
		"""
		return (self.savecounter > 0)
