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
from game.util import livingObject, livingProperty

class Session(livingObject):
	"""Session class represents the games main ingame view and controls cameras and map loading."""
	timer = livingProperty()
	manager = livingProperty()
	scheduler = livingProperty()
	view = livingProperty()
	entities = livingProperty()
	ingame_gui = livingProperty()
	keylistener = livingProperty()
	cursor = livingProperty()

	def begin(self):
		super(Session, self).begin()

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

		self.selected_instances = []

	def end(self):
		self.cursor = None
		self.keylistener = None
		self.ingame_gui = None
		self.entities = None
		self.view = None
		self.scheduler = None
		self.manager = None
		self.timer = None
		super(Session, self).end()

	def loadMap(self, map):
		"""Loads a map.
		@param map: string with the mapfile path.
		"""

		#load map
		game.main.db("attach ? as map", map)
		self.world = World()

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
