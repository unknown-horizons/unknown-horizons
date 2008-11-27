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

import weakref

import game.main
import fife
from game.world.storage import PositiveTotalStorage
from unit import Unit
from game.world.pathfinding import Movement
from game.util import Point
from game.gui.tabwidget import TabWidget
from game.gui.tradewidget import TradeWidget

class Ship(Unit):
	movement = Movement.SHIP_MOVEMENT
	"""Class representing a ship
		@param x: int x position
		@param y: int y position
	"""
	def __init__(self, x, y, **kwargs):
		super(Ship, self).__init__(x=x, y=y, **kwargs)

		self.setup_inventory()
		self.inventory.alter(5, 50) 	#res:food 	50t
		self.inventory.alter(6, 50) 	#res:tools 	50t
		self.inventory.alter(4, 50) 	#res:boards	50t

		self.set_name()

		game.main.session.world.ships.append(self)
		game.main.session.world.ship_map[self.position] = weakref.ref(self)

	def remove(self):
		super(Ship, self).remove()
		game.main.session.world.ships.remove(self)

	def setup_inventory(self):
		## TODO: inherit from storageholder
		self.inventory = PositiveTotalStorage(200)

	def move_tick(self):
		del game.main.session.world.ship_map[self.position]
		super(Ship, self).move_tick()
		game.main.session.world.ship_map[self.position] = weakref.ref(self)

	def check_for_blocking_units(self, position):
		if position in game.main.session.world.ship_map and game.main.session.world.ship_map[position]() is not self:
			return False
		else:
			return True

	def select(self):
		"""Runs neccesary steps to select the unit."""
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		if self.is_moving():
			loc = fife.Location(game.main.session.view.layers[2])
			loc.thisown = 0
			move_target = self.get_move_target()
			coords = fife.ModelCoordinate(move_target.x, move_target.y)
			coords.thisown = 0
			loc.setLayerCoordinates(coords)
			game.main.session.view.renderer['GenericRenderer'].addAnimation("buoy_" + str(self.getId()), fife.GenericRendererNode(loc), game.main.fife.animationpool.addResourceFromFile("0"))
		self.draw_health()

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		game.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		game.main.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.getId()))
		game.main.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(self.getId()))

	def show_menu(self):
		callbacks = {
			'overview_ship':{
				'foundSettelment': game.main.fife.pychan.tools.callbackWithArguments(game.main.session.ingame_gui._build, 1, weakref.ref(self))
			},
			'stock_ship': {
				'trade': game.main.fife.pychan.tools.callbackWithArguments(game.main.session.ingame_gui.show_menu, TradeWidget(self))
			}
		}
		game.main.session.ingame_gui.show_menu(TabWidget(3, self, callbacks))

	def act(self, x, y):
		"""Moves the ship.
		This is called when a ship is selected and the right mouse button is pressed outside the ship"""
		self.stop()
		ship_id = self.getId() # this has to happen here,
		# cause a reference to self in a temporary function is implemented
		# as a hard reference, which causes a memory leak
		def tmp():
			game.main.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(ship_id))
		tmp()
		x,y=int(round(x)),int(round(y))
		move_possible = self.move(Point(x,y), tmp)
		#move_possible = self.move(Point(x,y))
		if not move_possible:
			return
		if self.position.x != x or self.position.y != y:
			move_target = self.get_move_target()
			if move_target is not None:
				loc = fife.Location(game.main.session.view.layers[2])
				loc.thisown = 0
				coords = fife.ModelCoordinate(move_target.x, move_target.y)
				coords.thisown = 0
				loc.setLayerCoordinates(coords)
				game.main.session.view.renderer['GenericRenderer'].addAnimation("buoy_" + str(self.getId()), fife.GenericRendererNode(loc), game.main.fife.animationpool.addResourceFromFile("0"))

	def set_name(self):
		self.name = game.main.db("SELECT name FROM data.shipnames WHERE for_player = 1 ORDER BY random() LIMIT 1")[0][0]

	def save(self, db):
		super(Ship, self).save(db)

		db("INSERT INTO name (rowid, name) VALUES(?, ?)", self.getId(), self.name)
		self.inventory.save(db, self.getId())

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)

		self.setup_inventory()
		self.setup_inventory()
		self.inventory.load(db, worldid)

		self.name = db("SELECT name FROM name WHERE rowid = ?", worldid)[0][0]

		return self


class PirateShip(Ship):
	"""Represents a pirate ship."""
	def set_name(self):
		self.name = game.main.db("SELECT name FROM data.shipnames WHERE for_pirates = 1 ORDER BY random() LIMIT 1")[0][0]

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
