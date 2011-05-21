# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.world.pathfinding.pather import ShipPather, FisherShipPather
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Point, NamedObject, Circle
from horizons.world.units.collectors import FisherShipCollector
from unit import Unit
from horizons.command.uioptions import TransferResource
from horizons.constants import LAYERS, STORAGE

class ShipRoute(object):
	"""
	waypoints: list of dicts with the keys
		- branch_office:  a branch office object
		- resource_list: a {res_id:amount} dict
			- if amount is negative the ship unloads
			- if amount is positive the ship loads

	#NOTE new methods need to be added to handle route editing.
	"""
	def __init__(self, ship, waypoints=[]):
		self.ship = ship
		self.waypoints = waypoints                             
		self.current_waypoint = -1
		self.enabled = False

	def append(self, branch_office):
		self.waypoints.append({
		  'branch_office' : branch_office,
		  'resource_list' : {}
		})

	def move_waypoint_down(self, position):
		if position == len(self.waypoints):
			return
		self.waypoints.insert(position+1,self.waypoints.pop(position))

	def move_waypoint_up(self, position):
		if position == 0:
			return
		self.waypoints.insert(position-1,self.waypoints.pop(position))

	def add_to_resource_list(self, position, res_id, amount):
		self.waypoints[position]['resource_list'][res_id] = amount

	def remove_from_resource_list(self, position, res_id):
		self.waypoints[position]['resource_list'].pop(res_id)

	def on_route_bo_reached(self):
		branch_office = self.get_location()['branch_office']
		resource_list = self.get_location()['resource_list']
		settlement = branch_office.settlement
		# if ship and branch office have the same owner, the ship will
		# load/unload resources without paying anything
		if settlement.owner == self.ship.owner:
			for res in resource_list:
				amount = resource_list[res]
				if amount > 0:
					try:
						amount = max(0, amount - self.ship.inventory._storage[res])
					except KeyError:
						pass
					TransferResource (amount, res, branch_office, self.ship).execute(self.ship.session)

				else:
					TransferResource (-amount, res, self.ship, branch_office).execute(self.ship.session)
		self.move_to_next_route_bo()

	def move_to_next_route_bo(self):
		next_destination = self.get_next_destination()
		if next_destination == None:
			return

		branch_office = next_destination['branch_office']
		if self.ship.position.distance_to_point(branch_office.position.center()) <= self.ship.radius:
			self.on_route_bo_reached()
			return

		found_path_to_bo = False

		for point in Circle(branch_office.position.center(), self.ship.radius):
			try:
				self.ship.move(point, self.on_route_bo_reached)
			except MoveNotPossible:
				continue
			found_path_to_bo = True
			break
		if not found_path_to_bo:
			self.disable()

	def get_next_destination(self):
		if not self.enabled:
			return None
		if len(self.waypoints) < 2:
			return None

		self.current_waypoint += 1
		self.current_waypoint %= len(self.waypoints)
		return self.waypoints[self.current_waypoint]

	def get_location(self):
		return self.waypoints[self.current_waypoint]

	def enable(self):
		self.enabled=True
		self.move_to_next_route_bo()

	def disable(self):
		self.enabled=False
		self.ship.stop()

	def clear(self):
		self.waypoints=[]
		self.current_waypoint=-1

class Ship(NamedObject, StorageHolder, Unit):
	"""Class representing a ship
	@param x: int x position
	@param y: int y position
	"""
	pather_class = ShipPather
	tabs = (ShipOverviewTab, ShipInventoryTab)
	health_bar_y = -150
	is_ship = True
	is_selectable = True

	def __init__(self, x, y, **kwargs):
		super(Ship, self).__init__(x=x, y=y, **kwargs)
		self.session.world.ships.append(self)
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def remove(self):
		super(Ship, self).remove()
		self.session.world.ships.remove(self)
		self.session.view.remove_change_listener()
		del self.session.world.ship_map[self.position.to_tuple()]

	def create_inventory(self):
		self.inventory = PositiveTotalStorage(STORAGE.SHIP_TOTAL_STORAGE)

	def create_route(self, waypoints=[]):
		self.route=ShipRoute(self, waypoints)

	def _move_tick(self):
		"""Keeps track of the ship's position in the global ship_map"""
		del self.session.world.ship_map[self.position.to_tuple()]

		super(Ship, self)._move_tick()

		# save current and next position for ship, since it will be between them
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
		self.session.world.ship_map[self._next_target.to_tuple()] = weakref.ref(self)

	def select(self, reset_cam=False):
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
		if reset_cam:
			self.session.view.set_location(self.position.to_tuple())
		self.session.view.add_change_listener(self.draw_health)

	def deselect(self):
		"""Runs necessary steps to deselect the unit."""
		self.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		self.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.worldid))
		self.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(self.worldid))
		self.session.view.remove_change_listener(self.draw_health)

	def go(self, x, y):
		"""Moves the ship.
		This is called when a ship is selected and RMB is pressed outside the ship"""
		self.stop()
		
		#disable the trading route
		if hasattr(self, 'route'):
			self.route.disable()
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
		# We need unicode strings as the name is displayed on screen.
		return map(lambda x: unicode(x[0], 'utf-8'), names)

	def save(self, db):
		super(Ship, self).save(db)

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)

		# register ship in world
		self.session.world.ships.append(self)
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def find_nearby_ships(self, radius=15):
		# TODO: Replace 15 with a distance dependant on the ship type and any
		# other conditions.
		ships = self.session.world.get_ships(self.position, radius)
		ships.remove(self)
		return ships

class PirateShip(Ship):
	"""Represents a pirate ship."""
	tabs = ()
	def _possible_names(self):
		names = self.session.db("SELECT name FROM data.shipnames WHERE for_pirates = 1")
		return map(lambda x: x[0], names)

class TradeShip(Ship):
	"""Represents a trade ship."""
	tabs = ()
	enemy_tabs = (TraderShipOverviewTab, )
	health_bar_y = -220

	def _possible_names(self):
		return [ _('Trader') ]

class FisherShip(FisherShipCollector, Ship):
	"""Represents a fisher ship."""
	tabs = ()
	pather_class = FisherShipPather
	health_bar_y = -50
	is_selectable = False
