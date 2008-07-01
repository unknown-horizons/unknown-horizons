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
import fife
from game.world.storage import ArbitraryStorage
from unit import Unit

class Ship(Unit):
	"""Class representing a ship
		@param x: int x position
		@param y: int y position
	"""
	def __init__(self, x, y):
		super(Ship, self).__init__(x, y)
		self.inventory = ArbitraryStorage(4, 50)
		self.inventory.alter_inventory(6, 15)
		self.inventory.alter_inventory(5, 30)
		self.inventory.alter_inventory(4, 50)
		self.name = str(game.main.db("SELECT name FROM shipnames ORDER BY random() LIMIT 1")[0][0])
		self.health = 100

	def select(self):
		"""Runs neccesary steps to select the unit."""
		self._instance.say(str(self.health) + '%', 0) # display health over selected ship
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		game.main.session.ingame_gui.show_ship(game.main.session.selected_instance) #show the gui for ships

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		game.main.session.selected_instance._instance.say('') #remove status of last selected unit
		game.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		game.main.session.ingame_gui.toggle_visible('ship') # hide the gui for ships
