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

from horizons.ai.aiplayer.mission import ShipMission
from horizons.util import Callback, WorldObject
from horizons.util.python import decorators
from horizons.constants import RES, TRADER
from horizons.command.uioptions import SellResource, BuyResource
from horizons.ext.enum import Enum
from horizons.component.storagecomponent import StorageComponent
from horizons.component.namedcomponent  import NamedComponent
from horizons.component.tradepostcomponent import TradePostComponent

class InternationalTrade(ShipMission):
	"""
	Given a ship, a settlement_manager of our settlement, a settlement of another player,
	and either a resource to be bought or sold (or both) the ship will load/unload the
	required resources at our settlement and do the necessary trading at the other player's one.
	"""

	missionStates = Enum('created', 'moving_to_my_settlement', 'moving_to_other_settlement', 'returning_to_my_settlement')

	def __init__(self, settlement_manager, settlement, ship, bought_resource, sold_resource, success_callback, failure_callback):
		super(InternationalTrade, self).__init__(success_callback, failure_callback, ship)
		assert sold_resource is not None or bought_resource is not None
		self.settlement_manager = settlement_manager
		self.settlement = settlement
		self.bought_resource = bought_resource
		self.sold_resource = sold_resource
		self.state = self.missionStates.created

	def save(self, db):
		super(InternationalTrade, self).save(db)
		db("INSERT INTO ai_mission_international_trade(rowid, settlement_manager, settlement, ship, bought_resource, sold_resource, state) VALUES(?, ?, ?, ?, ?, ?, ?)", \
			self.worldid, self.settlement_manager.worldid, self.settlement.worldid, self.ship.worldid, self.bought_resource, self.sold_resource, self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT settlement_manager, settlement, ship, bought_resource, sold_resource, state FROM ai_mission_international_trade WHERE rowid = ?", worldid)[0]
		self.settlement_manager = WorldObject.get_object_by_id(db_result[0])
		self.settlement = WorldObject.get_object_by_id(db_result[1])
		self.bought_resource = db_result[3]
		self.sold_resource = db_result[4]
		self.state = self.missionStates[db_result[5]]
		super(InternationalTrade, self).load(db, worldid, success_callback, failure_callback, WorldObject.get_object_by_id(db_result[2]))

		if self.state is self.missionStates.moving_to_my_settlement:
			self.ship.add_move_callback(Callback(self._reached_my_settlement))
			self.ship.add_blocked_callback(Callback(self._move_to_my_settlement))
		elif self.state is self.missionStates.moving_to_other_settlement:
			self.ship.add_move_callback(Callback(self._reached_other_settlement))
			self.ship.add_blocked_callback(Callback(self._move_to_other_settlement))
		elif self.state is self.missionStates.returning_to_my_settlement:
			self.ship.add_move_callback(Callback(self._returned_to_my_settlement))
			self.ship.add_blocked_callback(Callback(self._return_to_my_settlement))
		else:
			assert False, 'invalid state'

	def start(self):
		if self.sold_resource is not None:
			self.state = self.missionStates.moving_to_my_settlement
			self._move_to_my_settlement()
		else:
			self.state = self.missionStates.moving_to_other_settlement
			self._move_to_other_settlement()
		self.log.info('%s started an international trade mission between %s and %s to sell %s and buy %s using %s', self, \
			self.settlement_manager.settlement.get_component(NamedComponent).name, self.settlement.get_component(NamedComponent).name, self.sold_resource, self.bought_resource, self.ship)

	def _move_to_my_settlement(self):
		self._move_to_warehouse_area(self.settlement_manager.settlement.warehouse.position, Callback(self._reached_my_settlement), \
			Callback(self._move_to_my_settlement), 'Unable to move to my settlement (%s)' % self.settlement_manager.settlement.get_component(NamedComponent).name)

	def _get_max_sellable_amount(self, available_amount):
		if self.sold_resource not in self.settlement.get_component(TradePostComponent).buy_list:
			return 0
		if self.settlement.get_component(TradePostComponent).buy_list[self.sold_resource] >= self.settlement.get_component(StorageComponent).inventory[self.sold_resource]:
			return 0
		if available_amount <= 0:
			return 0
		price = int(self.owner.session.db.get_res_value(self.sold_resource) * TRADER.PRICE_MODIFIER_SELL)
		return min(self.settlement.get_component(StorageComponent).inventory[self.sold_resource] - self.settlement.get_component(TradePostComponent).buy_list[self.sold_resource],
			self.settlement.owner.get_component(StorageComponent).inventory[RES.GOLD] // price, available_amount)

	def _reached_my_settlement(self):
		self.log.info('%s reached my warehouse area (%s)', self, self.settlement_manager.settlement.get_component(NamedComponent).name)
		available_amount = max(0, self.settlement_manager.settlement.get_component(StorageComponent).inventory[self.sold_resource] - self.settlement_manager.resource_manager.resource_requirements[self.sold_resource])
		sellable_amount = self._get_max_sellable_amount(available_amount)
		if sellable_amount <= 0:
			self.log.info('%s no resources can be sold', self)
			if self.bought_resource is None:
				self.report_failure('No resources need to be sold nor bought')
				return
		else:
			self.move_resource(self.ship, self.settlement_manager.settlement, self.sold_resource, -sellable_amount)
			self.log.info('%s loaded resources', self)
		self.state = self.missionStates.moving_to_other_settlement
		self._move_to_other_settlement()

	def _move_to_other_settlement(self):
		self._move_to_warehouse_area(self.settlement.warehouse.position, Callback(self._reached_other_settlement), \
			Callback(self._move_to_other_settlement), 'Unable to move to the other settlement (%s)' % self.settlement.get_component(NamedComponent).name)

	def _get_max_buyable_amount(self):
		if self.bought_resource is None:
			return 0
		if self.bought_resource not in self.settlement.get_component(TradePostComponent).sell_list:
			return 0
		if self.settlement.get_component(TradePostComponent).sell_list[self.bought_resource] >= self.settlement.get_component(StorageComponent).inventory[self.bought_resource]:
			return 0
		needed_amount = self.settlement_manager.resource_manager.resource_requirements[self.bought_resource] - \
			self.settlement_manager.settlement.get_component(StorageComponent).inventory[self.bought_resource]
		if needed_amount <= 0:
			return 0
		price = int(self.owner.session.db.get_res_value(self.bought_resource) * TRADER.PRICE_MODIFIER_BUY)
		return min(self.settlement.get_component(StorageComponent).inventory[self.bought_resource] - self.settlement.get_component(TradePostComponent).sell_list[self.bought_resource],
			self.settlement_manager.owner.get_component(StorageComponent).inventory[RES.GOLD] // price, needed_amount)

	def _reached_other_settlement(self):
		self.log.info('%s reached the other warehouse area (%s)', self, self.settlement.get_component(NamedComponent).name)
		if self.sold_resource is not None:
			sellable_amount = self._get_max_sellable_amount(self.ship.get_component(StorageComponent).inventory[self.sold_resource])
			if sellable_amount > 0:
				BuyResource(self.settlement.get_component(TradePostComponent), self.ship, self.sold_resource, sellable_amount).execute(self.owner.session)
				if self.bought_resource is None:
					self.report_success('Sold %d of resource %d' % (sellable_amount, self.sold_resource))
					return
				else:
					self.log.info('%s sold %d of resource %d', self, sellable_amount, self.sold_resource)

		buyable_amount = self._get_max_buyable_amount()
		if buyable_amount <= 0:
			self.report_failure('No resources can be bought')
			return

		SellResource(self.settlement.get_component(TradePostComponent), self.ship, self.bought_resource, buyable_amount).execute(self.owner.session)
		self.log.info('%s bought %d of resource %d', self, buyable_amount, self.bought_resource)
		self.state = self.missionStates.returning_to_my_settlement
		self._return_to_my_settlement()

	def _return_to_my_settlement(self):
		self._move_to_warehouse_area(self.settlement_manager.settlement.warehouse.position, Callback(self._returned_to_my_settlement), \
			Callback(self._return_to_my_settlement), 'Unable to return to %s' % self.settlement_manager.settlement.get_component(NamedComponent).name)

	def _returned_to_my_settlement(self):
		self._unload_all_resources(self.settlement_manager.settlement)
		self.report_success('Unloaded the bought resources at %s' % self.settlement_manager.settlement.get_component(NamedComponent).name)

decorators.bind_all(InternationalTrade)
