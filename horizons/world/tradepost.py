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

from horizons.util import WorldObject
from horizons.constants import RES, TRADER
from horizons.scheduler import Scheduler

class TradePost(object):
	"""This Class has to be inherited by every class that wishes to use BuySellTab and trade with
	the free trader.
	"""
	def __init__(self):
		super(TradePost, self).__init__()
		self.__init()

	def __init(self):
		self.buy_list = {} # dict of resources that are to be bought. { res_id: limit, .. }
		self.sell_list = {} # dict of resources that are to be sold.  { res_id: limit, .. }
		self.buy_history = {} # { tick_id: (res, amount, price) }
		self.sell_history = {} # { tick_id: (res, amount, price) }
		self.total_income = 0
		self.total_expenses = 0

	def add_to_buy_list(self, res_id, limit):
		self.buy_list[res_id] = limit

	def remove_from_buy_list(self, res_id):
		if res_id in self.buy_list:
			del self.buy_list[res_id]

	def add_to_sell_list(self, res_id, limit):
		self.sell_list[res_id] = limit

	def remove_from_sell_list(self, res_id):
		if res_id in self.sell_list:
			del self.sell_list[res_id]

	def save(self, db):
		super(TradePost, self).save(db)

		for resource, limit in self.buy_list.iteritems():
			assert limit is not None, "limit must not be none"
			db("INSERT INTO trade_buy(object, resource, trade_limit) VALUES(?, ?, ?)",
				 self.worldid, resource, limit)

		for resource, limit in self.sell_list.iteritems():
			assert limit is not None, "limit must not be none"
			db("INSERT INTO trade_sell(object, resource, trade_limit) VALUES(?, ?, ?)",
				 self.worldid, resource, limit)

		db("INSERT INTO trade_values(object, total_income, total_expenses) VALUES (?, ?, ?)",
		   self.worldid, self.total_income, self.total_expenses)

	def load(self, db, worldid):
		super(TradePost, self).load(db, worldid)

		self.__init()

		for (res, limit) in db("SELECT resource, trade_limit FROM trade_buy WHERE object = ?", worldid):
			self.buy_list[res] = limit

		for (res, limit) in db("SELECT resource, trade_limit FROM trade_sell WHERE object = ?", worldid):
			self.sell_list[res] = limit

		self.total_income, self.total_expenses = db("SELECT total_income, total_expenses FROM trade_values WHERE object = ?",
		   self.worldid)[0]

	def buy(self, res, amount, price):
		"""Check if we can buy, and process actions to our inventory
		@param res:
		@param amount:
		@param price: cumulative price for whole amount of res
		@return bool, whether we did buy it"""
		assert price >= 0 and amount >= 0
		if not res in self.buy_list or \
		   self.owner.inventory[RES.GOLD_ID] < price or \
		   self.inventory.get_free_space_for(res) < amount or \
		   amount + self.inventory[res] > self.buy_list[res]:
			return False

		else:
			remnant = self.owner.inventory.alter(RES.GOLD_ID, -price)
			assert remnant == 0
			remnant = self.inventory.alter(res, amount)
			assert remnant == 0
			self.buy_history[ Scheduler().cur_tick ] = (res, amount, price)
			self.total_expenses += amount*price
			return True
		assert False

	def sell(self, res, amount, price):
		"""Check if we can sell, and process actions to our inventory
		@param res:
		@param amount:
		@param price: cumulative price for whole amount of res
		@return bool, whether we did sell it"""
		assert price >= 0 and amount >= 0
		if not res in self.sell_list or \
			 self.inventory[res] < amount or \
			 self.inventory[res] - amount < self.sell_list[res]:
			return False

		else:
			remnant = self.owner.inventory.alter(RES.GOLD_ID, price)
			assert remnant == 0
			remnant = self.inventory.alter(res, -amount)
			assert remnant == 0
			self.sell_history[ Scheduler().cur_tick ] = (res, amount, price)
			self.total_income += amount*price
			return True
		assert False

	def sell_resource(self, ship_worldid, resource_id, amount):
		""" Attempt to sell the given amount of resource to the ship, returns the amount sold """
		if resource_id not in self.sell_list:
			return 0
		ship = WorldObject.get_object_by_id(ship_worldid)

		price = int(self.session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_BUY) # price per ton of resource
		assert price > 0

		# can't sell more than what we have
		amount = min(amount, self.inventory[resource_id])
		# can't sell more than the ship can fit in its inventory
		amount = min(amount, ship.inventory.get_free_space_for(resource_id))
		# can't sell more than the ship's owner can afford
		amount = min(amount, ship.owner.inventory[RES.GOLD_ID] // price)
		# can't sell more than we are trying to sell according to the settings
		amount = min(amount, self.inventory[resource_id] - self.sell_list[resource_id])
		if amount <= 0:
			return 0

		total_price = price * amount
		assert self.owner.inventory.alter(RES.GOLD_ID, total_price) == 0
		assert ship.owner.inventory.alter(RES.GOLD_ID, -total_price) == 0
		assert self.inventory.alter(resource_id, -amount) == 0
		assert ship.inventory.alter(resource_id, amount) == 0
		self.sell_history[Scheduler().cur_tick] = (resource_id, amount, total_price)
		self.total_income += total_price
		return amount

	def buy_resource(self, ship_worldid, resource_id, amount):
		""" Attempt to buy the given amount of resource from the ship, return the amount bought """
		if resource_id not in self.buy_list:
			return 0
		ship = WorldObject.get_object_by_id(ship_worldid)

		price = int(self.session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_SELL) # price per ton of resource
		assert price > 0

		# can't buy more than the ship has
		amount = min(amount, ship.inventory[resource_id])
		# can't buy more than we can fit in the inventory
		amount = min(amount, self.inventory.get_free_space_for(resource_id))
		# can't buy more than we can afford
		amount = min(amount, self.owner.inventory[RES.GOLD_ID] // price)
		# can't buy more than we are trying to buy according to the settings
		amount = min(amount, self.buy_list[resource_id] - self.inventory[resource_id])
		if amount <= 0:
			return 0

		total_price = price * amount
		assert self.owner.inventory.alter(RES.GOLD_ID, -total_price) == 0
		assert ship.owner.inventory.alter(RES.GOLD_ID, total_price) == 0
		assert self.inventory.alter(resource_id, amount) == 0
		assert ship.inventory.alter(resource_id, -amount) == 0
		self.buy_history[Scheduler().cur_tick] = (resource_id, amount, total_price)
		self.total_expenses += total_price
		return amount

	@property
	def sell_income(self):
		"""Returns sell income of last month.
		Deletes older entries of the sell list."""
		income = 0
		last_month_start = Scheduler().cur_tick - Scheduler().get_ticks_of_month()
		keys_to_delete = []
		for key, values in self.sell_history.iteritems():
			if key < last_month_start:
				keys_to_delete.append(key)
			else:
				income += values[2]
		# remove old keys
		for key in keys_to_delete:
			del self.sell_history[key]
		return income

	@property
	def buy_expenses(self):
		"""Returns last months buy expenses.
		Deletes older entries of the buy list."""
		expenses = 0
		last_month_start = Scheduler().cur_tick - Scheduler().get_ticks_of_month()
		keys_to_delete = []
		for key, values in self.buy_history.iteritems():
			if key < last_month_start:
				keys_to_delete.append(key)
			else:
				expenses += values[2]
		# remove old keys
		for key in keys_to_delete:
			del self.buy_history[key]
		return expenses

	@property
	def total_earnings(self):
		"""Returns the entire earning of this settlement
		total_earnings = sell_income - buy_expenses"""
		return self.total_income - self.total_expenses
