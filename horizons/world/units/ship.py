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
import copy
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
from horizons.world.component.healthcomponent import HealthComponent

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

		self.wait_at_load = False # wait until every res has been loaded
		self.wait_at_unload = False #  wait until every res could be unloaded

		self.current_transfer = {} # used for partial unloading in combination with waiting

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
		resource_list = self.current_transfer or self.get_location()['resource_list']

		if self.current_transfer is not None:
			for res in copy.copy(self.current_transfer):
				# make sure we don't keep trying to (un)load something when the decision about that resource has changed
				if self.current_transfer[res] == 0 or res not in self.get_location()['resource_list'] or \
						cmp(self.current_transfer[res], 0) != cmp(self.get_location()['resource_list'][res], 0):
					del self.current_transfer[res]

		settlement = branch_office.settlement
		status = self._transer_resources(settlement, resource_list)
		if (not status.settlement_has_enough_space_to_take_res and self.wait_at_unload) or \
		   (not status.settlement_provides_enough_res and self.wait_at_load):
			self.current_transfer = status.remaining_transfers
			# retry
			Scheduler().add_new_object(self.on_route_bo_reached, self, GAME_SPEED.TICKS_PER_SECOND)
		else:
			self.current_transfer = None
			self.move_to_next_route_bo()

	def _transer_resources(self, settlement, resource_list):
		"""Transfers resources to/from settlement according to list.
		@return: TransferStatus instance
		"""

		class TransferStatus(object):
			def __init__(self):
				self.settlement_provides_enough_res = self.settlement_has_enough_space_to_take_res = True
				self.remaining_transfers = {}

		status = TransferStatus()
		status.remaining_transfers = copy.copy(resource_list)

		for res in resource_list:
			amount = resource_list[res]
			if amount == 0:
				continue

			if amount > 0:
				# load from settlement onto ship
				if settlement.owner is self.ship.owner:
					if settlement.inventory[res] < amount: # not enough res
						amount = settlement.inventory[res]

					# check if ship has enough space is handled implicitly below
					amount_transferred = settlement.transfer_to_storageholder(amount, res, self.ship)
				else:
					amount_transferred = settlement.sell_resource(self.ship.worldid, res, amount)

				if amount_transferred < status.remaining_transfers[res] and self.ship.inventory.get_free_space_for(res) > 0:
					status.settlement_provides_enough_res = False
				status.remaining_transfers[res] -= amount_transferred
			else:
				# load from ship onto settlement
				amount = -amount # use positive below
				if settlement.owner is self.ship.owner:
					if self.ship.inventory[res] < amount: # check if ship has as much as planned
						amount = self.ship.inventory[res]

					if settlement.inventory.get_free_space_for(res) < amount: # too little space
						amount = settlement.inventory.get_free_space_for(res)

					amount_transferred = self.ship.transfer_to_storageholder(amount, res, settlement)
				else:
					amount_transferred = settlement.buy_resource(self.ship.worldid, res, amount)

				if amount_transferred < -status.remaining_transfers[res] and self.ship.inventory[res] > 0:
					status.settlement_has_enough_space_to_take_res = False
				status.remaining_transfers[res] += amount_transferred
		return status

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

	def can_enable(self):
		branch_offices = set()
		for waypoint in self.waypoints:
			branch_offices.add(waypoint['branch_office'])
		return len(branch_offices) > 1

	def enable(self):
		if not self.can_enable():
			return False
		self.enabled = True
		self.move_to_next_route_bo()
		return True

	def disable(self):
		self.enabled = False
		self.ship.stop()

	def clear(self):
		self.waypoints = []
		self.current_waypoint = -1

	@classmethod
	def has_route(self, db, worldid):
		"""Check if a savegame contains route information for a certain ship"""
		return len(db("SELECT * FROM ship_route WHERE ship_id = ?", worldid)) != 0

	def load(self, db):
		enabled, self.current_waypoint, self.wait_at_load, self.wait_at_unload = \
		       db("SELECT enabled, current_waypoint, wait_at_load, wait_at_unload " + \
		          "FROM ship_route WHERE ship_id = ?", self.ship.worldid)[0]

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

		waiting = False
		for res, amount in db("SELECT res, amount FROM ship_route_current_transfer WHERE ship_id = ?", self.ship.worldid):
			waiting = True
			self.current_transfer[res] = amount
			Scheduler().add_new_object(self.on_route_bo_reached, self, GAME_SPEED.TICKS_PER_SECOND)

		if enabled and not waiting:
			self.current_waypoint -= 1
			self.enable()

	def save(self, db):
		worldid = self.ship.worldid

		db("INSERT INTO ship_route(ship_id, enabled, current_waypoint, wait_at_load, wait_at_unload) VALUES(?, ?, ?, ?, ?)",
		   worldid, self.enabled, self.current_waypoint, self.wait_at_load, self.wait_at_unload)

		if self.current_transfer:
			for res, amount in self.current_transfer.iteritems():
				db("INSERT INTO ship_route_current_transfer(ship_id, res, amount) VALUES(?, ?, ?)",
				   worldid, res, amount);

		for entry in self.waypoints:
			index = self.waypoints.index(entry)
			db("INSERT INTO ship_route_waypoint(ship_id, branch_office_id, waypoint_index) VALUES(?, ?, ?)",
			   worldid, entry['branch_office'].worldid, index)
			for res in entry['resource_list']:
				db("INSERT INTO ship_route_resources(ship_id, waypoint_index, res, amount) VALUES(?, ?, ?, ?)",
				   worldid, index, res, entry['resource_list'][res])

	def get_ship_status(self):
		"""Return the current status of the ship."""
		if self.ship.is_moving():
			return _('Trade route: going to %s' % self.ship.get_location_based_status(self.ship.get_move_target()))
		return _('Trade route: waiting at %s' % self.ship.get_location_based_status(self.ship.position))

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

	has_health = True

	in_ship_map = True # (#1023)

	def __init__(self, x, y, **kwargs):
		super(Ship, self).__init__(x=x, y=y, **kwargs)
		self.__init()

	def save(self, db):
		super(Ship, self).save(db)
		if hasattr(self, 'route'):
			self.route.save(db)

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)
		self.__init()

		# if ship did not have route configured, do not add attribute
		if ShipRoute.has_route(db, worldid):
			self.create_route()
			self.route.load(db)

	def __init(self):
		self._selected = False
		# register ship in world
		if self.__class__.has_health:
			self.add_component('health', HealthComponent)
		self.session.world.ships.append(self)
		if self.in_ship_map:
			self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def remove(self):
		super(Ship, self).remove()
		self.session.world.ships.remove(self)
		if self.session.view.has_change_listener(self.draw_health):
			self.session.view.remove_change_listener(self.draw_health)
		if self.in_ship_map:
			del self.session.world.ship_map[self.position.to_tuple()]
			if self._next_target.to_tuple() in self.session.world.ship_map:
				del self.session.world.ship_map[self._next_target.to_tuple()]
			self.in_ship_map = False
		if self._selected:
			self.deselect()
			if self in self.session.selected_instances:
				self.session.selected_instances.remove(self)

	def create_inventory(self):
		self.inventory = PositiveTotalNumSlotsStorage(STORAGE.SHIP_TOTAL_STORAGE, STORAGE.SHIP_TOTAL_SLOTS_NUMBER)

	def create_route(self):
		self.route = ShipRoute(self)

	def _move_tick(self, resume = False):
		"""Keeps track of the ship's position in the global ship_map"""
		if self.in_ship_map:
			del self.session.world.ship_map[self.position.to_tuple()]

		try:
			super(Ship, self)._move_tick(resume)
		except PathBlockedError:
			# if we fail to resume movement then the ship should still be on the map but the exception has to be raised again.
			if resume:
				if self.in_ship_map:
					self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
				raise

		if self.in_ship_map:
			# save current and next position for ship, since it will be between them
			self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
			self.session.world.ship_map[self._next_target.to_tuple()] = weakref.ref(self)

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the unit."""
		self._selected = True
		self.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1, 64)
		# add a buoy at the ship's target if the player owns the ship
		if self.session.world.player == self.owner:
			self._update_buoy()

		self.draw_health()
		if reset_cam:
			self.session.view.center(*self.position.to_tuple())
		self.session.view.add_change_listener(self.draw_health)

	def deselect(self):
		"""Runs necessary steps to deselect the unit."""
		self._selected = False
		self.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		self.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.worldid))
		self.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(self.worldid))
		# this is necessary to make deselect idempotent
		if self.session.view.has_change_listener(self.draw_health):
			self.session.view.remove_change_listener(self.draw_health)

	def go(self, x, y):
		"""Moves the ship.
		This is called when a ship is selected and the right mouse button is pressed outside the ship"""
		self.stop()

		#disable the trading route
		if hasattr(self, 'route'):
			self.route.disable()

		move_target = Point(int(round(x)), int(round(y)))

		try:
			self.move(move_target)
		except MoveNotPossible:
			# find a near tile to move to
			surrounding = Circle(move_target, radius=1)
			# try with smaller circles, increase radius if smaller circle isn't reachable
			while surrounding.radius < 5:
				try:
					self.move(surrounding)
				except MoveNotPossible:
					surrounding.radius += 1
					continue
				break

		if self.get_move_target() is None: # neither target nor surrounding possible
			# TODO: give player some kind of feedback
			pass

	def move(self, *args, **kwargs):
		super(Ship, self).move(*args, **kwargs)
		if self._selected and self.session.world.player == self.owner: # handle buoy
			# if move() is called as move_callback, tmp() from above might
			# be executed after this, so draw the new buoy after move_callbacks have finished.
			Scheduler().add_new_object(self._update_buoy, self, run_in=0)

	def _update_buoy(self):
		"""Draw a buoy at the move target if the ship is moving."""
		move_target = self.get_move_target()
		if move_target != None:
			# set remove buoy callback
			ship_id = self.worldid
			session = self.session # this has to happen here,
			# cause a reference to self in a temporary function is implemented
			# as a hard reference, which causes a memory leak
			def tmp():
				session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(ship_id))
			tmp() # also remove now

			self.add_move_callback(tmp)

			loc = fife.Location(self.session.view.layers[LAYERS.OBJECTS])
			loc.thisown = 0  # thisown = 0 because the genericrenderernode might delete it
			coords = fife.ModelCoordinate(move_target.x, move_target.y)
			coords.thisown = 1 # thisown = 1 because setLayerCoordinates will create a copy
			loc.setLayerCoordinates(coords)
			self.session.view.renderer['GenericRenderer'].addAnimation(
				"buoy_" + str(self.worldid), fife.RendererNode(loc),
				horizons.main.fife.animationloader.loadResource("as_buoy0-idle-45")
			)

	def _possible_names(self):
		names = self.session.db("SELECT name FROM shipnames WHERE for_player = 1")
		# We need unicode strings as the name is displayed on screen.
		return map(lambda x: unicode(x[0], 'utf-8'), names)


	def find_nearby_ships(self, radius=15):
		# TODO: Replace 15 with a distance dependant on the ship type and any
		# other conditions.
		ships = self.session.world.get_ships(self.position, radius)
		if self in ships:
			ships.remove(self)
		return ships

	def get_location_based_status(self, position):
		branch_offices = self.session.world.get_branch_offices(position, self.radius, self.owner, True)
		if branch_offices:
			branch_office = branch_offices[0] # TODO: don't ignore the other possibilities
			player_suffix = ''
			if branch_office.owner is not self.owner:
				player_suffix = ' (' + branch_office.owner.name + ')'
			return branch_office.settlement.name + player_suffix
		return None

	def get_status(self):
		"""Return the current status of the ship."""
		if hasattr(self, 'route') and self.route.enabled:
			return self.route.get_ship_status()
		elif self.is_moving():
			target = self.get_move_target()
			location_based_status = self.get_location_based_status(target)
			if location_based_status is not None:
				return _('Going to %s' % location_based_status)
			return _('Going to %(x)d, %(y)d' % {'x': target.x, 'y': target.y})
		else:
			location_based_status = self.get_location_based_status(self.position)
			if location_based_status is not None:
				return _('Idle at %s' % location_based_status)
			return _('Idle at %(x)d, %(y)d' % {'x': self.position.x, 'y': self.position.y})

class PirateShip(Ship):
	"""Represents a pirate ship."""
	tabs = ()
	def _possible_names(self):
		names = self.session.db("SELECT name FROM shipnames WHERE for_pirate = 1")
		return map(lambda x: unicode(x[0]), names)

class TradeShip(Ship):
	"""Represents a trade ship."""
	tabs = ()
	enemy_tabs = (TraderShipOverviewTab, )
	health_bar_y = -220
	has_health = False

	def __init__(self, x, y, **kwargs):
		super(TradeShip, self).__init__(x, y, **kwargs)

	def _possible_names(self):
		return [ _(u'Trader') ]

class FisherShip(FisherShipCollector, Ship):
	"""Represents a fisher ship."""
	tabs = ()
	pather_class = FisherShipPather
	health_bar_y = -50
	is_selectable = False

	has_health = False

	in_ship_map = False # (#1023)

	def _update_buoy(self):
		pass # no buoy for the fisher
