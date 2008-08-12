# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import math
import shutil
import glob
import os
import os.path
import time

import fife

import game.main
from game.gui.selectiontool import SelectionTool
from game.world.building import building
from game.world.units.ship import Ship
from game.world.player import Player
from game.gui.ingamegui import IngameGui
from game.gui.ingamekeylistener import IngameKeyListener
from game.world.island import Island
from game.dbreader import DbReader
from game.timer import Timer
from game.scheduler import Scheduler
from game.manager import SPManager
from game.view import View
from game.world import World
from game.entities import Entities
from game.util import livingObject, livingProperty, WorldObject

class Session(livingObject):
	"""Session class represents the games main ingame view and controls cameras and map loading."""
	autosavedir = 'content/save/autosave'
	quicksavedir = 'content/save/quicksave'
	autosave_filenamepattern = '%(dir)s/autosave-%(timestamp)d.sqlite'
	quicksave_filenamepattern = '%(dir)s/quicksave-%(timestamp).2f.sqlite'
	
	timer = livingProperty()
	manager = livingProperty()
	scheduler = livingProperty()
	view = livingProperty()
	entities = livingProperty()
	ingame_gui = livingProperty()
	keylistener = livingProperty()
	cursor = livingProperty()
	world = livingProperty()

	def begin(self):
		super(Session, self).begin()

		WorldObject.reset()

		#game
		self.timer = Timer(16)
		self.manager = SPManager()
		self.scheduler = Scheduler(self.timer)
		self.view = View((15, 15))
		self.entities = Entities()

		#GUI
		self.ingame_gui = IngameGui()
		self.keylistener = IngameKeyListener()
		self.cursor = SelectionTool()

		self.selected_instances = set()
		self.selection_groups = [set()] * 10
		
		#autosave
		if game.main.settings.savegame.autosaveinterval != 0:
			self.scheduler.add_new_object(self.autosave, self, game.main.settings.savegame.autosaveinterval*self.timer.ticks_per_second*60, -1)

	def end(self):
		self.scheduler.rem_all_classinst_calls(self)
		
		self.cursor = None
		self.keylistener = None
		self.ingame_gui = None
		self.entities = None
		self.view = None
		self.scheduler = None
		self.manager = None
		self.timer = None
		self.world = None

		self.selected_instances = None
		self.selection_groups = None
		super(Session, self).end()

		#import pdb 
		#import gc
		#print 'WorldObject.get_objs().valuerefs()'
		#pdb.set_trace()

	def autosave(self):
		"""Called automatically in an interval"""
		savegame = self.__class__.autosave_filenamepattern % {'dir' : self.__class__.autosavedir,'timestamp' : time.time()}
		self.save(savegame)
		self.delete_dispensable_savegames('%s/autosave-*.sqlite' % self.__class__.autosavedir, 
																			game.main.settings.savegame.savedquicksaves)

	def quicksave(self):
		"""Called when user presses a hotkey"""
		savegame = self.__class__.quicksave_filenamepattern % {'dir' : self.__class__.quicksavedir, 'timestamp' : time.time()}
		self.save(savegame)
		self.delete_dispensable_savegames('%s/quicksave-*.sqlite' % self.__class__.quicksavedir,
																			game.main.settings.savegame.savedquicksaves)
		
	def quickload(self):
		"""Loads last quicksave"""
		files = glob.glob("%s/*" % self.__class__.quicksavedir)
		if len(files) == 0:
			# FIXME: I'm not sure if such gui-code should be placed here
			game.main.showPopup("No quicksaves found", "You need to quicksave before you can quickload.")
			return 
		files.sort()
		game.main.loadGame(files[-1])

	def delete_dispensable_savegames(self, pattern, limit):
		"""Delete savegames that are no longer needed
		@param pattern: globbing pattern that all savegames conform to
		@param limit: number of savegames to keep
		"""
		files = glob.glob(pattern)
		if len(files) > limit:
			files.sort()
			for i in xrange(0, len(files) - limit):
				os.unlink(files[i])

	def save(self, savegame = "content/save/quicksave.sqlite"):
		"""
		@param savegame: the file, where the game will be saved
		"""
		if os.path.exists(savegame):
			os.unlink(savegame)
		shutil.copyfile('content/savegame_template.sqlite', savegame)

		db = DbReader(savegame)
		try:
			db("BEGIN")
			db("INSERT INTO metadata(name, value) VALUES(\"timestamp\", ?)", time.time())
			self.world.save(db)
			#self.manager.save(db)
			#self.view.save(db)
		finally:
			db("COMMIT")

	def load(self, savegame = "content/save/quicksave.sqlite"):
		"""Loads a map.
		@param savegame: path to the savegame database.
		"""

		db = DbReader(savegame)
		self.world = World(db)
		#setup view
		#self.view.center(((self.world.max_x - self.world.min_x) / 2.0), ((self.world.max_y - self.world.min_y) / 2.0))

	def generateMap(self):
		"""Generates a map."""

		#load map
		game.main.db("attach ':memory:' as map")
		#...
		self.world = World()

		#setup view
		self.view.center(((self.world.max_x - self.world.min_x) / 2.0), ((self.world.max_y - self.world.min_y) / 2.0))
