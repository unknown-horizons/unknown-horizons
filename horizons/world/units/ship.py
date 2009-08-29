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

import weakref
import fife

import horizons.main

from horizons.gui.tabs import TabWidget, ShipInventoryTab, ShipOverviewTab
from horizons.world.storage import PositiveTotalStorage
from horizons.world.pathfinding.pather import ShipPather
from horizons.util import Point, NamedObject
from unit import Unit
from horizons.constants import LAYERS

class Ship(NamedObject, Unit):
	"""Class representing a ship
	@param x: int x position
	@param y: int y position
	"""
	pather_class = ShipPather

	def __init__(self, x, y, **kwargs):
		super(Ship, self).__init__(x=x, y=y, **kwargs)
		print "Creating new ship at:", x, y
		self.setup_inventory()

		horizons.main.session.world.ships.append(self)
		horizons.main.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def remove(self):
		super(Ship, self).remove()
		horizons.main.session.world.ships.remove(self)

	def setup_inventory(self):
		## TODO: inherit from storageholder
		self.inventory = PositiveTotalStorage(200)

	def _move_tick(self):
		"""Keeps track of the ship's position in the global ship_map"""
		del horizons.main.session.world.ship_map[self.position.to_tuple()]

		super(Ship, self)._move_tick()

		# save current and next position for ship, since it will be between them
		horizons.main.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
		horizons.main.session.world.ship_map[self._next_target.to_tuple()] = weakref.ref(self)

	def select(self):
		"""Runs necessary steps to select the unit."""
		horizons.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		if self.is_moving():
			loc = fife.Location(horizons.main.session.view.layers[LAYERS.OBJECTS])
			loc.thisown = 0
			move_target = self.get_move_target()
			coords = fife.ModelCoordinate(move_target.x, move_target.y)
			coords.thisown = 0
			loc.setLayerCoordinates(coords)
			horizons.main.session.view.renderer['GenericRenderer'].addAnimation(
				"buoy_" + str(self.getId()), fife.GenericRendererNode(loc),
				horizons.main.fife.animationpool.addResourceFromFile("as_buoy0-idle-45")
			)
		self.draw_health()

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		horizons.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		horizons.main.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.getId()))
		horizons.main.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(self.getId()))

	def show_menu(self):
		tab = TabWidget(tabs=[ShipOverviewTab(self), ShipInventoryTab(self)])
			#'stock_ship': {
			#	'trade': horizons.main.fife.pychan.tools.callbackWithArguments(horizons.main.session.ingame_gui.show_menu, TradeWidget(self))
			#}
		horizons.main.session.ingame_gui.show_menu(tab)

	def go(self, x, y):
		"""Moves the ship.
		This is called when a ship is selected and the right mouse button is pressed outside the ship"""
		self.stop()
		ship_id = self.getId() # this has to happen here,
		# cause a reference to self in a temporary function is implemented
		# as a hard reference, which causes a memory leak
		def tmp():
			horizons.main.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(ship_id))
		tmp()
		x, y = int(round(x)), int(round(y))
		move_possible = self.move(Point(x, y), tmp)
		if not move_possible:
			return
		if self.position.x != x or self.position.y != y:
			move_target = self.get_move_target()
			if move_target is not None:
				loc = fife.Location(horizons.main.session.view.layers[LAYERS.OBJECTS])
				loc.thisown = 0
				coords = fife.ModelCoordinate(move_target.x, move_target.y)
				coords.thisown = 0
				loc.setLayerCoordinates(coords)
				horizons.main.session.view.renderer['GenericRenderer'].addAnimation(
					"buoy_" + str(self.getId()), fife.GenericRendererNode(loc),
					horizons.main.fife.animationpool.addResourceFromFile("as_buoy0-idle-45")
				)

	def get_default_name(self):
		return horizons.main.db("SELECT name FROM data.shipnames WHERE for_player = 1 ORDER BY random() LIMIT 1")[0][0]

	def save(self, db):
		super(Ship, self).save(db)

		self.inventory.save(db, self.getId())

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)

		self.setup_inventory()
		self.inventory.load(db, worldid)

		# register ship in world
		horizons.main.session.world.ships.append(self)
		horizons.main.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

		return self


class PirateShip(Ship):
	"""Represents a pirate ship."""
	def get_default_name(self):
		return horizons.main.db("SELECT name FROM data.shipnames WHERE for_pirates = 1 ORDER BY random() LIMIT 1")[0][0]

	def show_menu(self):
		pass

	def go(self, x, y):
		pass


class TradeShip(Ship):
	"""Represents a trade ship."""

	def show_menu(self):
		pass

	def go(self, x, y):
		pass

class FisherShip(Ship):
	"""Represents a fisher ship."""

	def show_menu(self):
		pass
