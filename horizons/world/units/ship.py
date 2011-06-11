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

from horizons.gui.tabs import ShipInventoryTab, ShipOverviewTab, \
                              TraderShipOverviewTab, EnemyShipOverviewTab
from horizons.world.storage import PositiveTotalNumSlotsStorage
from horizons.world.storageholder import StorageHolder
from horizons.world.pathfinding.pather import ShipPather, FisherShipPather
from horizons.world.pathfinding import PathBlockedError
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Point, NamedObject, Circle, WorldObject
from horizons.world.units.collectors import FisherShipCollector
from unit import Unit
from horizons.command.uioptions import TransferResource
from horizons.constants import LAYERS, STORAGE, GAME_SPEED
from horizons.scheduler import Scheduler


class ShipRoute(object):
	"""
	waypoints: list of dicts with the keys
		- branch_office:  a branch office object
		- resource_list: a {res_id:amount} dict
			- if amount is negative the ship unloads
			- if amount is positive the ship loads

	#NOTE new methods need to be added to handle route editing.
	"""
	def __init__(self, ship):
		self.ship = ship
		self.waypoints = []
		self.current_waypoint = -1
		self.enabled = False

	def append(self, branch_office):
		self.waypoints.append({
		  'branch_office' : branch_office,
		  'resource_list' : {}
		})

	def move_waypoint(self, position, direction):
		if position == len(self.waypoints) and direction is 'down' or \
		   position == 0 and direction is 'up':
			return
		if direction is 'up':
			new_pos = position - 1
		elif direction is 'down':
			new_pos = position + 1
		else:
			return
		self.waypoints.insert(new_pos, self.waypoints.pop(position))

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

	def on_ship_blocked(self):
		# the ship was blocked while it was already moving so try again
		self.move_to_next_route_bo(advance_waypoint = False)

	def move_to_next_route_bo(self, advance_waypoint = True):
		next_destination = self.get_next_destination(advance_waypoint)
		if next_destination == None:
			return

		branch_office = next_destination['branch_office']
		if self.ship.position.distance_to_point(branch_office.position.center()) <= self.ship.radius:
			self.on_route_bo_reached()
			return

		try:
			self.ship.move(Circle(branch_office.position.center(), self.ship.radius), self.on_route_bo_reached,
				blocked_callback = self.on_ship_blocked)
		except MoveNotPossible:
			# retry in 5 seconds
			Scheduler().add_new_object(self.on_ship_blocked, self, GAME_SPEED.TICKS_PER_SECOND * 5)

	def get_next_destination(self, advance_waypoint):
		if not self.enabled:
			return None
		if len(self.waypoints) < 2:
			return None

		if advance_waypoint:
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

	def load(self, db):
		enabled, self.current_waypoint = db("SELECT enabled, current_waypoint FROM ship_route WHERE ship_id = ?", self.ship.worldid)[0]

		query = "SELECT branch_office_id FROM ship_route_waypoint WHERE ship_id = ? ORDER BY waypoint_index"
		offices_id = db(query, self.ship.worldid)

		for office_id, in offices_id:
			branch_office = WorldObject.get_object_by_id(office_id)
			query = "SELECT res, amount FROM ship_route_resources WHERE ship_id = ? and waypoint_index = ?"
			resource_list = dict(db(query, self.ship.worldid, len(self.waypoints)))

			self.waypoints.append({
			  'branch_office' : branch_office,
			  'resource_list' : resource_list
			})

		if enabled:
			self.current_waypoint -= 1
			self.enable()

	def save(self, db):
		worldid = self.ship.worldid
		db("INSERT INTO ship_route(ship_id, enabled, current_waypoint) VALUES(?, ?, ?)",
		   worldid, self.enabled, self.current_waypoint)
		for entry in self.waypoints:
			index = self.waypoints.index(entry)
			db("INSERT INTO ship_route_waypoint(ship_id, branch_office_id, waypoint_index) VALUES(?, ?, ?)",
			   worldid, entry['branch_office'].worldid, index)
			for res in entry['resource_list']:
				db("INSERT INTO ship_route_resources(ship_id, waypoint_index, res, amount) VALUES(?, ?, ?, ?)",
				   worldid, index, res, entry['resource_list'][res])

class Ship(NamedObject, StorageHolder, Unit):
	"""Class representing a ship
	@param x: int x position
	@param y: int y position
	"""
	pather_class = ShipPather
	tabs = (ShipOverviewTab, ShipInventoryTab, )
	enemy_tabs = (EnemyShipOverviewTab, )
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
		self.inventory = PositiveTotalNumSlotsStorage(STORAGE.SHIP_TOTAL_STORAGE, STORAGE.SHIP_TOTAL_SLOTS_NUMBER)

	def create_route(self):
		self.route=ShipRoute(self)

	def _move_tick(self, resume = False):
		"""Keeps track of the ship's position in the global ship_map"""
		del self.session.world.ship_map[self.position.to_tuple()]

		try:
			super(Ship, self)._move_tick(resume)
		except PathBlockedError:
			# if we fail to resume movement then the ship should still be on the map but the exception has to be raised again.
			if resume:
				self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
			raise

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
		if hasattr(self, 'route'):
			self.route.save(db)

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)

		# register ship in world
		self.session.world.ships.append(self)
		self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

		# if ship did not have route configured, do not add attribute
		if len(db("SELECT * FROM ship_route WHERE ship_id = ?", self.worldid)) is 0:
			return
		self.create_route()
		self.route.load(db)

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
		names = self.session.db("SELECT name FROM data.shipnames WHERE for_pirate = 1")
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
