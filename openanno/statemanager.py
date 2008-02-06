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

from openanno.gameview import GameView
from openanno.world import World
from openanno.localcontroller import LocalController
from openanno.player import Player	

instance = None
MAPFILE = 'content/datasets/maps/openanno-test-map.xml'

def init(engine):
	"""Initiailze the global StateManager
	Must be called before using get_instance()"""
	global instance
	instance = StateManager(engine)

def get_instance():
	"""Get the global StateManager instance"""
	global instance
	if instance == None:
		raise Exception("StateManager not initialized")
	return instance

class StateManager(object):
	"""Singleton state manager class
	This class manages the current state of the game and
	switches between states accordingly"""
	
	def __init__(self, engine):
		self.engine = engine
		
		self.engine.getSoundManager().init()

		world = World()
		world.players.append(Player())
		world.local_playerid = 0
		
		controller = LocalController(self.engine, world)
		controller.create_world(MAPFILE)

		self.currentState = GameView(controller)
		self.currentState.adjust_views()
	
	def run(self):
		"""Run the state loop"""
		self.currentState.run()
