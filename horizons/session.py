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

import shutil
import os
import os.path
import time
import logging

import horizons.main

from horizons.gui.ingamegui import IngameGui
from horizons.gui.mousetools import SelectionTool
from horizons.gui.keylisteners import IngameKeyListener
from horizons.gui.mousetools import TearingTool
from timer import Timer
from scheduler import Scheduler
from extscheduler import ExtScheduler
from manager import SPManager
from view import View
from world import World
from entities import Entities
from util import WorldObject, LivingObject, livingProperty, DbReader, Color
from horizons.savegamemanager import SavegameManager
from horizons.world.building.buildable import Buildable
from horizons.command import Command
from horizons.settings import Settings
from horizons.constants import PATHS
from horizons.campaign import CampaignEventHandler


class Session(LivingObject):
	"""Session class represents the games main ingame view and controls cameras and map loading.

	This is the most important class if you are going to hack on Unknown Horizons, it provides most of
	the important ingame variables.
	Here's a small list of commonly used attributes:
	* manager - horizons.manager instance. Used to execute commands that need to be tick,
				synchronized check the class for more information.
	* scheduler - horizons.scheduler instance. Used to execute timed events that do not effect
	              network horizons.
	* view - horizons.view instance. Used to control the ingame camera.
	* entities - horizons.entities instance. used to hold preconstructed dummy classes from the db
	             for later initialization.
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
	campaign_eventhandler = livingProperty()

	log = logging.getLogger('session')

	def __init__(self, gui, db):
		super(Session, self).__init__()
		self.gui = gui # main gui, not ingame gui
		self.db = db # main db for game data (game.sqlite)
		# this saves how often the current game has been saved
		self.savecounter = 0
		self.is_alive = False

	def init_session(self):
		self.log.debug("Initing session")
		self.is_alive = True

		WorldObject.reset()

		#game
		self.timer = Timer()
		Scheduler.create_instance(self.timer)
		self.manager = SPManager(self)
		self.view = View(self, (15, 15))
		Entities.load(self.db)
		Command.default_manager = self.manager
		self.campaign_eventhandler = CampaignEventHandler(self) # dummy handler with no events

		#GUI
		self.gui.session = self
		self.ingame_gui = IngameGui(self, self.gui)
		self.keylistener = IngameKeyListener(self)
		self.cursor = SelectionTool(self)
		self.display_speed()

		self.selected_instances = set()
		self.selection_groups = [set()] * 10 # List of sets that holds the player assigned unit groups.

		#autosave
		if Settings().savegame.autosaveinterval != 0:
			self.log.debug("Initing autosave every %s minutes", Settings().savegame.autosaveinterval)
			ExtScheduler().add_new_object(self.autosave, self, \
			                             Settings().savegame.autosaveinterval * 60, -1)
		Buildable.init_buildable(self)

	def end(self):
		self.log.debug("Ending session")
		self.is_alive = False

		Command.default_manager = None
		Buildable.end_buildable()
		self.gui.session = None

		Scheduler().rem_all_classinst_calls(self)
		ExtScheduler().rem_all_classinst_calls(self)

		if Settings().sound.enabled:
			for emitter in horizons.main.fife.emitter['ambient']:
				emitter.stop()
				horizons.main.fife.emitter['ambient'].remove(emitter)
			horizons.main.fife.emitter['effects'].stop()
			horizons.main.fife.emitter['speech'].stop()
		self.world = None
		self.cursor = None
		self.keylistener = None
		self.ingame_gui = None
		self.view = None
		self.manager = None
		self.timer = None
		self.campaign_eventhandler = None
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
		"""Called automatically in an interval"""
		self.log.debug("Session: autosaving")
		# call saving through horizons.main and not directly through session, so that save errors are handled
		success = horizons.main.save_game(SavegameManager.create_autosave_filename())
		if success:
			SavegameManager.delete_dispensable_savegames(autosaves = True)

	def quicksave(self):
		"""Called when user presses the quicksave hotkey"""
		self.log.debug("Session: quicksaving")
		# call saving through horizons.main and not directly through session, so that save errors are handled
		success = horizons.main.save_game(SavegameManager.create_quicksave_filename())
		if success:
			self.ingame_gui.message_widget.add(None, None, 'QUICKSAVE')
			SavegameManager.delete_dispensable_savegames(quicksaves = True)
		else:
			self.gui.show_popup(_('Error'), _('Failed to quicksave.'))

	def quickload(self):
		"""Loads last quicksave"""
		files = SavegameManager.get_quicksaves(include_displaynames = False)[0]
		if len(files) == 0:
			self.gui.show_popup(_("No quicksaves found"), _("You need to quicksave before you can quickload."))
			return
		files.sort()
		horizons.main.load_game(files[-1])

	def save(self, savegame):
		"""
		@param savegame: the file, where the game will be saved
		@return: bool, whether save was successful or not
		"""
		self.log.debug("Session: Saving to %s", savegame)
		if os.path.exists(savegame):
			os.unlink(savegame)
		shutil.copyfile(PATHS.SAVEGAME_TEMPLATE, savegame)

		self.savecounter += 1

		db = DbReader(savegame)
		try:
			db("BEGIN")
			self.world.save(db)
			#self.manager.save(db)
			self.view.save(db)
			self.ingame_gui.save(db)
			self.campaign_eventhandler.save(db)

			for instance in self.selected_instances:
				db("INSERT INTO selected(`group`, id) VALUES(NULL, ?)", instance.getId())
			for group in xrange(len(self.selection_groups)):
				for instance in self.selection_groups[group]:
					db("INSERT INTO selected(`group`, id) VALUES(?, ?)", group, instance.getId())

			SavegameManager.write_metadata(db, self.savecounter)
			# Savegame integrity assurance
			"""
		except Exception, e:
			# remove invalid savegamefile
			os.unlink(savegame)
			print "Save exception", e
			raise e
		"""
		finally:
			db("COMMIT")

	def record(self, savegame):
		self.save(savegame)
		self.db("ATTACH ? AS demo", savegame)
		self.manager.recording = True

	def stop_record(self):
		assert(self.manager.recording)
		self.manager.recording = False
		self.db("DETACH demo")

	def load(self, savegame, playername = "Default Player", playercolor = Color(), is_scenario=False):
		"""Loads a map.
		@param savegame: path to the savegame database.
		@param playername: string with the playername (None if no player is to be created)
		@param playercolor: Color instance, player's color or None
		"""
		if is_scenario:
			# savegame is a yaml file, that contains reference to acctual map file
			self.campaign_eventhandler = CampaignEventHandler(self, savegame)
			savegame = os.path.join(SavegameManager.maps_dir, \
			                        self.campaign_eventhandler.get_map_file())

		self.log.debug("Session: Loading from %s", savegame)
		savegame_db = DbReader(savegame) # Initialize new dbreader
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
			self.world.setup_player(playername, playercolor)
			center = self.world.init_new_world()
			self.view.center(center[0], center[1])
		else:
			# try to load campaign data
			self.campaign_eventhandler.load(savegame_db)
		self.manager.load(savegame_db) # load the manager (there might me old scheduled ticks.
		self.ingame_gui.load(savegame_db) # load the old gui positions and stuff

		for instance_id in savegame_db("SELECT id FROM selected WHERE `group` IS NULL"): # Set old selected instance
			obj = WorldObject.get_object_by_id(instance_id[0])
			self.selected_instances.add(obj)
			obj.select()
		for group in xrange(len(self.selection_groups)): # load user defined unit groups
			for instance_id in savegame_db("SELECT id FROM selected WHERE `group` = ?", group):
				self.selection_groups[group].add(WorldObject.get_object_by_id(instance_id[0]))

		self.cursor.apply_select() # Set cursor correctly, menus might need to be opened.

		assert hasattr(self.world, "player"), 'Error: there is no human player'
		"""
		TUTORIAL:
		From here on you should digg into the classes that are loaded above, especially the world class.
		(horizons/world/__init__.py). It's where the magic happens and all buildings and units are loaded.
		"""

	def generate_map(self):
		"""Generates a map."""

		#load map
		self.db("attach ':memory:' as map")
		#...
		self.world = World(self)
		self.world._init(self.db)

		#setup view
		self.view.center(((self.world.max_x - self.world.min_x) / 2.0), ((self.world.max_y - self.world.min_y) / 2.0))

	def speed_set(self, ticks):
		old = self.timer.ticks_per_second
		self.timer.ticks_per_second = ticks
		self.view.map.setTimeMultiplier(float(ticks) / float(Settings().ticks.default))
		if old == 0 and self.timer.tick_next_time is None: #back from paused state
			self.timer.tick_next_time = time.time() + (self.paused_time_missing / ticks)
		elif ticks == 0 or self.timer.tick_next_time is None: #go into paused state or very early speed change (before any tick)
			self.paused_time_missing = ((self.timer.tick_next_time - time.time()) * old) if self.timer.tick_next_time is not None else None
			self.timer.tick_next_time = None
		else:
			self.timer.tick_next_time = self.timer.tick_next_time + ((self.timer.tick_next_time - time.time()) * old / ticks)
		self.display_speed()

	def display_speed(self):
		text = u''
		tps = self.timer.ticks_per_second
		if tps == 0: # pause
			text = u'II'
		elif tps == 16: # normal speed, 1x
			pass # display nothing
		else:
			text = unicode(tps/16) + 'x' # 2x, 4x, ...
		self.ingame_gui.display_game_speed(text)

	def speed_up(self):
		if self.timer.ticks_per_second in Settings().ticks.steps:
			i = Settings().ticks.steps.index(self.timer.ticks_per_second)
			if i + 1 < len(Settings().ticks.steps):
				self.speed_set(Settings().ticks.steps[i + 1])
		else:
			self.speed_set(Settings().ticks.steps[0])

	def speed_down(self):
		if self.timer.ticks_per_second in Settings().ticks.steps:
			i = Settings().ticks.steps.index(self.timer.ticks_per_second)
			if i > 0:
				self.speed_set(Settings().ticks.steps[i - 1])
		else:
			self.speed_set(Settings().ticks.steps[0])

	def speed_pause(self):
		self.log.debug("Session: Pausing")
		if not self.speed_is_paused():
			self.paused_ticks_per_second = self.timer.ticks_per_second
			self.speed_set(0)

	def speed_unpause(self):
		self.log.debug("Session: Unpausing")
		if self.speed_is_paused():
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
