# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import copy

from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import  Circle, WorldObject, ChangeListener
from horizons.constants import GAME_SPEED
from horizons.scheduler import Scheduler
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent, TRADE_ERROR_TYPE

class TradeRoute(ChangeListener):
	"""
	waypoints: list of dicts with the keys
		- warehouse:  a warehouse object
		- resource_list: a {res_id:amount} dict
			- if amount is negative the ship unloads
			- if amount is positive the ship loads

	Change notifications mainly notify about changes of enable.
	"""
	def __init__(self, ship):
		super(TradeRoute, self).__init__()
		self.ship = ship
		self.waypoints = []
		self.current_waypoint = -1
		self.enabled = False

		self.wait_at_load = False # wait until every res has been loaded
		self.wait_at_unload = False #  wait until every res could be unloaded

		self.current_transfer = {} # used for partial unloading in combination with waiting

	def append(self, warehouse_worldid):
		warehouse = WorldObject.get_object_by_id(warehouse_worldid)
		self.waypoints.append({
			'warehouse' : warehouse,
			'resource_list' : {}
		})

	def set_wait_at_load(self, flag):
		self.wait_at_load = flag # as method for commands

	def set_wait_at_unload(self, flag):
		self.wait_at_unload = flag # as methods for commands


	def move_waypoint(self, position, direction):
		was_enabled = self.enabled
		if was_enabled:
			self.disable()

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

		if was_enabled:
			self.enable()

	def remove_waypoint(self, position):
		was_enabled = self.enabled
		if was_enabled:
			self.disable()
		try:
			self.waypoints.pop(position)
		except IndexError:
			pass # usually multiple clicks in short succession with mp delay

		if was_enabled:
			self.enable() # might fail if too few waypoints now

		self._changed()

	def toggle_load_unload(self, position, res_id):
		self.waypoints[position]['resource_list'][res_id] *= -1

	def add_to_resource_list(self, position, res_id, amount):
		self.waypoints[position]['resource_list'][res_id] = amount

	def remove_from_resource_list(self, position, res_id):
		self.waypoints[position]['resource_list'].pop(res_id)

	def on_route_warehouse_reached(self):
		"""Transfer resources, wait if necessary and move to next warehouse when possible"""
		warehouse = self.get_location()['warehouse']
		resource_list = self.current_transfer or self.get_location()['resource_list']
		suppress_messages = self.current_transfer is not None # no messages from  second try on

		if self.current_transfer is not None:
			for res in copy.copy(self.current_transfer):
				# make sure we don't keep trying to (un)load something when the decision about that resource has changed
				if self.current_transfer[res] == 0 or res not in self.get_location()['resource_list'] or \
				   cmp(self.current_transfer[res], 0) != cmp(self.get_location()['resource_list'][res], 0):
					del self.current_transfer[res]

		settlement = warehouse.settlement
		status = self._transfer_resources(settlement, resource_list, suppress_messages)

		if not self.enabled: # got disabled while retrying transfer
			self.current_transfer = None
			return

		if (not status.settlement_has_enough_space_to_take_res and self.wait_at_unload) or \
		   (not status.settlement_provides_enough_res and self.wait_at_load):
			self.current_transfer = status.remaining_transfers
			# retry
			Scheduler().add_new_object(self.on_route_warehouse_reached, self, GAME_SPEED.TICKS_PER_SECOND)
		else:
			self.current_transfer = None
			self.move_to_next_route_warehouse()

	def _transfer_resources(self, settlement, resource_list, suppress_messages=False):
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
					if settlement.get_component(StorageComponent).inventory[res] < amount: # not enough res
						amount = settlement.get_component(StorageComponent).inventory[res]

					# the ship should never pick up more than the number defined in the route config
					if self.ship.get_component(StorageComponent).inventory[res] + amount > self.get_location()['resource_list'][res]:
						amount = self.get_location()['resource_list'][res] - self.ship.get_component(StorageComponent).inventory[res]

					# check if ship has enough space is handled implicitly below
					amount_transferred = settlement.transfer_to_storageholder(amount, res, self.ship)
				else:
					amount_transferred, error = settlement.get_component(TradePostComponent).sell_resource(
					  self.ship.worldid, res, amount,add_error_type=True, suppress_messages=suppress_messages)
					if error == TRADE_ERROR_TYPE.PERMANENT:
						# pretend to have everything and move on, waiting doesn't make sense
						amount_transferred = amount


				inv_comp = self.ship.get_component(StorageComponent)
				if amount_transferred < status.remaining_transfers[res] and \
				   inv_comp.inventory.get_free_space_for(res) > 0 and\
				   inv_comp.inventory[res] < self.get_location()['resource_list'][res]:
					status.settlement_provides_enough_res = False
				status.remaining_transfers[res] -= amount_transferred
			else:
				# load from ship onto settlement
				amount = -amount # use positive below
				if settlement.owner is self.ship.owner:
					if self.ship.get_component(StorageComponent).inventory[res] < amount: # check if ship has as much as planned
						amount = self.ship.get_component(StorageComponent).inventory[res]

					if settlement.get_component(StorageComponent).inventory.get_free_space_for(res) < amount: # too little space
						amount = settlement.get_component(StorageComponent).inventory.get_free_space_for(res)

					amount_transferred = self.ship.transfer_to_storageholder(amount, res, settlement)
				else:
					amount_transferred, error = settlement.get_component(TradePostComponent).buy_resource(
					  self.ship.worldid, res, amount, add_error_type=True, suppress_messages=suppress_messages)
					if error == TRADE_ERROR_TYPE.PERMANENT:
						amount_transferred = amount # is negative

				if amount_transferred < -status.remaining_transfers[res] and self.ship.get_component(StorageComponent).inventory[res] > 0:
					status.settlement_has_enough_space_to_take_res = False
				status.remaining_transfers[res] += amount_transferred
		return status

	def on_ship_blocked(self):
		# the ship was blocked while it was already moving so try again
		self.move_to_next_route_warehouse(advance_waypoint = False)

	def move_to_next_route_warehouse(self, advance_waypoint=True):
		next_destination = self.get_next_destination(advance_waypoint)
		if next_destination == None:
			return

		warehouse = next_destination['warehouse']
		if self.ship.position.distance_to_point(warehouse.position.center()) <= self.ship.radius:
			self.on_route_warehouse_reached()
			return

		try:
			self.ship.move(Circle(warehouse.position.center(), self.ship.radius), self.on_route_warehouse_reached,
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
		warehouses = set()
		for waypoint in self.waypoints:
			warehouses.add(waypoint['warehouse'])
		return len(warehouses) > 1

	def enable(self):
		if not self.can_enable():
			return False
		self.enabled = True
		self.move_to_next_route_warehouse()
		self._changed()
		return True

	def disable(self):
		self.enabled = False
		self.ship.stop()
		self._changed()

	def clear(self):
		self.waypoints = []
		self.current_waypoint = -1

	@classmethod
	def has_route(self, db, worldid):
		"""Check if a savegame contains route information for a certain ship"""
		return len(db("SELECT * FROM ship_route WHERE ship_id = ?", worldid)) != 0

	def load(self, db):
		enabled, self.current_waypoint, self.wait_at_load, self.wait_at_unload = \
			db("SELECT enabled, current_waypoint, wait_at_load, wait_at_unload " +
			   "FROM ship_route WHERE ship_id = ?", self.ship.worldid)[0]

		query = "SELECT warehouse_id FROM ship_route_waypoint WHERE ship_id = ? ORDER BY waypoint_index"
		offices_id = db(query, self.ship.worldid)

		for office_id, in offices_id:
			warehouse = WorldObject.get_object_by_id(office_id)
			query = "SELECT res, amount FROM ship_route_resources WHERE ship_id = ? and waypoint_index = ?"
			resource_list = dict(db(query, self.ship.worldid, len(self.waypoints)))

			self.waypoints.append({
				'warehouse' : warehouse,
				'resource_list' : resource_list
			})

		waiting = False
		for res, amount in db("SELECT res, amount FROM ship_route_current_transfer WHERE ship_id = ?", self.ship.worldid):
			waiting = True
			self.current_transfer[res] = amount
			Scheduler().add_new_object(self.on_route_warehouse_reached, self, GAME_SPEED.TICKS_PER_SECOND)

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
			db("INSERT INTO ship_route_waypoint(ship_id, warehouse_id, waypoint_index) VALUES(?, ?, ?)",
			   worldid, entry['warehouse'].worldid, index)
			for res in entry['resource_list']:
				db("INSERT INTO ship_route_resources(ship_id, waypoint_index, res, amount) VALUES(?, ?, ?, ?)",
				   worldid, index, res, entry['resource_list'][res])

	def get_ship_status(self):
		"""Return the current status of the ship."""
		if self.ship.is_moving():
			#xgettext:python-format
			return (_('Trade route: going to {location}').format(
			           location=self.ship.get_location_based_status(self.ship.get_move_target())),
			        self.ship.get_move_target())
			#xgettext:python-format
		return (_('Trade route: waiting at {position}').format(
		           position=self.ship.get_location_based_status(self.ship.position)),
		        self.ship.position)
