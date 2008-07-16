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
		#self.name = str(game.main.db("SELECT name FROM shipnamespirate ORDER BY random() LIMIT 1")[0][0])

	def select(self):
		"""Runs neccesary steps to select the unit."""
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		game.main.session.view.renderer['GenericRenderer'].removeAll(3)
		if self.unit_position[0] != self.move_target[0] or self.unit_position[1] != self.move_target[1]:
			loc = fife.Location(game.main.session.view.layers[1])
			loc.thisown = 0
			coords = fife.ModelCoordinate(self.move_target[0], self.move_target[1])
			coords.thisown = 0
			loc.setLayerCoordinates(coords)
			game.main.session.view.renderer['GenericRenderer'].addAnimation(3, fife.GenericRendererNode(loc), game.main.fife.animationpool.addResourceFromFile("0"));
		self.draw_health()

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		game.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		game.main.session.view.renderer['GenericRenderer'].removeAll(2)
		game.main.session.view.renderer['GenericRenderer'].removeAll(3)

	def show_menu(self):
		game.main.session.ingame_gui.show_ship(self) #show the gui for ships

	def act(self, x, y):
		def tmp():
			game.main.session.view.renderer['GenericRenderer'].removeAll(3)
		tmp()
		x,y=int(round(x)),int(round(y))
		self.move(x, y, tmp)
		if self.unit_position[0] != x or self.unit_position[1] != y:
			loc = fife.Location(game.main.session.view.layers[1])
			loc.thisown = 0
			coords = fife.ModelCoordinate(self.move_target[0], self.move_target[1])
			coords.thisown = 0
			loc.setLayerCoordinates(coords)
			game.main.session.view.renderer['GenericRenderer'].addAnimation(3, fife.GenericRendererNode(loc), game.main.fife.animationpool.addResourceFromFile("0"));
