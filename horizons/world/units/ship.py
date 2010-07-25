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
from fife import fife

import horizons.main

from horizons.gui.tabs import ShipInventoryTab, ShipOverviewTab, TraderShipOverviewTab
from horizons.world.storage import PositiveTotalStorage
from horizons.world.storageholder import StorageHolder
from horizons.world.pathfinding.pather import ShipPather
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Point, NamedObject, Circle
from unit import Unit
from horizons.constants import LAYERS

class Ship(NamedObject, StorageHolder, Unit):
	"""Class representing a ship
	@param x: int x position
	@param y: int y position
	"""
	pather_class = ShipPather
	tabs = (ShipOverviewTab, ShipInventoryTab)

	def __init__(self, x, y, **kwargs):
		super(Ship, self).__init__(x=x, y=y, **kwargs)

		self.session.world.ships.append(self)
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def remove(self):
		super(Ship, self).remove()
		self.session.world.ships.remove(self)
		del self.session.world.ship_map[self.position.to_tuple()]

	def create_inventory(self):
		self.inventory = PositiveTotalStorage(200)

	def _move_tick(self):
		"""Keeps track of the ship's position in the global ship_map"""
		del self.session.world.ship_map[self.position.to_tuple()]

		super(Ship, self)._move_tick()

		# save current and next position for ship, since it will be between them
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
		self.session.world.ship_map[self._next_target.to_tuple()] = weakref.ref(self)

	def select(self):
		"""Runs necessary steps to select the unit."""
		self.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		# add a buoy at the ship's target if the player owns the ship
		if self.is_moving() and self.session.world.player == self.owner:
			loc = fife.Location(self.session.view.layers[LAYERS.OBJECTS])
			loc.thisown = 0 # thisown = 0 because the genericrenderernode might delete it
			move_target = self.get_move_target()
			coords = fife.ModelCoordinate(move_target.x, move_target.y)
			coords.thisown = 1 # thisown = 1 because setLayerCoordinates will create a copy
			loc.setLayerCoordinates(coords)
			self.session.view.renderer['GenericRenderer'].addAnimation(
				"buoy_" + str(self.worldid), fife.GenericRendererNode(loc),
				horizons.main.fife.animationpool.addResourceFromFile("as_buoy0-idle-45")
			)
		self.draw_health()

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		self.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		self.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.worldid))
		self.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(self.worldid))

	def go(self, x, y):
		"""Moves the ship.
		This is called when a ship is selected and the right mouse button is pressed outside the ship"""
		self.stop()
		ship_id = self.worldid # this has to happen here,
		# cause a reference to self in a temporary function is implemented
		# as a hard reference, which causes a memory leak
		def tmp():
			if self.session.world.player == self.owner:
				self.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(ship_id))
		tmp()
		move_target = Point(int(round(x)), int(round(y)))
		try:
			self.move(move_target, tmp)
		except MoveNotPossible:
			# find a near tile to move to
			target_found = False
			surrounding = Circle(move_target, radius=0)
			while not target_found and surrounding.radius < 4:
				surrounding.radius += 1
				for move_target in surrounding:
					try:
						self.move(move_target, tmp)
					except MoveNotPossible:
						continue
					target_found = True
					break
		if self.session.world.player == self.owner:
			if self.position.x != move_target.x or self.position.y != move_target.y:
				move_target = self.get_move_target()
			if move_target is not None:
				loc = fife.Location(self.session.view.layers[LAYERS.OBJECTS])
				loc.thisown = 0
				coords = fife.ModelCoordinate(move_target.x, move_target.y)
				coords.thisown = 0
				loc.setLayerCoordinates(coords)
				self.session.view.renderer['GenericRenderer'].addAnimation(
					"buoy_" + str(self.worldid), fife.GenericRendererNode(loc),
					horizons.main.fife.animationpool.addResourceFromFile("as_buoy0-idle-45")
				)

	def _possible_names(self):
		names = self.session.db("SELECT name FROM data.shipnames WHERE for_player = 1")
		return map(lambda x: x[0], names)

	def save(self, db):
		super(Ship, self).save(db)

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)

		# register ship in world
		self.session.world.ships.append(self)
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def find_nearby_ships(self):
		# TODO: Replace 20 with a distance dependant on the ship type and any
		# other conditions.
		ships = self.session.world.get_ships(self.position, 15)
		ships.remove(self)
		return ships

class PirateShip(Ship):
	"""Represents a pirate ship."""
	tabs = ()
	def _possible_names(self):
		names = self.session.db("SELECT name FROM data.shipnames WHERE for_player = 1")
		return map(lambda x: x[0], names)

class TradeShip(Ship):
	"""Represents a trade ship."""
	tabs = ()
	enemy_tabs = (TraderShipOverviewTab, )
	def _possible_names(self):
		return [ _('Trader') ]

class FisherShip(Ship):
	"""Represents a fisher ship."""
	tabs = ()
