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

import logging

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject, Circle
from horizons.constants import UNITS, BUILDINGS, TRADER
from horizons.ai.generic import GenericAI
from horizons.ext.enum import Enum
from horizons.world.units.movingobject import MoveNotPossible
from horizons.command.unit import CreateUnit
from horizons.world.component.tradepostcomponent import TradePostComponent


class Trader(GenericAI):
	"""A trader represents the free trader that travels around the map with its trading ship(s) and
	sells resources to players and buys resources from them. This is a very simple form of AI, as it
	doesn't do any more then drive to a place on water or a warehouse randomly and then buys and
	sells resources. A game should not have more then one free trader (it could though)
	@param id: int - player id, every Player needs a unique id, as the free trader is a Player instance, it also does.
	@param name: Traders name, also needed for the Player class.
	@param color: util.Color instance with the traders banner color, also needed for the Player class"""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'moving_to_warehouse', 'reached_warehouse')

	log = logging.getLogger("ai.trader")
	regular_player = False

	def __init__(self, session, id, name, color, **kwargs):
		super(Trader, self).__init__(session, id, name, color, **kwargs)
		self.__init()
		self.create_ship()

	def create_ship(self):
		"""Create a ship and place it randomly"""
		self.log.debug("Trader %s: creating new ship", self.worldid)
		point = self.session.world.get_random_possible_ship_position()
		ship = CreateUnit(self.worldid, UNITS.TRADER_SHIP_CLASS, point.x, point.y)(issuer=self)
		self.ships[ship] = self.shipStates.reached_warehouse
		Scheduler().add_new_object(Callback(self.ship_idle, ship), self, run_in=0)

	def __init(self):
		self.office = {} # { ship.worldid : warehouse }. stores the warehouse the ship is currently heading to
		self.allured_by_signal_fire = {} # bool, used to get away from a signal fire (and not be allured again immediately)

	def save(self, db):
		super(Trader, self).save(db)

		# mark self as a trader
		db("UPDATE player SET is_trader = 1 WHERE rowid = ?", self.worldid)

		for ship in self.ships:
			# prepare values
			ship_state = self.ships[ship]

			remaining_ticks = None
			# get current callback in scheduler, according to ship state, to retrieve
			# the number of ticks, when the call will actually be done
			current_callback = None
			if ship_state == self.shipStates.reached_warehouse:
				current_callback = Callback(self.ship_idle, ship)
			if current_callback is not None:
				# current state has a callback
				calls = Scheduler().get_classinst_calls(self, current_callback)
				assert len(calls) == 1, "got %s calls for saving %s: %s" %(len(calls), current_callback, calls)
				remaining_ticks = max(calls.values()[0], 1)

			targeted_warehouse = None if ship.worldid not in self.office else self.office[ship.worldid].worldid

			# put them in the database
			db("INSERT INTO trader_ships(rowid, state, remaining_ticks, targeted_warehouse) \
			   VALUES(?, ?, ?, ?)", ship.worldid, ship_state.index, remaining_ticks, targeted_warehouse)

	def _load(self, db, worldid):
		super(Trader, self)._load(db, worldid)
		self.__init()

	def load_ship_states(self, db):
		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)
		for ship_id, state_id, remaining_ticks, targeted_warehouse in \
				db("SELECT rowid, state, remaining_ticks, targeted_warehouse FROM trader_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)

			self.ships[ship] = state

			if state == self.shipStates.moving_random:
				ship.add_move_callback(Callback(self.ship_idle, ship))
			elif state == self.shipStates.moving_to_warehouse:
				ship.add_move_callback(Callback(self.reached_warehouse, ship))
				assert targeted_warehouse is not None
				self.office[ship.worldid] = WorldObject.get_object_by_id(targeted_warehouse)
			elif state == self.shipStates.reached_warehouse:
				assert remaining_ticks is not None
				Scheduler().add_new_object( \
					Callback(self.ship_idle, ship), self, remaining_ticks)

	def get_ship_count(self):
		"""Returns number of ships"""
		return len(self.ships)

	def send_ship_random(self, ship):
		"""Sends a ship to a random position on the map.
		@param ship: Ship instance that is to be used"""
		super(Trader, self).send_ship_random(ship)
		ship.add_conditional_callback(Callback(self._check_for_signal_fire_in_ship_range, ship), \
		                              callback=Callback(self._ship_found_signal_fire, ship))

	def _check_for_signal_fire_in_ship_range(self, ship):
		"""Returns the signal fire instance, if there is one in the ships range, else False"""
		if ship in self.allured_by_signal_fire and self.allured_by_signal_fire[ship]:
			return False # don't visit signal fire again
		for tile in self.session.world.get_tiles_in_radius(ship.position, ship.radius):
			try:
				if tile.object.id == BUILDINGS.SIGNAL_FIRE_CLASS:
					return tile.object
			except AttributeError:
				pass # tile has no object or object has no id
		return False

	def _ship_found_signal_fire(self, ship):
		signal_fire = self._check_for_signal_fire_in_ship_range(ship)
		self.log.debug("Trader %s ship %s found signal fire %s", self.worldid, ship.worldid, signal_fire)
		# search a warehouse in the range of the signal fire and move to it
		warehouses = self.session.world.get_warehouses()
		for house in warehouses:
			if house.position.distance(signal_fire.position) <= signal_fire.radius and \
			   house.owner == signal_fire.owner:
				self.log.debug("Trader %s moving to house %s", self.worldid, house)
				self.allured_by_signal_fire[ship] = True
				# HACK: remove allured flag in a few ticks
				def rem_allured(self, ship): self.allured_by_signal_fire[ship] = False
				Scheduler().add_new_object(Callback(rem_allured, self, ship), self, Scheduler().get_ticks(60))
				self.send_ship_random_warehouse(ship, house)
				return
		self.log.debug("Trader can't find warehouse in range of signal fire")

	def send_ship_random_warehouse(self, ship, warehouse=None):
		"""Sends a ship to a random warehouse on the map
		@param ship: Ship instance that is to be used
		@param warehouse: warehouse instance to move to. Random one is selected on None."""
		self.log.debug("Trader %s ship %s moving to warehouse (random=%s)", self.worldid, ship.worldid, \
		               (warehouse is None))
		# maybe this kind of list should be saved somewhere, as this is pretty performance intense
		warehouses = self.session.world.get_warehouses()
		if len(warehouses) == 0:
			# there aren't any warehouses, so move randomly
			self.send_ship_random(ship)
		else:
			# select a warehouse
			if warehouse is None:
				rand = self.session.random.randint(0, len(warehouses)-1)
				self.office[ship.worldid] = warehouses[rand]
			else:
				self.office[ship.worldid] = warehouse
			# try to find a possible position near the warehouse

			if self.office[ship.worldid] == None:
				# DEBUG output for http://trac.unknown-horizons.org/t/ticket/958
				print "warehouse: ", warehouse
				print "offices: ", [ str(i) for i in warehouses ]
				print "self.office: ", self.office
				print "ship wid: ", ship.worldid
				print "ship: ", ship

			try:
				ship.move(Circle(self.office[ship.worldid].position.center(), ship.radius), Callback(self.reached_warehouse, ship))
				self.ships[ship] = self.shipStates.moving_to_warehouse
			except MoveNotPossible:
				self.send_ship_random(ship)

	def reached_warehouse(self, ship):
		"""Actions that need to be taken when reaching a warehouse
		@param ship: ship instance"""
		self.log.debug("Trader %s ship %s: reached warehouse", self.worldid, ship.worldid)
		settlement = self.office[ship.worldid].settlement
		# NOTE: must be sorted for mp games (same order everywhere)
		trade_comp = settlement.get_component(TradePostComponent)
		for res in sorted(trade_comp.buy_list.iterkeys()): # check for resources that the settlement wants to buy
			wanted_amount = trade_comp.buy_list[res]
			actual_min_limit = min(wanted_amount, TRADER.SELL_AMOUNT_MIN)
			# select a random amount to sell
			amount = self.session.random.randint(actual_min_limit, TRADER.SELL_AMOUNT_MAX)
			if amount == 0:
				continue
			price = int(self.session.db.get_res_value(res) * TRADER.PRICE_MODIFIER_SELL * amount)
			trade_comp.buy(res, amount, price, self.worldid)
			# don't care if it has been bought. the trader just offers.
			self.log.debug("Trader %s: offered sell %s tons of res %s", self.worldid, amount, res)

		# NOTE: must be sorted for mp games (same order everywhere)
		for res in sorted(trade_comp.sell_list.iterkeys()):
			# select a random amount to buy from the settlement
			amount = self.session.random.randint(*TRADER.BUY_AMOUNT)
			if amount == 0:
				continue
			price = int(self.session.db.get_res_value(res) * TRADER.PRICE_MODIFIER_BUY * amount)
			trade_comp.sell(res, amount, price, self.worldid)
			self.log.debug("Trader %s: offered buy %s tons of res %s", self.worldid, amount, res)

		del self.office[ship.worldid]
		# wait 2 seconds before going on to the next island
		Scheduler().add_new_object(Callback(self.ship_idle, ship), self, \
		                           Scheduler().get_ticks(TRADER.TRADING_DURATION))
		self.ships[ship] = self.shipStates.reached_warehouse

	def ship_idle(self, ship):
		"""Called if a ship is idle. Sends ship to a random place or  warehouse (which target
		to use is decided by chance, probability for warehouse (BUSINESS_S.) is 2/3 by default)
		@param ship: ship instance"""
		if self.session.random.randint(0, 100) < TRADER.BUSINESS_SENSE:
			# delay one tick, to allow old movement calls to completely finish
			self.log.debug("Trader %s ship %s: idle, moving to random warehouse", self.worldid, ship.worldid)
			Scheduler().add_new_object(Callback(self.send_ship_random_warehouse, ship), self, run_in=0)
		else:
			self.log.debug("Trader %s ship %s: idle, moving to random location", self.worldid, ship.worldid)
			Scheduler().add_new_object(Callback(self.send_ship_random, ship), self, run_in=0)
