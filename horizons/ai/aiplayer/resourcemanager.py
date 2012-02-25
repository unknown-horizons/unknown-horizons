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

import math

from collections import defaultdict

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.util import WorldObject
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, RES, TRADER
from horizons.command.uioptions import AddToBuyList, RemoveFromBuyList, AddToSellList, RemoveFromSellList
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.tradepostcomponent import TradePostComponent
from horizons.world.component.namedcomponent import NamedComponent
from horizons.world.settlement import Settlement

class ResourceManager(WorldObject):
	"""
	An object of this class manages production capacity and keeps track of over/under stock.

	The main task of this class is to keep track of the available and used production capacity.
	That knowledge is used to figure out how much of the settlement's production
	capacity is being exported and the relevant data is saved accordingly.

	The other important task of this class is to keep track of how much resources the
	settlement should have in inventory and how much it actually has.
	That data is used by this class to make buy/sell decisions in this settlement,
	by InternationalTradeManager to decide which resources to buy/sell at other players'
	warehouses and by SpecialDomesticTradeManager to decide which resources to transfer
	between the player's settlements in order to make best use of them.

	Currently the quota priority system works by assigning local requests a high priority
	and the export requests a low priority which should minimise the amount of resources
	that have to be transferred.

	The division of resources and production capacities is purely logical and does not
	affect the way the actual game works.
	"""

	def __init__(self, settlement_manager):
		super(ResourceManager, self).__init__()
		self.__init(settlement_manager)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self._data = {} # {(resource_id, building_id): SingleResourceManager, ...}
		self._chain = {} # {resource_id: SimpleProductionChainSubtreeChoice, ...} (cache that doesn't have to be saved)
		self._low_priority_requests = {} # {(quota_holder, resource_id): amount, ...} (only used during 1 tick, doesn't have to be saved)
		self._settlement_manager_id = {} # {quota_holder: settlement_manager_id, ...} (cache that doesn't have to be saved)
		self.trade_storage = defaultdict(lambda: defaultdict(lambda: 0)) # {settlement_manager_id: {resource_id: float(amount)}, ...} shows how much of a resource is reserved for a particular settlement
		self.resource_requirements = {} # {resource_id: int(amount), ...} the amount of resource the settlement would like to have in inventory (used to make buy/sell decisions)
		self.personality = self.settlement_manager.owner.personality_manager.get('ResourceManager')

	def save(self, db):
		super(ResourceManager, self).save(db)
		db("INSERT INTO ai_resource_manager(rowid, settlement_manager) VALUES(?, ?)", self.worldid, self.settlement_manager.worldid)
		for resource_manager in self._data.itervalues():
			resource_manager.save(db, self.worldid)
		for settlement_manager_id, reserved_storage in self.trade_storage.iteritems():
			for resource_id, amount in reserved_storage.iteritems():
				if amount > 1e-9:
					db("INSERT INTO ai_resource_manager_trade_storage(resource_manager, settlement_manager, resource, amount) VALUES(?, ?, ?, ?)", \
					   self.worldid, settlement_manager_id, resource_id, amount)
		for resource_id, amount in self.resource_requirements.iteritems():
			db("INSERT INTO ai_resource_manager_requirement(resource_manager, resource, amount) VALUES(?, ?, ?)", self.worldid, resource_id, amount)

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_resource_manager WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(ResourceManager, self).load(db, worldid)
		self.__init(settlement_manager)
		for db_row in db("SELECT rowid, resource_id, building_id FROM ai_single_resource_manager WHERE resource_manager = ?", worldid):
			self._data[(db_row[1], db_row[2])] = SingleResourceManager.load(db, settlement_manager, db_row[0])
		for db_row in db("SELECT settlement_manager, resource, amount FROM ai_resource_manager_trade_storage WHERE resource_manager = ?", worldid):
			self.trade_storage[db_row[0]][db_row[1]] = db_row[2]
		for db_row in db("SELECT resource, amount FROM ai_resource_manager_requirement WHERE resource_manager = ?", worldid):
			self.resource_requirements[db_row[0]] = db_row[1]

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def _get_chain(self, resource_id, resource_producer, production_ratio):
		"""Return a SimpleProductionChainSubtreeChoice or None if it impossible to produce the resource."""
		options = []
		if resource_id in resource_producer:
			for production_line, abstract_building in resource_producer[resource_id]:
				possible = True
				sources = []
				for consumed_resource, amount in production_line.consumed_res.iteritems():
					next_production_ratio = abs(production_ratio * amount / production_line.produced_res[resource_id])
					subtree = self._get_chain(consumed_resource, resource_producer, next_production_ratio)
					if not subtree:
						possible = False
						break
					sources.append(subtree)
				if possible:
					options.append(SimpleProductionChainSubtree(self, resource_id, production_line, abstract_building, sources, production_ratio))
		if not options:
			return None
		return SimpleProductionChainSubtreeChoice(options)

	def _make_chain(self, resource_id):
		"""Return a SimpleProductionChainSubtreeChoice that knows how to produce the resource."""
		resource_producer = {}
		for abstract_building in AbstractBuilding.buildings.itervalues():
			for resource, production_line in abstract_building.lines.iteritems():
				if resource not in resource_producer:
					resource_producer[resource] = []
				resource_producer[resource].append((production_line, abstract_building))
		chain = self._get_chain(resource_id, resource_producer, 1.0)
		chain.assign_identifier('')
		return chain

	def refresh(self):
		"""Refresh the actual production capacity of the buildings and lower quotas if necessary."""
		for resource_manager in self._data.itervalues():
			resource_manager.refresh()

	def request_quota_change(self, quota_holder, priority, resource_id, building_id, amount):
		"""
		Request that the quota of quota_holder be changed to the given amount for the specific resource/building pair.

		@param quota_holder: a string identifying the quota holder (persistent over save/load cycles)
		@param priority: boolean showing whether this quota has high priority (high priority means that low priority quotas can be lowered if necessary)
		@param resource_id: the required resource
		@param building_id: the type of building where this capacity should be gotten from
		@param amount: the amount of resource per tick that is needed
		"""

		key = (resource_id, building_id)
		if key not in self._data:
			self._data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		self._data[key].request_quota_change(quota_holder, priority, amount)

	def get_quota(self, quota_holder, resource_id, building_id):
		"""Return the current quota given the resource and the type of building that should produce it."""
		key = (resource_id, building_id)
		if key not in self._data:
			self._data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		return self._data[key].get_quota(quota_holder)

	def request_deep_quota_change(self, quota_holder, priority, resource_id, amount):
		"""Request that the quota of quota_holder be changed to the given amount recursively."""
		if resource_id not in self._chain:
			self._chain[resource_id] = self._make_chain(resource_id)
		actual_amount = self._chain[resource_id].request_quota_change(quota_holder, amount, priority)
		if not priority:
			self._low_priority_requests[(quota_holder, resource_id)] = actual_amount
		if actual_amount + 1e-9 < amount:
			# release excess production that can't be used
			self._chain[resource_id].request_quota_change(quota_holder, actual_amount, priority)
		return actual_amount

	def get_deep_quota(self, quota_holder, resource_id):
		"""Return the current quota at the bottleneck."""
		if resource_id not in self._chain:
			self._chain[resource_id] = self._make_chain(resource_id)
		return self._chain[resource_id].get_quota(quota_holder)

	def replay_deep_low_priority_requests(self):
		"""Retry adding low priority quota requests. This is required to make the feeder island mechanism work."""
		for (quota_holder, resource_id), amount in self._low_priority_requests.iteritems():
			self.request_deep_quota_change(quota_holder, False, resource_id, amount)

	def record_expected_exportable_production(self, ticks):
		"""Record the amount of production that should be transferred to other islands."""
		for (quota_holder, resource_id), amount in self._low_priority_requests.iteritems():
			if quota_holder not in self._settlement_manager_id:
				self._settlement_manager_id[quota_holder] = WorldObject.get_object_by_id(int(quota_holder[1:].split(',')[0])).settlement_manager.worldid
			self.trade_storage[self._settlement_manager_id[quota_holder]][resource_id] += ticks * amount

	def get_total_export(self, resource_id):
		"""Return the total amount of the given resource being (logically) exported per tick."""
		total = 0
		for resource_manager in self._data.itervalues():
			if resource_manager.resource_id == resource_id:
				total += resource_manager.get_total_export()
		return total

	def get_total_trade_storage(self, resource_id):
		"""Return the amount of the given resource that should be kept aside for other settlements."""
		total = 0
		for settlement_storage in self.trade_storage.itervalues():
			for stored_resource_id, amount in settlement_storage.iteritems():
				if stored_resource_id == resource_id:
					total += amount
		return int(math.ceil(total))

	def get_default_resource_requirement(self, resource_id):
		"""Return the default amount of resource that should be in the settlement inventory."""
		if resource_id in [RES.TOOLS_ID, RES.BOARDS_ID]:
			return self.personality.default_resource_requirement
		elif self.settlement_manager.feeder_island and resource_id == RES.BRICKS_ID:
			return self.personality.default_feeder_island_brick_requirement if self.settlement_manager.owner.settler_level > 0 else 0
		elif not self.settlement_manager.feeder_island and resource_id == RES.FOOD_ID:
			return self.personality.default_food_requirement
		return 0

	def get_unit_building_costs(self, resource_id):
		return 0 # TODO: take into account all the resources that are needed to build units

	def get_required_upgrade_resources(self, resource_id, upgrade_limit):
		"""Return the amount of resource still needed to upgrade at most upgrade_limit residences."""
		limit_left = upgrade_limit
		needed = 0
		for residence in self.settlement_manager.settlement.buildings_by_id.get(BUILDINGS.RESIDENTIAL_CLASS, []):
			if limit_left <= 0:
				break
			production = residence._get_upgrade_production()
			if production is None or production.is_paused():
				continue
			for res, amount in production.get_consumed_resources().iteritems():
				if res == resource_id and residence.get_component(StorageComponent).inventory[resource_id] < abs(amount):
					# TODO: take into account the residence's collector
					needed += abs(amount) - residence.get_component(StorageComponent).inventory[resource_id]
					limit_left -= 1
		return needed

	def get_required_building_resources(self, resource_id):
		return 0 # TODO

	def get_current_resource_requirement(self, resource_id):
		"""Return the amount of resource that should be in the settlement inventory to provide for all needs."""
		currently_reserved = self.get_total_trade_storage(resource_id)
		future_reserve = int(math.ceil(self.get_total_export(resource_id) * self.personality.reserve_time))
		current_usage = int(math.ceil(self.settlement_manager.get_resource_production_requirement(resource_id) * self.personality.reserve_time))
		unit_building_costs = self.get_unit_building_costs(resource_id)
		upgrade_costs = self.get_required_upgrade_resources(resource_id, self.personality.max_upgraded_houses)
		building_costs = self.get_required_building_resources(resource_id)

		total_needed = currently_reserved + future_reserve + current_usage + unit_building_costs + upgrade_costs + building_costs
		return max(total_needed, self.get_default_resource_requirement(resource_id))

	def manager_buysell(self):
		"""Calculate the required inventory levels and make buy/sell decisions based on that."""
		managed_resources = [RES.TOOLS_ID, RES.BOARDS_ID, RES.BRICKS_ID, RES.FOOD_ID, RES.TEXTILE_ID, RES.LIQUOR_ID, RES.TOBACCO_PRODUCTS_ID, RES.SALT_ID]
		settlement = self.settlement_manager.settlement
		assert isinstance(settlement, Settlement)
		inventory = settlement.get_component(StorageComponent).inventory
		session = self.settlement_manager.session
		gold = self.settlement_manager.owner.get_component(StorageComponent).inventory[RES.GOLD_ID]

		buy_sell_list = [] # [(importance (lower is better), resource_id, limit, sell), ...]
		for resource_id in managed_resources:
			current_requirement = self.get_current_resource_requirement(resource_id)
			self.resource_requirements[resource_id] = current_requirement
			max_buy = int(round(current_requirement * self.personality.buy_threshold)) # when to stop buying
			if 0 < current_requirement <= self.personality.low_requirement_threshold: # avoid not buying resources when very little is needed in the first place
				max_buy = current_requirement
			min_sell = int(round(current_requirement * self.personality.sell_threshold)) # when to start selling

			if inventory[resource_id] < max_buy:
				# have 0, need 100, max_buy 67, importance -0.0434
				# have 0, need 30, max_buy 20, importance -0.034
				# have 10, need 30, max_buy 20, importance 0.288
				# have 19, need 30, max_buy 20, importance 0.578
				# have 66, need 100, max_buy 67, importance 0.610
				importance = inventory[resource_id] / float(current_requirement + 1) - math.log(max_buy + 10) / 100
				buy_sell_list.append((importance, resource_id, max_buy, False))
			elif inventory[resource_id] > min_sell:
				price = int(session.db.get_res_value(resource_id) * TRADER.PRICE_MODIFIER_BUY)
				# have 50, need 30, min_sell 40, gold 5000, price 15, importance 0.08625
				# have 100, need 30, min_sell 40, gold 5000, price 15, importance 0.02464
				# have 50, need 30, min_sell 40, gold 0, price 15, importance 0.05341
				# have 50, need 20, min_sell 27, gold 5000, price 15, importance 0.07717
				# have 28, need 20, min_sell 27, gold 5000, price 15, importance 0.23150
				# have 28, need 20, min_sell 27, gold 0, price 15, importance 0.14335
				# have 50, need 30, min_sell 40, gold 10000000, price 15, importance 0.16248
				# have 40, need 30, min_sell 40, gold 5000, price 30, importance 0.04452
				importance = 100.0 / (inventory[resource_id] - min_sell + 10) / (current_requirement + 1) * math.log(gold + 200) / (price + 1)
				buy_sell_list.append((importance, resource_id, min_sell, True))
		if not buy_sell_list:
			return # nothing to buy nor sell

		# discard the less important ones
		buy_sell_list = sorted(buy_sell_list)[:3]
		bought_sold_resources = zip(*buy_sell_list)[1]
		# make sure the right resources are sold and bought with the right limits
		tradepost = settlement.get_component(TradePostComponent)
		sell_list = tradepost.sell_list
		buy_list = tradepost.buy_list
		for resource_id in managed_resources:
			if resource_id in bought_sold_resources:
				limit, sell = buy_sell_list[bought_sold_resources.index(resource_id)][2:]
				if sell and resource_id in buy_list:
					RemoveFromBuyList(tradepost, resource_id).execute(session)
				elif not sell and resource_id in sell_list:
					RemoveFromSellList(tradepost, resource_id).execute(session)
				if sell and (resource_id not in sell_list or sell_list[resource_id] != limit):
					AddToSellList(tradepost, resource_id, limit).execute(session)
				elif not sell and (resource_id not in buy_list or buy_list[resource_id] != limit):
					AddToBuyList(tradepost, resource_id, limit).execute(session)
			else:
				if resource_id in buy_list:
					RemoveFromBuyList(tradepost, resource_id).execute(session)
				elif resource_id in sell_list:
					RemoveFromSellList(tradepost, resource_id).execute(session)

	def finish_tick(self):
		"""Clear data used during a single tick."""
		self._low_priority_requests.clear()

	def __str__(self):
		if not hasattr(self, "settlement_manager"):
			return 'UninitialisedResourceManager'
		result = 'ResourceManager(%s, %d)' % (self.settlement_manager.settlement.get_component(NamedComponent).name, self.worldid)
		for resource_manager in self._data.itervalues():
			res = resource_manager.resource_id
			if res not in [RES.FOOD_ID, RES.TEXTILE_ID, RES.BRICKS_ID]:
				continue
			result += '\n' + resource_manager.__str__()
		return result

class SingleResourceManager(WorldObject):
	"""An object of this class keeps track of the production capacity of a single resource/building type pair of a settlement."""

	epsilon = 1e-7 # epsilon for avoiding problems with miniscule values
	virtual_resources = set([RES.FISH_ID, RES.RAW_CLAY_ID, RES.RAW_IRON_ID]) # resources that are not actually produced by player owned buildings
	virtual_production = 9999 # pretend that virtual resources are always produced in this amount (should be larger than actually needed)

	def __init__(self, settlement_manager, resource_id, building_id):
		super(SingleResourceManager, self).__init__()
		self.__init(settlement_manager, resource_id, building_id)
		self.low_priority = 0.0 # used resource production per tick assigned to low priority holders
		self.available = 0.0 # unused resource production per tick
		self.total = 0.0 # total resource production per tick

	def __init(self, settlement_manager, resource_id, building_id):
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.building_id = building_id
		self.quotas = {} # {quota_holder: (amount, priority), ...}

	def save(self, db, resource_manager_id):
		super(SingleResourceManager, self).save(db)
		db("INSERT INTO ai_single_resource_manager(rowid, resource_manager, resource_id, building_id, low_priority, available, total) VALUES(?, ?, ?, ?, ?, ?, ?)", \
		   self.worldid, resource_manager_id, self.resource_id, self.building_id, self.low_priority, self.available, self.total)
		for identifier, (quota, priority) in self.quotas.iteritems():
			db("INSERT INTO ai_single_resource_manager_quota(single_resource_manager, identifier, quota, priority) VALUES(?, ?, ?, ?)", self.worldid, identifier, quota, priority)

	def _load(self, db, settlement_manager, worldid):
		super(SingleResourceManager, self).load(db, worldid)
		(resource_id, building_id, self.low_priority, self.available, self.total) = \
		    db("SELECT resource_id, building_id, low_priority, available, total FROM ai_single_resource_manager WHERE rowid = ?", worldid)[0]
		self.__init(settlement_manager, resource_id, building_id)

		for (identifier, quota, priority) in db("SELECT identifier, quota, priority FROM ai_single_resource_manager_quota WHERE single_resource_manager = ?", worldid):
			self.quotas[identifier] = (quota, priority)

	@classmethod
	def load(cls, db, settlement_manager, worldid):
		self = cls.__new__(cls)
		self._load(db, settlement_manager, worldid)
		return self

	def _get_current_production(self):
		"""Return the current amount of resource per tick being produced at buildings of this type."""
		if self.resource_id in self.virtual_resources:
			return self.virtual_production
		buildings = self.settlement_manager.settlement.buildings_by_id.get(self.building_id, [])
		return sum(AbstractBuilding.buildings[building.id].get_production_level(building, self.resource_id) for building in buildings)

	def refresh(self):
		"""Adjust the quotas to take into account the current production levels."""
		currently_used = sum(zip(*self.quotas.itervalues())[0])
		self.total = self._get_current_production()
		if self.total + self.epsilon >= currently_used:
			self.available = self.total - currently_used
		else:
			# unable to honour current quota assignments
			self.available = 0.0
			if currently_used - self.total <= self.low_priority and self.low_priority > self.epsilon:
				# the problem can be solved by reducing low priority quotas
				new_low_priority = max(0.0, self.low_priority - (currently_used - self.total))
				multiplier = 0.0 if new_low_priority < self.epsilon else new_low_priority / self.low_priority
				assert 0.0 <= multiplier < 1.0
				for quota_holder, (quota, priority) in self.quotas.iteritems():
					if quota > self.epsilon and not priority:
						self.quotas[quota_holder] = (quota * multiplier, priority)
					elif not priority:
						self.quotas[quota_holder] = (0.0, priority)
				self.low_priority = new_low_priority
			elif currently_used > self.total + self.epsilon:
				# decreasing all high priority quotas equally, removing low priority quotas completely
				multiplier = 0.0 if self.total < self.epsilon else self.total / (currently_used - self.low_priority)
				assert 0.0 <= multiplier < 1.0
				for quota_holder, (quota, priority) in self.quotas.iteritems():
					if quota > self.epsilon and priority:
						self.quotas[quota_holder] = (quota * multiplier, priority)
					else:
						self.quotas[quota_holder] = (0.0, priority)
				self.low_priority = 0.0

	def get_quota(self, quota_holder):
		"""Return the current quota of the given quota holder."""
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = (0.0, False)
		return self.quotas[quota_holder][0]

	def request_quota_change(self, quota_holder, priority, amount):
		"""
		Request that the quota of quota_holder be changed to the given amount.

		The algorithm:
		* if the new amount is less than before: set the new quota to the requested value
		* else if there is enough spare capacity to raise the quota: do it
		* else assign all the spare capacity
			* if this is a high priority request:
				* reduce the low priority quotas to get the maximum possible amount for this quota holder

		@param quota_holder: a string identifying the quota holder (persistent over save/load cycles)
		@param priority: boolean showing whether this quota has high priority (high priority means that low priority quotas can be lowered if necessary)
		@param amount: the amount of resource per tick that is needed
		"""

		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = (0.0, priority)
		amount = max(amount, 0.0)

		if abs(amount - self.quotas[quota_holder][0]) < self.epsilon:
			pass # ignore miniscule change requests
		elif amount < self.quotas[quota_holder][0]:
			# lower the amount of reserved production
			change = self.quotas[quota_holder][0] - amount
			self.available += change
			self.quotas[quota_holder] = (self.quotas[quota_holder][0] - change, priority)
			if not priority:
				self.low_priority -= change
		else:
			if priority and self.available < (amount - self.quotas[quota_holder][0]) and self.low_priority > self.epsilon:
				# can't get the full requested amount but can get more by reusing some of the low priority quotas
				new_low_priority = max(0.0, self.low_priority - (amount - self.quotas[quota_holder][0] - self.available))
				multiplier = 0.0 if new_low_priority < self.epsilon else new_low_priority / self.low_priority
				assert 0.0 <= multiplier < 1.0
				for other_quota_holder, (quota, other_priority) in self.quotas.iteritems():
					if quota > self.epsilon and not other_priority:
						self.quotas[other_quota_holder] = (quota * multiplier, other_priority)
					elif not other_priority:
						self.quotas[other_quota_holder] = (0.0, other_priority)
				self.available += self.low_priority - new_low_priority
				self.low_priority = new_low_priority

			# raise the amount of reserved production as much as possible
			change = min(amount - self.quotas[quota_holder][0], self.available)
			self.available -= change
			self.quotas[quota_holder] = (self.quotas[quota_holder][0] + change, priority)
			if not priority:
				self.low_priority += change

	def get_total_export(self):
		"""Return the total amount of capacity that is reserved by quota holders in other settlements."""
		# this is accurate for now because all trade is set to low priority and nothing else is
		return self.low_priority

	def __str__(self):
		if not hasattr(self, "resource_id"):
			return 'UninitialisedSingleResourceManager'
		result = 'Resource %d production %.5f/%.5f (%.5f low priority)' % (self.resource_id, self.available, self.total, self.low_priority)
		for quota_holder, (quota, priority) in self.quotas.iteritems():
			result += '\n  %squota assignment %.5f to %s' % ('priority ' if priority else '', quota, quota_holder)
		return result

class SimpleProductionChainSubtreeChoice(object):
	"""This is a simple version of ProductionChainSubtreeChoice used to make recursive quotas possible."""

	def __init__(self, options):
		super(SimpleProductionChainSubtreeChoice, self).__init__()
		self.options = options # [SimpleProductionChainSubtree, ...]
		self.resource_id = options[0].resource_id

	def assign_identifier(self, prefix):
		"""Recursively assign an identifier to this subtree to know which subtree owns which resource quota."""
		self.identifier = prefix + ('/choice' if len(self.options) > 1 else '')
		for option in self.options:
			option.assign_identifier(self.identifier)

	def request_quota_change(self, quota_holder, amount, priority):
		"""Try to reserve currently available production. Return the total amount that can be reserved."""
		total_reserved = 0.0
		for option in self.options:
			total_reserved += option.request_quota_change(quota_holder, max(0.0, amount - total_reserved), priority)
		return total_reserved

	def get_quota(self, quota_holder):
		return sum(option.get_quota(quota_holder) for option in self.options)

class SimpleProductionChainSubtree(object):
	"""This is a simple version of ProductionChainSubtree used to make recursive quotas possible."""

	def __init__(self, resource_manager, resource_id, production_line, abstract_building, children, production_ratio):
		super(SimpleProductionChainSubtree, self).__init__()
		self.resource_manager = resource_manager
		self.resource_id = resource_id
		self.production_line = production_line
		self.abstract_building = abstract_building
		self.children = children # [SimpleProductionChainSubtreeChoice, ...]
		self.production_ratio = production_ratio

	def assign_identifier(self, prefix):
		"""Recursively assign an identifier to this subtree to know which subtree owns which resource quota."""
		self.identifier = '%s/%d,%d' % (prefix, self.resource_id, self.abstract_building.id)
		for child in self.children:
			child.assign_identifier(self.identifier)

	def request_quota_change(self, quota_holder, amount, priority):
		"""Try to reserve currently available production. Return the total amount that can be reserved."""
		total_reserved = amount
		for child in self.children:
			total_reserved = min(total_reserved, child.request_quota_change(quota_holder, amount, priority))

		self.resource_manager.request_quota_change(quota_holder + self.identifier, priority, self.resource_id, self.abstract_building.id, amount * self.production_ratio)
		return min(total_reserved, self.resource_manager.get_quota(quota_holder + self.identifier, self.resource_id, self.abstract_building.id) / self.production_ratio)

	def get_quota(self, quota_holder):
		"""Return the current quota at the bottleneck."""
		root_quota = self.resource_manager.get_quota(quota_holder + self.identifier, self.resource_id, self.abstract_building.id) / self.production_ratio
		if self.children:
			return min(root_quota, min(child.get_quota(quota_holder) for child in self.children))
		return root_quota

decorators.bind_all(ResourceManager)
decorators.bind_all(SingleResourceManager)
decorators.bind_all(SimpleProductionChainSubtreeChoice)
decorators.bind_all(SimpleProductionChainSubtree)
