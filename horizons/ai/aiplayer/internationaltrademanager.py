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

from collections import defaultdict

from mission.internationaltrade import InternationalTrade
from horizons.constants import RES, TRADER
from horizons.util.python import decorators
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent

class InternationalTradeManager(object):
	"""
	An object of this class manages the international trade routes of one AI player.

	The current implementation is limited to one active route between each pair of our
	settlement and another player's settlement where each route can have at most one
	bought and one sold resource. The routes are automatically removed when they have
	been used once or when the ship gets destroyed.
	"""

	log = logging.getLogger("ai.aiplayer.internationaltrade")

	def __init__(self, owner):
		super(InternationalTradeManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.personality = owner.personality_manager.get('InternationalTradeManager')

	def _trade_mission_exists(self, settlement, settlement_manager):
		"""Return a boolean showing whether there is a trade route between the settlements."""
		for mission in self.owner.missions:
			if not isinstance(mission, InternationalTrade):
				continue
			if mission.settlement is settlement and mission.settlement_manager is settlement_manager:
				return True
		return False

	def _add_route(self):
		"""Add a new international trade route if possible."""
		ship = None
		for possible_ship, state in self.owner.ships.iteritems():
			if state is self.owner.shipStates.idle:
				ship = possible_ship
				break
		if not ship:
			#self.log.info('%s international trade: no available ships', self)
			return

		# find all possible legal trade route options
		options = defaultdict(lambda: []) # {(settlement, settlement_manager): (total value, amount, resource id, bool(selling)), ...}
		for settlement in self.world.settlements:
			if settlement.owner is self.owner:
				continue # don't allow routes of this type between the player's own settlements
			for settlement_manager in self.owner.settlement_managers:
				if self._trade_mission_exists(settlement, settlement_manager):
					continue # allow only one international trade route between a pair of settlements
				my_inventory = settlement_manager.settlement.get_component(StorageComponent).inventory
				resource_manager = settlement_manager.resource_manager

				# add the options where we sell to the other player
				for resource_id, limit in settlement.get_component(TradePostComponent).buy_list.iteritems():
					if resource_id not in resource_manager.resource_requirements:
						continue # not a well-known resource: ignore it
					if limit <= settlement.get_component(StorageComponent).inventory[resource_id]:
						continue # they aren't actually buying the resource
					if my_inventory[resource_id] <= resource_manager.resource_requirements[resource_id]:
						continue # my settlement is unable to sell the resource
					price = int(self.session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_SELL)
					tradable_amount = min(my_inventory[resource_id] - resource_manager.resource_requirements[resource_id],
						limit - settlement.get_component(StorageComponent).inventory[resource_id], ship.get_component(StorageComponent).inventory.get_limit(), settlement.owner.get_component(StorageComponent).inventory[RES.GOLD] // price)
					options[(settlement, settlement_manager)].append((tradable_amount * price, tradable_amount, resource_id, True))

				# add the options where we buy from the other player
				for resource_id, limit in settlement.get_component(TradePostComponent).sell_list.iteritems():
					if resource_id not in resource_manager.resource_requirements:
						continue # not a well-known resource: ignore it
					if limit >= settlement.get_component(StorageComponent).inventory[resource_id]:
						continue # they aren't actually selling the resource
					if my_inventory[resource_id] >= resource_manager.resource_requirements[resource_id]:
						continue # my settlement doesn't want to buy the resource
					price = int(self.session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_BUY)
					tradable_amount = min(resource_manager.resource_requirements[resource_id] - my_inventory[resource_id],
						settlement.get_component(StorageComponent).inventory[resource_id] - limit, ship.get_component(StorageComponent).inventory.get_limit(), self.owner.get_component(StorageComponent).inventory[RES.GOLD] // price)
					options[(settlement, settlement_manager)].append((tradable_amount * price, tradable_amount, resource_id, False))
		if not options:
			#self.log.info('%s international trade: no interesting options', self)
			return

		# make up final options where a route is limited to at most one resource bought and one resource sold
		final_options = [] # [(value, bought resource id or None, sold resource id or None, settlement, settlement_manager), ...]
		for (settlement, settlement_manager), option in sorted(options.iteritems()):
			best_buy = None # largest amount of resources
			best_sale = None # most expensive sale
			for total_price, tradable_amount, resource_id, selling in option:
				if selling:
					if best_sale is None or best_sale[0] < total_price:
						best_sale = (total_price, tradable_amount, resource_id)
				else:
					if best_buy is None or best_buy[1] < tradable_amount:
						best_buy = (total_price, tradable_amount, resource_id)
			buy_coefficient = self.personality.buy_coefficient_rich if self.owner.get_component(StorageComponent).inventory[RES.GOLD] > self.personality.little_money else self.personality.buy_coefficient_poor
			total_value = (best_sale[0] if best_sale else 0) + (best_buy[1] if best_buy else 0) * buy_coefficient
			final_options.append((total_value, best_buy[2] if best_buy else None, best_sale[2] if best_sale else None, settlement, settlement_manager))

		bought_resource, sold_resource, settlement, settlement_manager = max(final_options)[1:]
		self.owner.start_mission(InternationalTrade(settlement_manager, settlement, ship, bought_resource, sold_resource, self.owner.report_success, self.owner.report_failure))

	def tick(self):
		self._add_route()

decorators.bind_all(InternationalTradeManager)
