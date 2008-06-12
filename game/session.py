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

import game.main

import math
import fife
from game.gui.selectiontool import SelectionTool
from game.world.building import building
from game.world.units.ship import Ship
from game.world.player import Player
from game.gui.ingamegui import IngameGui
from game.gui.ingamekeylistener import IngameKeyListener
from game.world.island import Island
from game.timer import Timer
from game.scheduler import Scheduler
from game.manager import SPManager
from game.view import View
from game.world import World
from game.entities import Entities

class Session(object):
	"""Session class represents the games main ingame view and controls cameras and map loading."""
	def init(self):
		#game
		self.timer = Timer(16)
		game.main.fife.pump.append(self.timer.check_tick)
		self.manager = SPManager()
		self.scheduler = Scheduler()
		self.view = View()
		self.entities = Entities()

		#GUI
		self.ingame_gui = IngameGui()
		self.keylistener = IngameKeyListener()
		self.cursor = SelectionTool()

		#to be (re)moved:
		self.selected_instance = None

	def __del__(self):
		print 'deconstruct',self
		self.ingame_gui.end()
		game.main.fife.pump.remove(self.timer.check_tick)

	def loadMap(self, map):
		"""Loads a map.
		@var map: string with the mapfile path.
		"""

		#load map
		game.main.db("attach ? as map", map)
		self.world = World()

		#setup view
		self.view.center(((self.world.max_x - self.world.min_x) / 2.0), ((self.world.max_y - self.world.min_y) / 2.0))

	def generateMap(self):
		"""Loads a map.
		@var map: string with the mapfile path.
		"""

		#load map
		game.main.db("attach ':memory:' as map")
		#...
		self.world = World()

		#setup view
		self.view.center(((self.world.max_x - self.world.min_x) / 2.0), ((self.world.max_y - self.world.min_y) / 2.0))
