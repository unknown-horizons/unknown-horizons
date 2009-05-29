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

import random

import horizons.main

from horizons.util import Point, Callback, WorldObject
from horizons.ext.enum import Enum
from horizons.world.player import Player
from horizons.world.storageholder import StorageHolder

class Trader(Player, StorageHolder):
	"""A trader represents the free trader that travels arround the map with his trading ship(s) and
	sells resources to players and buys resources from them. This is a very simple form of AI, as it
	doesn't do any more then drive to a place on water or a branchoffice randomly and then buys and
	sells resources. A game should not have more then one free trader (it could though)
	@param id: int - player id, every Player needs a unique id, as the freetrader is a Player instance, he also does.
	@param name: Traders name, also needed for the Player class.
	@param color: util.Color instance with the traders banner color, also needed for the Player class"""
	shipStates = Enum('moving_random', 'moving_to_branch', 'reached_branch')

	# amount range to buy/sell from settlement per resource
	buy_amount = (0, 4)
	sell_amount = (1, 4)

	def __init__(self, id, name, color, **kwargs):
		self._init(id, name, color)

		# create a ship and place it randomly (temporary hack)
		(x, y) = horizons.main.session.world.water[random.randint(0, len(horizons.main.session.world.water)-1)]
		self.ships[horizons.main.session.entities.units[6](x, y)] = self.shipStates.reached_branch
		horizons.main.session.scheduler.add_new_object(lambda: self.send_ship_random(self.ships.keys()[0]), self)

	def _init(self, ident, name, color):
		super(Trader, self)._init(id=ident, name=name, color=color)
		self.ships = {} # { ship : state}. used as list of ships and structure to know their state
		self.office = {} # { ship.id : branch }. stores the branch the ship is currently heading to

	def save(self, db):
		super(Trader, self).save(db)

		# mark self as a trader
		db("UPDATE player SET is_trader = 1 WHERE rowid = ?", self.getId())

		for ship in self.ships:
			# prepare values
			ship_state = self.ships[ship]

			remaining_ticks = None
			# get current callback in scheduler, according to ship state, to retrieve
			# the number of ticks, when the call will acctually be done
			current_callback = None
			if ship_state == self.shipStates.reached_branch:
				current_callback = Callback(self.ship_idle, ship)
			if current_callback is not None:
				# current state has a callback
				calls = horizons.main.session.scheduler.get_classinst_calls(self, current_callback)
				assert(len(calls) == 1)
				remaining_ticks = calls.values()[0]

			targeted_branch = None if ship.id not in self.office else self.office[ship.id].getId()

			# put them in the database
			db("INSERT INTO trader_ships(rowid, state, remaining_ticks, targeted_branch) \
			   VALUES(?, ?, ?, ?)", ship.getId(), ship_state.index, remaining_ticks, targeted_branch)

	@classmethod
	def load(cls, db, worldid):
		self = Trader.__new__(Trader)
		self._load(db, worldid)
		return self

	def _load(self, db, worldid):
		super(Trader, self)._load(db, worldid)

		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)
		for ship_id, state_id, remaining_ticks, targeted_branch in \
				db("SELECT rowid, state, remaining_ticks, targeted_branch FROM trader_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)

			self.ships[ship] = state

			if state == self.shipStates.moving_random:
				ship.add_move_callback(lambda: self.ship_idle(ship))
			elif state == self.shipStates.moving_to_branch:
				ship.add_move_callback(lambda: self.reached_branch(ship))
				assert targeted_branch is not None
				self.office[ship.id] = WorldObject.get_object_by_id(targeted_branch)
			elif state == self.shipStates.reached_branch:
				assert remaining_ticks is not None
				horizons.main.session.scheduler.add_new_object( \
					Callback(self.ship_idle, ship), self, remaining_ticks)

	def send_ship_random(self, ship):
		"""Sends a ship to a random position on the map.
		@param ship: Ship instance that is to be used"""
		# find random position
		rand_water_id = random.randint(0, len(horizons.main.session.world.water)-1)
		(x, y) = horizons.main.session.world.water[rand_water_id]
		# move ship there:
		ship.move(Point(x, y), lambda: self.ship_idle(ship))
		self.ships[ship] = self.shipStates.moving_random

	def send_ship_random_branch(self, ship):
		"""Sends a ship to a random branch office on the map
		@param ship: Ship instance that is to be used"""
		# maybe this kind of list should be saved somewhere, as this is pretty performance intense
		branchoffices = horizons.main.session.world.get_branch_offices()
		if len(branchoffices) == 0:
			# there aren't any branch offices, so move randomly
			self.send_ship_random(ship)
		else:
			# select a branch office
			rand = random.randint(0, len(branchoffices)-1)
			self.office[ship.id] = branchoffices[rand]
			for water in horizons.main.session.world.water: # get a position near the branch office
				if Point(water[0],water[1]).distance(self.office[ship.id].position) < 3:
					ship.move(Point(water[0],water[1]), lambda: self.reached_branch(ship))
					self.ships[ship] = self.shipStates.moving_to_branch
					break
			else:
				self.send_ship_random(ship)

	def reached_branch(self, ship):
		"""Actions that need to be taken when reaching a branch office
		@param ship: ship instance"""
		settlement = self.office[ship.id].settlement
		for res, limit in settlement.buy_list.iteritems(): # check for resources that the settlement wants to buy
			rand = random.randint(*self.sell_amount) # select a random amount to sell
			if settlement.inventory[res] >= limit:
				continue # continue if there are more resources in the inventory than the settlement wants to buy
			else:
				alter = rand if limit-settlement.inventory[res] >= rand else limit-settlement.inventory[res]
				ret = settlement.owner.inventory.alter(1, -alter*\
					int(float(horizons.main.db("SELECT value FROM resource WHERE rowid=?",res)[0][0])*1.5))
				if ret == 0: # check if enough money was in the inventory
					settlement.inventory.alter(res, alter)
				else: # if not, return the money taken
					settlement.owner.inventory.alter(1, alter*\
						int(float(horizons.main.db("SELECT value FROM resource WHERE rowid=?",res)[0][0])*1.5)-ret)
		for res, limit in settlement.sell_list.iteritems():
			# select a random amount to buy from the settlement
			rand = random.randint(self.buy_amount[0], \
														min(settlement.inventory.limit-limit, self.buy_amount[1]))
			if settlement.inventory[res] <= limit:
				continue # continue if there are fewer resources in the inventory than the settlement wants to sell
			else:
				alter = -rand if settlement.inventory[res]-limit >= rand else -(settlement.inventory[res]-limit)
				# Pay for bought resources
				settlement.owner.inventory.alter(1, -alter*\
					int(float(horizons.main.db("SELECT value FROM resource WHERE rowid=?",res)[0][0])*0.9))
				settlement.inventory.alter(res, alter)
		del self.office[ship.id]
		# wait 2 seconds before going on to the next island
		horizons.main.session.scheduler.add_new_object(Callback(self.ship_idle, ship), self, 32)
		self.ships[ship] = self.shipStates.reached_branch

	def ship_idle(self, ship):
		"""Called if a ship is idle. Sends ship to a branch office or a random place (which target
		to use is decided by chance, probability for branch office is 2/3)
		@param ship: ship instance"""
		if random.randint(0, 100) < 66:
			# delay one tick, to allow old movement calls to completely finish
			horizons.main.session.scheduler.add_new_object(lambda: self.send_ship_random(ship), self)
		else:
			horizons.main.session.scheduler.add_new_object(lambda: self.send_ship_random_branch(ship), self)
