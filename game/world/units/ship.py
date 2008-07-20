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
from game.world.storage import Storage
from unit import Unit
from game.world.pathfinding import Movement
from game.util import Point
from game.gui.tabwidget import TabWidget

class Ship(Unit):
	movement = Movement.SHIP_MOVEMENT
	"""Class representing a ship
		@param x: int x position
		@param y: int y position
	"""
	def __init__(self, x, y):
		super(Ship, self).__init__(x, y)
		self.inventory = Storage()
		self.inventory.addSlot(6,50)
		self.inventory.addSlot(5,50)
		self.inventory.addSlot(4,50)
		self.inventory.alter_inventory(6, 15)
		self.inventory.alter_inventory(5, 30)
		self.inventory.alter_inventory(4, 50)
		self.name = str(game.main.db("SELECT name FROM shipnames ORDER BY random() LIMIT 1")[0][0])
		#self.name = str(game.main.db("SELECT name FROM shipnamespirate ORDER BY random() LIMIT 1")[0][0])

	def select(self):
		"""Runs neccesary steps to select the unit."""
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		game.main.session.view.renderer['GenericRenderer'].removeAll(3)
		if self.unit_position.x != self.move_target.x or self.unit_position.y != self.move_target.y:
			loc = fife.Location(game.main.session.view.layers[2])
			loc.thisown = 0
			coords = fife.ModelCoordinate(self.move_target.x, self.move_target.y)
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
		game.main.session.ingame_gui.show_menu(TabWidget(3, self, {'overview_ship':{'foundSettelment': game.main.fife.pychan.tools.callbackWithArguments(game.main.session.ingame_gui._build, 1, self)}}))

	def act(self, x, y):
		def tmp():
			game.main.session.view.renderer['GenericRenderer'].removeAll(3)
		tmp()
		x,y=int(round(x)),int(round(y))
		self.move(Point(x,y), tmp)
		if self.unit_position.x != x or self.unit_position.y != y:
			loc = fife.Location(game.main.session.view.layers[2])
			loc.thisown = 0
			coords = fife.ModelCoordinate(self.move_target.x, self.move_target.y)
			coords.thisown = 0
			loc.setLayerCoordinates(coords)
			game.main.session.view.renderer['GenericRenderer'].addAnimation(3, fife.GenericRendererNode(loc), game.main.fife.animationpool.addResourceFromFile("0"));

class PirateShip(Ship):
	"""Represents a pirate ship."""

	def show_menu(self):
		pass

class TradeShip(Ship):
	"""Represents a trade ship."""

	def show_menu(self):
		pass

class FisherShip(Ship):
	"""Represents a fisher ship."""

	def show_menu(self):
		pass
