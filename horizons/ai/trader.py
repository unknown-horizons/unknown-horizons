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
import logging

import horizons.main

from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject, Circle
from horizons.constants import RES, UNITS, BUILDINGS
from horizons.ai.generic import AIPlayer
from horizons.ext.enum import Enum
from horizons.world.storageholder import StorageHolder
from horizons.world.units.movingobject import MoveNotPossible
from horizons.command.unit import CreateUnit


class Trader(AIPlayer):
	"""A trader represents the free trader that travels around the map with his trading ship(s) and
	sells resources to players and buys resources from them. This is a very simple form of AI, as it
	doesn't do any more then drive to a place on water or a branchoffice randomly and then buys and
	sells resources. A game should not have more then one free trader (it could though)
	@param id: int - player id, every Player needs a unique id, as the freetrader is a Player instance, he also does.
	@param name: Traders name, also needed for the Player class.
	@param color: util.Color instance with the traders banner color, also needed for the Player class"""

	shipStates = Enum.get_extended(AIPlayer.shipStates, 'moving_to_branch', 'reached_branch')

	SELLING_ADDITIONAL_CHARGE = 1.5 # sell at 1.5 times the price
	BUYING_CHARGE_DEDUCTION = 0.9 # buy at 0.9 times the price

	log = logging.getLogger("ai.trader")

	# amount range to buy/sell from settlement per resource
	buy_amount = (2, 6)
	sell_amount = (2, 6)

	_res_values = {} # stores money value of resources. Use only get_res_value() for access

	def __init__(self, session, id, name, color, **kwargs):
		super(Trader, self).__init__(session, id, name, color, **kwargs)
		self.__init()

		# create a ship and place it randomly (temporary hack)
		point = self.session.world.get_random_possible_ship_position()
		ship = CreateUnit(self.getId(), UNITS.TRADER_SHIP_CLASS, point.x, point.y).execute(self.session)
		self.ships[ship] = self.shipStates.reached_branch
		Scheduler().add_new_object(Callback(self.send_ship_random, self.ships.keys()[0]), self)

	def __init(self):
		self.office = {} # { ship.id : branch }. stores the branch the ship is currently heading to
		self.allured_by_signal_fire = {} # bool, used to get away from a signal fire (and not be allured again immediately)

	def save(self, db):
		super(Trader, self).save(db)

		# mark self as a trader
		db("UPDATE player SET is_trader = 1 WHERE rowid = ?", self.getId())

		for ship in self.ships:
			# prepare values
			ship_state = self.ships[ship]

			remaining_ticks = None
			# get current callback in scheduler, according to ship state, to retrieve
			# the number of ticks, when the call will actually be done
			current_callback = None
			if ship_state == self.shipStates.reached_branch:
				current_callback = Callback(self.ship_idle, ship)
			if current_callback is not None:
				# current state has a callback
				calls = Scheduler().get_classinst_calls(self, current_callback)
				assert len(calls) == 1, "got %s calls for saving %s: %s" %(len(calls), current_callback, calls)
				remaining_ticks = max(calls.values()[0], 1)

			targeted_branch = None if ship.id not in self.office else self.office[ship.id].getId()

			# put them in the database
			db("INSERT INTO trader_ships(rowid, state, remaining_ticks, targeted_branch) \
			   VALUES(?, ?, ?, ?)", ship.getId(), ship_state.index, remaining_ticks, targeted_branch)

	def _load(self, db, worldid):
		super(Trader, self)._load(db, worldid)
		self.__init()

	def load_ship_states(self, db):
		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)
		for ship_id, state_id, remaining_ticks, targeted_branch in \
				db("SELECT rowid, state, remaining_ticks, targeted_branch FROM trader_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)

			self.ships[ship] = state

			if state == self.shipStates.moving_random:
				ship.add_move_callback(Callback(self.ship_idle, ship))
			elif state == self.shipStates.moving_to_branch:
				ship.add_move_callback(Callback(self.reached_branch, ship))
				assert targeted_branch is not None
				self.office[ship.id] = WorldObject.get_object_by_id(targeted_branch)
			elif state == self.shipStates.reached_branch:
				assert remaining_ticks is not None
				Scheduler().add_new_object( \
					Callback(self.ship_idle, ship), self, remaining_ticks)

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
		self.log.debug("Trader %s found signal fire %s", ship.getId(), signal_fire)
		# search a branch office in the range of the signal fire and move to it
		branch_offices = self.session.world.get_branch_offices()
		for bo in branch_offices:
			if bo.position.distance(signal_fire.position) <= signal_fire.radius and \
			   bo.owner == signal_fire.owner:
				self.log.debug("Trader %s moving to bo %s", ship.getId(), bo)
				self.allured_by_signal_fire[ship] = True
				# HACK: remove allured flag in a few ticks
				def rem_allured(self, ship): self.allured_by_signal_fire[ship] = False
				Scheduler().add_new_object(Callback(rem_allured, self, ship), self, 20*60*16)
				self.send_ship_random_branch(ship, bo)
				return
		self.log.debug("Trader can't find bo in range of the signal fire")

	def send_ship_random_branch(self, ship, branch_office=None):
		"""Sends a ship to a random branch office on the map
		@param ship: Ship instance that is to be used
		@param branch_office: Branch Office instance to move to. Random one is selected on None."""
		self.log.debug("Trader %s: moving to bo (random=%s)", self.getId(), (branch_office is None))
		# maybe this kind of list should be saved somewhere, as this is pretty performance intense
		branchoffices = self.session.world.get_branch_offices()
		if len(branchoffices) == 0:
			# there aren't any branch offices, so move randomly
			self.send_ship_random(ship)
		else:
			# select a branch office
			if branch_office is None:
				rand = random.randint(0, len(branchoffices)-1)
				self.office[ship.id] = branchoffices[rand]
			else:
				self.office[ship.id] = branch_office
			found_path_to_bo = False
			# try to find a possible position near the bo
			for point in Circle(self.office[ship.id].position.center(), 3):
				try:
					ship.move(point, Callback(self.reached_branch, ship))
				except MoveNotPossible:
					continue
				found_path_to_bo = True
				self.ships[ship] = self.shipStates.moving_to_branch
				break
			if not found_path_to_bo:
				self.send_ship_random(ship)

	def reached_branch(self, ship):
		"""Actions that need to be taken when reaching a branch office
		@param ship: ship instance"""
		self.log.debug("Trader %s: reached bo", self.getId())
		settlement = self.office[ship.id].settlement
		for res in settlement.buy_list.iterkeys(): # check for resources that the settlement wants to buy
			amount = random.randint(*self.sell_amount) # select a random amount to sell
			if amount == 0:
				continue
			price = int(self.get_res_value(res) * self.SELLING_ADDITIONAL_CHARGE * amount)
			settlement.buy(res, amount, price)
			# don't care if he bought it. the trader just offers.
			self.log.debug("Trader %s: offered sell %s tons of res %s", self.getId(), amount, res)

		for res in settlement.sell_list.iterkeys():
			# select a random amount to buy from the settlement
			amount = random.randint(*self.buy_amount)
			if amount == 0:
				continue
			price = int(self.get_res_value(res) * self.BUYING_CHARGE_DEDUCTION * amount)
			settlement.sell(res, amount, price)
			self.log.debug("Trader %s: offered buy %s tons of res %s", self.getId(), amount, res)

		del self.office[ship.id]
		# wait 2 seconds before going on to the next island
		Scheduler().add_new_object(Callback(self.ship_idle, ship), self, Scheduler().get_ticks(4))
		self.ships[ship] = self.shipStates.reached_branch

	def ship_idle(self, ship):
		"""Called if a ship is idle. Sends ship to a branch office or a random place (which target
		to use is decided by chance, probability for branch office is 2/3)
		@param ship: ship instance"""
		if random.randint(0, 100) < 66:
			# delay one tick, to allow old movement calls to completely finish
			self.log.debug("Trader %s: idle, moving to random location", self.getId())
			Scheduler().add_new_object(Callback(self.send_ship_random, ship), self)
		else:
			self.log.debug("Trader %s: idle, moving to random bo", self.getId())
			Scheduler().add_new_object(Callback(self.send_ship_random_branch, ship), self)

	def notify_unit_path_blocked(self, unit):
		self.log.warning("Trader %s: ship blocked", self.getId())
		# retry moving ship in 2 secs
		Scheduler().add_new_object(Callback(self.ship_idle, unit), self, 32)

	@classmethod
	def get_res_value(cls, res):
		"""Returns the money value of a resource"""
		try:
			return cls._res_values[res]
		except KeyError:
			# resource value has yet to be fetched
			cls._res_values[res] = \
					float(horizons.main.db.get_res_value(res))
			return cls._res_values[res]
