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

import json
import logging
import os
import os.path
import time
import traceback
from random import Random

import horizons.globals
import horizons.main
from horizons.ai.aiplayer import AIPlayer
from horizons.command.building import Tear
from horizons.command.unit import RemoveUnit
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.component.namedcomponent import NamedComponent
from horizons.component.selectablecomponent import SelectableBuildingComponent
from horizons.constants import GAME_SPEED
from horizons.entities import Entities
from horizons.extscheduler import ExtScheduler
from horizons.gui.ingamegui import IngameGui
from horizons.i18n import gettext as T
from horizons.messaging import LoadingProgress, MessageBus, SettingChanged, SpeedChanged
from horizons.messaging.queuingmessagebus import QueuingMessageBus
from horizons.savegamemanager import SavegameManager
from horizons.scenario import ScenarioEventHandler
from horizons.scheduler import Scheduler
from horizons.util.dbreader import DbReader
from horizons.util.living import LivingObject, livingProperty
from horizons.util.savegameaccessor import SavegameAccessor
from horizons.util.uhdbaccessor import read_savegame_template
from horizons.util.worldobject import WorldObject
from horizons.view import View
from horizons.world import World


class Session(LivingObject):
	"""The Session class represents the game's main ingame view and controls cameras and map loading.
	It is alive as long as a game is running.
	Many objects require a reference to this, which makes it a pseudo-global, from which we would
	like to move away in the long term. This is where we hope the components come into play, which
	you will encounter later.

	This is the most important class if you are going to hack on Unknown Horizons; it provides most of
	the important ingame variables.
	Here's a small list of commonly used attributes:

	* world - horizons.world instance of the currently running horizons. Stores players and islands,
		which store settlements, which store buildings, which have productions and collectors.
		Therefore, world deserves its name -- it contains the whole game state.
	* scheduler - horizons.scheduler instance. Used to execute timed events. Master of time in UH.
	* manager - horizons.manager instance. Used to execute commands (used to apply user interactions).
		There is a singleplayer and a multiplayer version. Our mp system works by the mp-manager not
		executing the commands directly, but sending them to all players, where they will be executed
		at the same tick.
	* view - horizons.view instance. Used to control the ingame camera.
	* ingame_gui - horizons.gui.ingame_gui instance. Used to control the ingame gui framework.
		(This is different from gui, which is the main menu and general session-independent gui)
	* selected_instances - Set that holds the currently selected instances (building, units).

	TUTORIAL:
	For further digging you should now be checking out the load() function.
	"""
	timer = livingProperty()
	manager = livingProperty()
	view = livingProperty()
	ingame_gui = livingProperty()
	scenario_eventhandler = livingProperty()

	log = logging.getLogger('session')

	def __init__(self, db, rng_seed=None, ingame_gui_class=IngameGui):
		super().__init__()
		assert isinstance(db, horizons.util.uhdbaccessor.UhDbAccessor)
		self.log.debug("Initing session")
		self.db = db # main db for game data (game.sql)
		# this saves how often the current game has been saved
		self.savecounter = 0
		self.is_alive = True
		self.paused_ticks_per_second = GAME_SPEED.TICKS_PER_SECOND

		self._clear_caches()

		#game
		self.random = self.create_rng(rng_seed)
		assert isinstance(self.random, Random)
		self.timer = self.create_timer()
		Scheduler.create_instance(self.timer)
		self.manager = self.create_manager()
		self.view = View()
		Entities.load(self.db)
		self.scenario_eventhandler = ScenarioEventHandler(self) # dummy handler with no events

		#GUI
		self._ingame_gui_class = ingame_gui_class

		self.selected_instances = set()
		# List of sets that holds the player assigned unit groups.
		self.selection_groups = [set() for _unused in range(10)]

		self._old_autosave_interval = None

	def start(self):
		"""Actually starts the game."""
		self.timer.activate()
		self.scenario_eventhandler.start()
		self.reset_autosave()
		SettingChanged.subscribe(self._on_setting_changed)

	def reset_autosave(self):
		"""(Re-)Set up autosave. Called if autosave interval has been changed."""
		# get_uh_setting returns floats like 4.0 and 42.0 since slider stepping is 1.0.
		interval = int(horizons.globals.fife.get_uh_setting("AutosaveInterval"))
		if interval != self._old_autosave_interval:
			self._old_autosave_interval = interval
			ExtScheduler().rem_call(self, self.autosave)
			if interval != 0: #autosave
				self.log.debug("Initing autosave every %s minutes", interval)
				ExtScheduler().add_new_object(self.autosave, self, interval * 60, -1)

	def _on_setting_changed(self, message):
		if message.setting_name == 'AutosaveInterval':
			self.reset_autosave()

	def create_manager(self):
		"""Returns instance of command manager (currently MPManager or SPManager)"""
		raise NotImplementedError

	def create_rng(self, seed=None):
		"""Returns a RNG (random number generator). Must support the python random.Random interface"""
		raise NotImplementedError

	def create_timer(self):
		"""Returns a Timer instance."""
		raise NotImplementedError

	@classmethod
	def _clear_caches(cls):
		"""Clear all data caches in global namespace related to a session"""
		WorldObject.reset()
		NamedComponent.reset()
		AIPlayer.clear_caches()
		SelectableBuildingComponent.reset()

	def end(self):
		self.log.debug("Ending session")
		self.is_alive = False

		# Has to be done here, cause the manager uses Scheduler!
		Scheduler().rem_all_classinst_calls(self)
		ExtScheduler().rem_all_classinst_calls(self)

		horizons.globals.fife.sound.end()

		# these will call end() if the attribute still exists by the LivingObject magic
		self.ingame_gui = None # keep this before world

		if hasattr(self, 'world'):
			# must be called before the world ref is gone, but may not exist yet while loading
			self.world.end()
		self.world = None
		self.view = None
		self.manager = None
		self.timer = None
		self.scenario_eventhandler = None

		Scheduler().end()
		Scheduler.destroy_instance()

		self.selected_instances = None
		self.selection_groups = None

		self._clear_caches()

		# discard() in case loading failed and we did not yet subscribe
		SettingChanged.discard(self._on_setting_changed)
		MessageBus().reset()
		QueuingMessageBus().reset()

	def quit(self):
		self.end()
		horizons.main.quit_session()

	def autosave(self):
		raise NotImplementedError

	def quicksave(self):
		raise NotImplementedError

	def quickload(self):
		raise NotImplementedError

	def save(self, savegame=None):
		raise NotImplementedError

	def load(self, options):
		"""Loads a map. Key method for starting a game."""
		"""
		TUTORIAL: Here you see how the vital game elements (and some random things that are also required)
		are initialized.
		"""
		if options.is_scenario:
			# game_identifier is a yaml file, that contains reference to actual map file
			self.scenario_eventhandler = ScenarioEventHandler(self, options.game_identifier)
			# scenario maps can be normal maps or scenario maps:
			map_filename = self.scenario_eventhandler.get_map_file()
			options.game_identifier = os.path.join(SavegameManager.scenario_maps_dir, map_filename)
			if not os.path.exists(options.game_identifier):
				options.game_identifier = os.path.join(SavegameManager.maps_dir, map_filename)
			options.is_map = True

		self.log.debug("Session: Loading from %s", options.game_identifier)
		savegame_db = SavegameAccessor(options.game_identifier, options.is_map, options) # Initialize new dbreader
		savegame_data = SavegameManager.get_metadata(savegame_db.db_path)
		self.view.resize_layers(savegame_db)

		# load how often the game has been saved (used to know the difference between
		# a loaded and a new game)
		self.savecounter = savegame_data.get('savecounter', 0)

		if savegame_data.get('rng_state', None):
			rng_state_list = json.loads(savegame_data['rng_state'])

			# json treats tuples as lists, but we need tuples here, so convert back
			def rec_list_to_tuple(x):
				if isinstance(x, list):
					return tuple(rec_list_to_tuple(i) for i in x)
				else:
					return x
			rng_state_tuple = rec_list_to_tuple(rng_state_list)
			# changing the rng is safe for mp, as all players have to have the same map
			self.random.setstate(rng_state_tuple)

		LoadingProgress.broadcast(self, 'session_create_world')
		self.world = World(self) # Load horizons.world module (check horizons/world/__init__.py)
		self.world._init(savegame_db, options.force_player_id, disasters_enabled=options.disasters_enabled)
		self.view.load(savegame_db, self.world) # load view
		if not self.is_game_loaded():
			options.init_new_world(self)
		else:
			# try to load scenario data
			self.scenario_eventhandler.load(savegame_db)
		self.manager.load(savegame_db) # load the manager (there might be old scheduled ticks).
		LoadingProgress.broadcast(self, "session_index_fish")
		self.world.init_fish_indexer() # now the fish should exist

		# load the old gui positions and stuff
		# Do this before loading selections, they need the minimap setup
		LoadingProgress.broadcast(self, "session_load_gui")
		self.ingame_gui = self._ingame_gui_class(self)
		self.ingame_gui.load(savegame_db)

		Scheduler().before_ticking()
		savegame_db.close()

		assert hasattr(self.world, "player"), 'Error: there is no human player'
		LoadingProgress.broadcast(self, "session_finish")
		"""
		TUTORIAL:
		That's it. After that, we call start() to activate the timer, and we're live.
		From here on you should dig into the classes that are loaded above, especially the world class
		(horizons/world/__init__.py). It's where the magic happens and all buildings and units are loaded.
		"""

	def speed_set(self, ticks, suggestion=False):
		"""Set game speed to ticks ticks per second"""
		old = self.timer.ticks_per_second
		self.timer.ticks_per_second = ticks
		self.view.map.setTimeMultiplier(float(ticks) / float(GAME_SPEED.TICKS_PER_SECOND))
		if old == 0 and self.timer.tick_next_time is None: # back from paused state
			if self.paused_time_missing is None:
				# happens if e.g. a dialog pauses the game during startup on hotkeypress
				self.timer.tick_next_time = time.time()
			else:
				self.timer.tick_next_time = time.time() + (self.paused_time_missing / ticks)
		elif ticks == 0 or self.timer.tick_next_time is None:
			# go into paused state or very early speed change (before any tick)
			if self.timer.tick_next_time is not None:
				self.paused_time_missing = (self.timer.tick_next_time - time.time()) * old
			else:
				self.paused_time_missing = None
			self.timer.tick_next_time = None
		else:
			"""
			Under odd circumstances (anti-freeze protection just activated, game speed
			decremented multiple times within this frame) this can delay the next tick
			by minutes. Since the positive effects of the code aren't really observeable,
			this code is commented out and possibly will be removed.

			# correct the time until the next tick starts
			time_to_next_tick = self.timer.tick_next_time - time.time()
			if time_to_next_tick > 0: # only do this if we aren't late
				self.timer.tick_next_time += (time_to_next_tick * old / ticks)
			"""

		SpeedChanged.broadcast(self, old, ticks)

	def speed_up(self):
		if self.speed_is_paused():
			AmbientSoundComponent.play_special('error')
			return
		if self.timer.ticks_per_second in GAME_SPEED.TICK_RATES:
			i = GAME_SPEED.TICK_RATES.index(self.timer.ticks_per_second)
			if i + 1 < len(GAME_SPEED.TICK_RATES):
				self.speed_set(GAME_SPEED.TICK_RATES[i + 1])
		else:
			self.speed_set(GAME_SPEED.TICK_RATES[0])

	def speed_down(self):
		if self.speed_is_paused():
			AmbientSoundComponent.play_special('error')
			return
		if self.timer.ticks_per_second in GAME_SPEED.TICK_RATES:
			i = GAME_SPEED.TICK_RATES.index(self.timer.ticks_per_second)
			if i > 0:
				self.speed_set(GAME_SPEED.TICK_RATES[i - 1])
		else:
			self.speed_set(GAME_SPEED.TICK_RATES[0])

	_pause_stack = 0 # this saves the level of pausing
	# e.g. if two dialogs are displayed, that pause the game,
	# unpause needs to be called twice to unpause the game. cf. #876

	def speed_pause(self, suggestion=False):
		self.log.debug("Session: Pausing")
		self._pause_stack += 1
		if not self.speed_is_paused():
			self.paused_ticks_per_second = self.timer.ticks_per_second
			self.speed_set(0, suggestion)

	def speed_unpause(self, suggestion=False):
		self.log.debug("Session: Unpausing")
		if self.speed_is_paused():
			self._pause_stack -= 1
			if self._pause_stack == 0:
				self.speed_set(self.paused_ticks_per_second)

	def speed_toggle_pause(self, suggestion=False):
		if self.speed_is_paused():
			self.speed_unpause(suggestion)
		else:
			self.speed_pause(suggestion)

	def speed_is_paused(self):
		return (self.timer.ticks_per_second == 0)

	def is_game_loaded(self):
		"""Checks if the current game is a new one, or a loaded one.
		@return: True if game is loaded, else False
		"""
		return (self.savecounter > 0)

	def remove_selected(self):
		self.log.debug('Removing %s', self.selected_instances)
		for instance in [inst for inst in self.selected_instances]:
			if instance.is_building:
				if instance.tearable and instance.owner is self.world.player:
					self.log.debug('Attempting to remove building %s', instance)
					Tear(instance).execute(self)
					self.selected_instances.discard(instance)
				else:
					self.log.debug('Unable to remove building %s', instance)
			elif instance.is_unit:
				if instance.owner is self.world.player:
					self.log.debug('Attempting to remove unit %s', instance)
					RemoveUnit(instance).execute(self)
					self.selected_instances.discard(instance)
				else:
					self.log.debug('Unable to remove unit %s', instance)
			else:
				self.log.error('Unable to remove unknown object %s', instance)

	def _do_save(self, savegame):
		"""Actual save code.
		@param savegame: absolute path"""
		assert os.path.isabs(savegame)
		self.log.debug("Session: Saving to %s", savegame)
		try:
			if os.path.exists(savegame):
				os.unlink(savegame)
			self.savecounter += 1

			db = DbReader(savegame)
		except IOError as e: # usually invalid filename
			headline = T("Failed to create savegame file")
			descr = T("There has been an error while creating your savegame file.")
			advice = T("This usually means that the savegame name contains unsupported special characters.")
			self.ingame_gui.open_error_popup(headline, descr, advice, str(e))
			# retry with new savegamename entered by the user
			# (this must not happen with quicksave/autosave)
			return self.save()
		except PermissionError:
			self.ingame_gui.open_error_popup(
				T("Access is denied"),
				T("The savegame file could be read-only or locked by another process.")
			)
			return self.save()

		try:
			read_savegame_template(db)

			db("BEGIN")
			self.world.save(db)
			self.view.save(db)
			self.ingame_gui.save(db)
			self.scenario_eventhandler.save(db)

			# Store RNG state
			rng_state = json.dumps(self.random.getstate())
			SavegameManager.write_metadata(db, self.savecounter, rng_state)

			# Make sure everything gets written now
			db("COMMIT")
			db.close()
			return True
		except Exception:
			self.log.error("Save Exception:")
			traceback.print_exc()
			# remove invalid savegamefile (but close db connection before deleting)
			db.close()
			os.unlink(savegame)
			return False

	def SetLogBook(self, logbook):
		self.view.SetLogBook(logbook)