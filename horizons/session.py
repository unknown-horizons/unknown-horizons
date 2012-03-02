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

import os
import os.path
import logging
import json
import traceback
import time
from random import Random

import horizons.main

from horizons.ai.aiplayer import AIPlayer
from horizons.gui.ingamegui import IngameGui
from horizons.gui.mousetools import SelectionTool, PipetteTool, TearingTool, BuildingTool, AttackingTool
from horizons.command.building import Tear
from horizons.util.dbreader import DbReader
from horizons.command.unit import RemoveUnit
from horizons.gui.keylisteners import IngameKeyListener
from horizons.scheduler import Scheduler
from horizons.extscheduler import ExtScheduler
from horizons.view import View
from horizons.gui import Gui
from horizons.world import World
from horizons.entities import Entities
from horizons.util import WorldObject, LivingObject, livingProperty, SavegameAccessor
from horizons.util.uhdbaccessor import read_savegame_template
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.world.component.namedcomponent import NamedComponent
from horizons.world.component.selectablecomponent import SelectableComponent
from horizons.savegamemanager import SavegameManager
from horizons.scenario import ScenarioEventHandler
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.constants import GAME_SPEED, PATHS
from horizons.util.messaging.messagebus import MessageBus
from horizons.world.managers.statusiconmanager import StatusIconManager

class Session(LivingObject):
	"""Session class represents the games main ingame view and controls cameras and map loading.
	It is alive as long as a game is running.
	Many objects require a reference to this, which makes it a pseudo-global, from what we would
	like to move away long-term. This is where we hope the components come into play, which
	you will encounter later

	This is the most important class if you are going to hack on Unknown Horizons, it provides most of
	the important ingame variables.
	Here's a small list of commonly used attributes:

	* world - horizons.world instance of the currently running horizons. Stores players and islands,
		which store settlements, which store buildings, which have productions and collectors.
		Therefore world deserves its name, it contains the whole game state.
	* scheduler - horizons.scheduler instance. Used to execute timed events. Master of time in UH.
	* manager - horizons.manager instance. Used to execute commands (used to apply user interactions).
		There is a singleplayer and a multiplayer version. Our mp system works by the mp-manager not
		executing the commands directly, but sending them to all players, where they will be executed
		at the same tick.
	* view - horizons.view instance. Used to control the ingame camera.
	* ingame_gui - horizons.gui.ingame_gui instance. Used to control the ingame gui framework.
		(This is different from gui, which is the main menu and general session-independent gui)
	* cursor - horizons.gui.{navigation/cursor/selection/building}tool instance. Used to handle
			   mouse events.
	* selected_instances - Set that holds the currently selected instances (building, units).

	TUTORIAL:
	For further digging you should now be checking out the load() function.
	"""
	timer = livingProperty()
	manager = livingProperty()
	view = livingProperty()
	ingame_gui = livingProperty()
	keylistener = livingProperty()
	scenario_eventhandler = livingProperty()

	log = logging.getLogger('session')

	def __init__(self, gui, db, rng_seed=None):
		super(Session, self).__init__()
		assert isinstance(db, horizons.util.uhdbaccessor.UhDbAccessor)
		self.log.debug("Initing session")
		self.gui = gui # main gui, not ingame gui
		self.db = db # main db for game data (game.sql)
		# this saves how often the current game has been saved
		self.savecounter = 0
		self.is_alive = True

		self._clear_caches()
		self.message_bus = MessageBus()

		#game
		self.random = self.create_rng(rng_seed)
		assert isinstance(self.random, Random)
		self.timer = self.create_timer()
		Scheduler.create_instance(self.timer)
		self.manager = self.create_manager()
		self.view = View(self)
		Entities.load(self.db)
		self.scenario_eventhandler = ScenarioEventHandler(self) # dummy handler with no events
		self.campaign = {}

		#GUI
		self.gui.session = self
		self.ingame_gui = IngameGui(self, self.gui)
		self.keylistener = IngameKeyListener(self)
		self.coordinates_tooltip = None
		self.display_speed()
		LastActivePlayerSettlementManager.create_instance(self)


		self.status_icon_manager = StatusIconManager(self)

		self.selected_instances = set()
		self.selection_groups = [set()] * 10 # List of sets that holds the player assigned unit groups.

		self._old_autosave_interval = None

	def start(self):
		"""Actually starts the game."""
		self.timer.activate()
		self.reset_autosave()

	def reset_autosave(self):
		"""(Re-)Set up autosave. Called if autosave interval has been changed."""
		# get_uh_setting returns floats like 4.0 and 42.0 since slider stepping is 1.0.
		interval = int(horizons.main.fife.get_uh_setting("AutosaveInterval"))
		if interval != self._old_autosave_interval:
			self._old_autosave_interval = interval
			ExtScheduler().rem_call(self, self.autosave)
			if interval != 0: #autosave
				self.log.debug("Initing autosave every %s minutes", interval)
				ExtScheduler().add_new_object(self.autosave, self, interval * 60, -1)

	def create_manager(self):
		"""Returns instance of command manager (currently MPManager or SPManager)"""
		raise NotImplementedError

	def create_rng(self, seed=None):
		"""Returns a RNG (random number generator). Must support the python random.Random interface"""
		raise NotImplementedError

	def create_timer(self):
		"""Returns a Timer instance."""
		raise NotImplementedError

	def _clear_caches(self):
		WorldObject.reset()
		NamedComponent.reset()
		AIPlayer.clear_caches()

	def end(self):
		self.log.debug("Ending session")
		self.is_alive = False

		LastActivePlayerSettlementManager().remove()
		LastActivePlayerSettlementManager.destroy_instance()

		self.gui.session = None

		Scheduler().rem_all_classinst_calls(self)
		ExtScheduler().rem_all_classinst_calls(self)

		if horizons.main.fife.get_fife_setting("PlaySounds"):
			for emitter in horizons.main.fife.sound.emitter['ambient'][:]:
				emitter.stop()
				horizons.main.fife.sound.emitter['ambient'].remove(emitter)
			horizons.main.fife.sound.emitter['effects'].stop()
			horizons.main.fife.sound.emitter['speech'].stop()
		if hasattr(self, "cursor"): # the line below would crash uglily on ^C
			self.cursor.remove()

		if hasattr(self, 'cursor') and self.cursor is not None:
			self.cursor.end()
		# these will call end() if the attribute still exists by the LivingObject magic
		self.ingame_gui = None # keep this before world
		self.cursor = None
		self.world.end() # must be called before the world ref is gone
		self.world = None
		self.keylistener = None
		self.view = None
		self.manager = None
		self.timer = None
		self.scenario_eventhandler = None

		Scheduler().end()
		Scheduler.destroy_instance()

		self.selected_instances = None
		self.selection_groups = None

		self.status_icon_manager = None
		self.message_bus = None

		horizons.main._modules.session = None
		self._clear_caches()

	def toggle_cursor(self, which, *args, **kwargs):
		"""Alternate between the cursor which and default.
		args and kwargs are used to construct which."""
		if self.current_cursor == which:
			self.set_cursor()
		else:
			self.set_cursor(which, *args, **kwargs)

	def set_cursor(self, which='default', *args, **kwargs):
		"""Sets the mousetool (i.e. cursor).
		This is done here for encapsulation and control over destructors.
		Further arguments are passed to the mouse tool constructor."""
		self.cursor.remove()
		self.current_cursor = which
		klass = {
			'default'   : SelectionTool,
		  'selection' : SelectionTool,
		  'tearing'   : TearingTool,
		  'pipette'   : PipetteTool,
		  'attacking' : AttackingTool,
		  'building'  : BuildingTool
		}[which]
		self.cursor = klass(self, *args, **kwargs)

	def toggle_destroy_tool(self):
		"""Initiate the destroy tool"""
		self.toggle_cursor('tearing')

	def autosave(self):
		raise NotImplementedError
	def quicksave(self):
		raise NotImplementedError
	def quickload(self):
		raise NotImplementedError
	def save(self, savegame=None):
		raise NotImplementedError

	def load(self, savegame, players, trader_enabled, pirate_enabled,
	         natural_resource_multiplier, is_scenario=False, campaign=None,
	         force_player_id=None, disasters_enabled=True):
		"""Loads a map. Key method for starting a game.
		@param savegame: path to the savegame database.
		@param players: iterable of dictionaries containing id, name, color, local, ai, and difficulty
		@param is_scenario: Bool whether the loaded map is a scenario or not
		@param force_player_id: the worldid of the selected human player or default if None (debug option)
		"""
		"""
		TUTORIAL: Here you see how the vital game elements (and some random things that are also required)
		are initialised
		"""
		if is_scenario:
			# savegame is a yaml file, that contains reference to actual map file
			self.scenario_eventhandler = ScenarioEventHandler(self, savegame)
			# scenario maps can be normal maps or scenario maps:
			map_filename = self.scenario_eventhandler.get_map_file()
			savegame = os.path.join(SavegameManager.scenario_maps_dir, map_filename)
			if not os.path.exists(savegame):
				savegame = os.path.join(SavegameManager.maps_dir, map_filename)
		self.campaign = {} if not campaign else campaign

		self.log.debug("Session: Loading from %s", savegame)
		savegame_db = SavegameAccessor(savegame) # Initialize new dbreader
		savegame_data = SavegameManager.get_metadata(savegame)

		# load how often the game has been saved (used to know the difference between
		# a loaded and a new game)
		self.savecounter = 0 if not 'savecounter' in savegame_data else savegame_data['savecounter']

		if savegame_data.get('rng_state', None):
			rng_state_list = json.loads( savegame_data['rng_state'] )
			# json treats tuples as lists, but we need tuples here, so convert back
			def rec_list_to_tuple(x):
				if isinstance(x, list):
					return tuple( rec_list_to_tuple(i) for i in x )
				else:
					return x
			rng_state_tuple = rec_list_to_tuple(rng_state_list)
			# changing the rng is safe for mp, as all players have to have the same map
			self.random.setstate( rng_state_tuple )

		self.world = World(self) # Load horizons.world module (check horizons/world/__init__.py)
		self.world._init(savegame_db, force_player_id, disasters_enabled=disasters_enabled)
		self.view.load(savegame_db) # load view
		if not self.is_game_loaded():
			# NOTE: this must be sorted before iteration, cause there is no defined order for
			#       iterating a dict, and it must happen in the same order for mp games.
			for i in sorted(players, lambda p1, p2: cmp(p1['id'], p2['id'])):
				self.world.setup_player(i['id'], i['name'], i['color'], i['local'], i['ai'], i['difficulty'])
			self.world.set_forced_player(force_player_id)
			center = self.world.init_new_world(trader_enabled, pirate_enabled, natural_resource_multiplier)
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
			obj.get_component(SelectableComponent).select()
		for group in xrange(len(self.selection_groups)): # load user defined unit groups
			for instance_id in savegame_db("SELECT id FROM selected WHERE `group` = ?", group):
				self.selection_groups[group].add(WorldObject.get_object_by_id(instance_id[0]))

		# cursor has to be inited last, else player interacts with a not inited world with it.
		self.current_cursor = 'default'
		self.cursor = SelectionTool(self)
		# Set cursor correctly, menus might need to be opened.
		# Open menus later, they may need unit data not yet inited
		self.cursor.apply_select()

		Scheduler().before_ticking()
		savegame_db.close()

		assert hasattr(self.world, "player"), 'Error: there is no human player'
		"""
		TUTORIAL:
		That's it. After that, we call start() to activate the timer, and we're on live.
		From here on you should digg into the classes that are loaded above, especially the world class.
		(horizons/world/__init__.py). It's where the magic happens and all buildings and units are loaded.
		"""

	def speed_set(self, ticks, suggestion=False):
		"""Set game speed to ticks ticks per second"""
		old = self.timer.ticks_per_second
		self.timer.ticks_per_second = ticks
		self.view.map.setTimeMultiplier(float(ticks) / float(GAME_SPEED.TICKS_PER_SECOND))
		if old == 0 and self.timer.tick_next_time is None: #back from paused state
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
				self.paused_time_missing =  None
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
		self.display_speed()

	def display_speed(self):
		text = u''
		up_icon = self.ingame_gui.widgets['minimap'].findChild(name='speedUp')
		down_icon = self.ingame_gui.widgets['minimap'].findChild(name='speedDown')
		tps = self.timer.ticks_per_second
		if tps == 0: # pause
			text = u'0x'
			up_icon.set_inactive()
			down_icon.set_inactive()
		else:
			if tps != GAME_SPEED.TICKS_PER_SECOND:
				text = unicode("%1gx" % (tps * 1.0/GAME_SPEED.TICKS_PER_SECOND))
				#%1g: displays 0.5x, but 2x instead of 2.0x
			index = GAME_SPEED.TICK_RATES.index(tps)
			if index + 1 >= len(GAME_SPEED.TICK_RATES):
				up_icon.set_inactive()
			else:
				up_icon.set_active()
			if index > 0:
				down_icon.set_active()
			else:
				down_icon.set_inactive()
		self.ingame_gui.display_game_speed(text)


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
					self.log.debug('Attempting to remove building %s', inst)
					Tear(instance).execute(self)
					self.selected_instances.discard(instance)
				else:
					self.log.debug('Unable to remove building %s', inst)
			elif instance.is_unit:
				if instance.owner is self.world.player:
					self.log.debug('Attempting to remove unit %s', inst)
					RemoveUnit(instance).execute(self)
					self.selected_instances.discard(instance)
				else:
					self.log.debug('Unable to remove unit %s', inst)
			else:
				self.log.error('Unable to remove unknown object %s', instance)

	def save_map(self, prefix):
		maps_folder = os.path.join(PATHS.USER_DIR, 'maps')
		if not os.path.exists(maps_folder):
			os.makedirs(maps_folder)
		self.world.save_map(maps_folder, prefix)

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
			headline = _("Failed to create savegame file")
			descr = _("There has been an error while creating your savegame file.")
			advice = _("This usually means that the savegame name contains unsupported special characters.")
			self.gui.show_error_popup(headline, descr, advice, unicode(e))
			return self.save() # retry with new savegamename entered by the user
			# this must not happen with quicksave/autosave
		except ZeroDivisionError as err:
			# TODO:
			# this should say WindowsError, but that somehow now leads to a NameError
			if err.winerror == 5:
				self.gui.show_error_popup(_("Access is denied"), \
				                          _("The savegame file is probably read-only."))
				return self.save()
			elif err.winerror == 32:
				self.gui.show_error_popup(_("File used by another process"), \
				                          _("The savegame file is currently used by another program."))
				return self.save()
			raise

		try:
			read_savegame_template(db)

			db("BEGIN")
			self.world.save(db)
			#self.manager.save(db)
			self.view.save(db)
			self.ingame_gui.save(db)
			self.scenario_eventhandler.save(db)

			for instance in self.selected_instances:
				db("INSERT INTO selected(`group`, id) VALUES(NULL, ?)", instance.worldid)
			for group in xrange(len(self.selection_groups)):
				for instance in self.selection_groups[group]:
					db("INSERT INTO selected(`group`, id) VALUES(?, ?)", group, instance.worldid)

			rng_state = json.dumps( self.random.getstate() )
			SavegameManager.write_metadata(db, self.savecounter, rng_state)
			# make sure everything get's written now
			db("COMMIT")
			db.close()
			return True
		except:
			print "Save Exception"
			traceback.print_exc()
			db.close() # close db before delete
			os.unlink(savegame) # remove invalid savegamefile
			return False
