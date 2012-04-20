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

from horizons.util import WorldObject, ChangeListener
from horizons.constants import RES, TRADER
from horizons.scheduler import Scheduler
from horizons.component.storagecomponent import StorageComponent
from horizons.component import Component

class TRADE_ERROR_TYPE(object):
	"""Machine controlled entities need to know the difference. On this basis, they decide
	whether to retry the trade in a few seconds.
	"""
	NO_ERROR, TEMPORARY, PERMANENT = range(3)

class TradePostComponent(ChangeListener, Component):
	"""This Class has to be inherited by every class that wishes to use BuySellTab and trade with
	the free trader.
	"""
	NAME = 'tradepostcomponent'
	yaml_tag = u'!TradePostComponent'

	def __init__(self):
		super(TradePostComponent, self).__init__()

	def initialize(self):
		self.buy_list = {} # dict of resources that are to be bought. { res_id: limit, .. }
		self.sell_list = {} # dict of resources that are to be sold.  { res_id: limit, .. }
		self.trade_history = [] # [(tick, player_id, resource_id, amount, gold), ...] ordered by tick, player_id
		self.buy_history = {} # { tick_id: (res, amount, price) }
		self.sell_history = {} # { tick_id: (res, amount, price) }
		self.total_income = 0
		self.total_expenses = 0

	def add_to_buy_list(self, res_id, limit):
		self.buy_list[res_id] = limit
		self._changed()

	def remove_from_buy_list(self, res_id):
		if res_id in self.buy_list:
			del self.buy_list[res_id]
			self._changed()

	def add_to_sell_list(self, res_id, limit):
		self.sell_list[res_id] = limit
		self._changed()

	def remove_from_sell_list(self, res_id):
		if res_id in self.sell_list:
			del self.sell_list[res_id]
			self._changed()

	def save(self, db):
		super(TradePostComponent, self).save(db)

		for resource, limit in self.buy_list.iteritems():
			assert limit is not None, "limit must not be none"
			db("INSERT INTO trade_buy(object, resource, trade_limit) VALUES(?, ?, ?)",
				 self.instance.worldid, resource, limit)

		for resource, limit in self.sell_list.iteritems():
			assert limit is not None, "limit must not be none"
			db("INSERT INTO trade_sell(object, resource, trade_limit) VALUES(?, ?, ?)",
				 self.instance.worldid, resource, limit)

		db("INSERT INTO trade_values(object, total_income, total_expenses) VALUES (?, ?, ?)",
		   self.instance.worldid, self.total_income, self.total_expenses)

		for row in self.trade_history:
			translated_tick = row[0] - Scheduler().cur_tick # pre-translate for the loading process
			db("INSERT INTO trade_history(settlement, tick, player, resource_id, amount, gold) VALUES(?, ?, ?, ?, ?, ?)",
				self.instance.worldid, translated_tick, row[1], row[2], row[3], row[4])

	def load(self, db, worldid):
		super(TradePostComponent, self).load(db, worldid)

		self.initialize()

		for (res, limit) in db("SELECT resource, trade_limit FROM trade_buy WHERE object = ?", worldid):
			self.buy_list[res] = limit

		for (res, limit) in db("SELECT resource, trade_limit FROM trade_sell WHERE object = ?", worldid):
			self.sell_list[res] = limit

		self.total_income, self.total_expenses = db("SELECT total_income, total_expenses FROM trade_values WHERE object = ?", worldid)[0]

		for row in db("SELECT tick, player, resource_id, amount, gold FROM trade_history WHERE settlement = ? ORDER BY tick, player", worldid):
			self.trade_history.append(row)

	def get_owner_inventory(self):
		return self.instance.owner.get_component(StorageComponent).inventory

	def get_inventory(self):
		return self.instance.get_component(StorageComponent).inventory

	def buy(self, res, amount, price, player_id):
		"""Buy from the free trader.
		@param res:
		@param amount:
		@param price: cumulative price for whole amount of res
		@param player_id: the worldid of the trade partner
		@return bool, whether we did buy it"""
		assert price >= 0 and amount >= 0
		if not res in self.buy_list or \
		   self.get_owner_inventory()[RES.GOLD] < price or \
		   self.get_inventory().get_free_space_for(res) < amount or \
		   amount + self.get_inventory()[res] > self.buy_list[res]:
			self._changed()
			return False

		else:
			remnant = self.get_owner_inventory().alter(RES.GOLD, -price)
			assert remnant == 0
			remnant = self.get_inventory().alter(res, amount)
			assert remnant == 0
			self.trade_history.append((Scheduler().cur_tick, player_id, res, amount, -price))
			self.buy_history[ Scheduler().cur_tick ] = (res, amount, price)
			self.total_expenses += amount*price
			self._changed()
			return True
		assert False

	def sell(self, res, amount, price, player_id):
		"""Sell to the free trader.
		@param res:
		@param amount:
		@param price: cumulative price for whole amount of res
		@param player_id: the worldid of the trade partner
		@return bool, whether we did sell it"""
		assert price >= 0 and amount >= 0
		if not res in self.sell_list or \
			 self.get_inventory()[res] < amount or \
			 self.get_inventory()[res] - amount < self.sell_list[res]:
			self._changed()
			return False

		else:
			remnant = self.get_owner_inventory().alter(RES.GOLD, price)
			assert remnant == 0
			remnant = self.get_inventory().alter(res, -amount)
			assert remnant == 0
			self.trade_history.append((Scheduler().cur_tick, player_id, res, -amount, price))
			self.sell_history[ Scheduler().cur_tick ] = (res, amount, price)
			self.total_income += amount*price
			self._changed()
			return True
		assert False

	def sell_resource(self, ship_worldid, resource_id, amount, add_error_type=False, suppress_messages=False):
		""" Attempt to sell the given amount of resource to the ship, returns the amount sold.
		@param add_error_type: if True, return tuple where second item is ERROR_TYPE"""
		ship = WorldObject.get_object_by_id(ship_worldid)

		def err(string, err_type):
			if not suppress_messages and ship.owner.is_local_player:
				self.session.ingame_gui.message_widget.add_custom(ship.position.x, ship.position.y, string)
			return 0 if not add_error_type else 0, err_type

		if resource_id not in self.sell_list:
			return err(_("The trade partner does not sell this."), TRADE_ERROR_TYPE.PERMANENT)

		price = int(self.session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_BUY) # price per ton of resource
		assert price > 0

		# can't sell more than the ship can fit in its inventory
		amount = min(amount, ship.get_component(StorageComponent).inventory.get_free_space_for(resource_id))
		if amount <= 0:
			return err(_("You can not store this."), TRADE_ERROR_TYPE.PERMANENT)
		# can't sell more than the ship's owner can afford
		amount = min(amount, ship.owner.get_component(StorageComponent).inventory[RES.GOLD] // price)
		if amount <= 0:
			return err(_("You can not afford to buy this."), TRADE_ERROR_TYPE.TEMPORARY)
		# can't sell more than what we have
		amount = min(amount, self.get_inventory()[resource_id])
		# can't sell more than we are trying to sell according to the settings
		amount = min(amount, self.get_inventory()[resource_id] - self.sell_list[resource_id])
		if amount <= 0:
			return err(_("The trade partner does not sell more of this."), TRADE_ERROR_TYPE.TEMPORARY)

		total_price = price * amount
		assert self.get_owner_inventory().alter(RES.GOLD, total_price) == 0
		assert ship.owner.get_component(StorageComponent).inventory.alter(RES.GOLD, -total_price) == 0
		assert self.get_inventory().alter(resource_id, -amount) == 0
		assert ship.get_component(StorageComponent).inventory.alter(resource_id, amount) == 0
		self.trade_history.append((Scheduler().cur_tick, ship.owner.worldid, resource_id, -amount, total_price))
		self.sell_history[Scheduler().cur_tick] = (resource_id, amount, total_price)
		self.total_income += total_price
		self._changed()
		return amount if not add_error_type else amount, TRADE_ERROR_TYPE.NO_ERROR

	def buy_resource(self, ship_worldid, resource_id, amount, add_error_type=False, suppress_messages=False):
		""" Attempt to buy the given amount of resource from the ship, return the amount bought
		@param add_error_type: if True, return tuple where second item is ERROR_TYPE"""
		ship = WorldObject.get_object_by_id(ship_worldid)

		def err(string, err_type):
			if not suppress_messages and ship.owner.is_local_player:
				self.session.ingame_gui.message_widget.add_custom(ship.position.x, ship.position.y, string)
			return 0 if not add_error_type else 0, err_type

		if resource_id not in self.buy_list:
			return err(_("The trade partner does not buy this."), TRADE_ERROR_TYPE.PERMANENT)

		price = int(self.session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_SELL) # price per ton of resource
		assert price > 0

		# can't buy more than the ship has
		amount = min(amount, ship.get_component(StorageComponent).inventory[resource_id])
		if amount <= 0:
			return err(_("You do not possess this."), TRADE_ERROR_TYPE.PERMANENT)
		# can't buy more than we can fit in the inventory
		amount = min(amount, self.get_inventory().get_free_space_for(resource_id))
		if amount <= 0:
			return err(_("The trade partner can not store more of this."), TRADE_ERROR_TYPE.TEMPORARY)
		# can't buy more than we can afford
		amount = min(amount, self.get_owner_inventory()[RES.GOLD] // price)
		if amount <= 0:
			return err(_("The trade partner can not afford to buy this."), TRADE_ERROR_TYPE.TEMPORARY)

		# can't buy more than we are trying to buy according to the settings
		amount = min(amount, self.buy_list[resource_id] - self.get_inventory()[resource_id])
		if amount <= 0:
			return err(_("The trade partner does not buy more of this."), TRADE_ERROR_TYPE.TEMPORARY)

		total_price = price * amount
		assert self.get_owner_inventory().alter(RES.GOLD, -total_price) == 0
		assert ship.owner.get_component(StorageComponent).inventory.alter(RES.GOLD, total_price) == 0
		assert self.get_inventory().alter(resource_id, amount) == 0
		assert ship.get_component(StorageComponent).inventory.alter(resource_id, -amount) == 0
		self.trade_history.append((Scheduler().cur_tick, ship.owner.worldid, resource_id, amount, -total_price))
		self.buy_history[Scheduler().cur_tick] = (resource_id, amount, total_price)
		self.total_expenses += total_price
		self._changed()
		return amount if not add_error_type else amount, TRADE_ERROR_TYPE.TEMPORARY

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
