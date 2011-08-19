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

import math
import logging

from collections import defaultdict

from mission.domestictrade import DomesticTrade

from building import AbstractBuilding
from horizons.util import Circle, WorldObject
from horizons.util.worldobject import WorldObjectNotFound
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, RES

class TradeManager(WorldObject):
	"""
	An object of this class manages the continuous domestic resource import process of one settlement.
	"""

	log = logging.getLogger("ai.aiplayer.trademanager")
	legal_resources = [RES.FOOD_ID, RES.TEXTILE_ID, RES.LIQUOR_ID, RES.BRICKS_ID]

	def __init__(self, settlement_manager):
		super(TradeManager, self).__init__()
		self.__init(settlement_manager)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self.owner = settlement_manager.owner
		self.data = {} # resource_id: SingleResourceTradeManager
		self.ships_sent = defaultdict(lambda: 0) # {settlement_manager_id: num_sent, ...}

	def save(self, db):
		super(TradeManager, self).save(db)
		db("INSERT INTO ai_trade_manager(rowid, settlement_manager) VALUES(?, ?)", self.worldid, self.settlement_manager.worldid)
		for resource_manager in self.data.itervalues():
			resource_manager.save(db, self.worldid)

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_trade_manager WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		self.__init(settlement_manager)
		for db_row in db("SELECT rowid, resource_id FROM ai_single_resource_trade_manager WHERE trade_manager = ?", worldid):
			self.data[db_row[1]] = SingleResourceTradeManager.load(db, settlement_manager, db_row[0])
		super(TradeManager, self).load(db, worldid)

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def refresh(self):
		for resource_manager in self.data.itervalues():
			resource_manager.refresh()

	def finalize_requests(self):
		for resource_manager in self.data.itervalues():
			resource_manager.finalize_requests()

	def request_quota_change(self, quota_holder, resource_id, amount):
		if resource_id not in self.legal_resources:
			return
		if resource_id not in self.data:
			self.data[resource_id] = SingleResourceTradeManager(self.settlement_manager, resource_id)
		self.data[resource_id].request_quota_change(quota_holder, amount)

	def get_quota(self, quota_holder, resource_id):
		if resource_id not in self.legal_resources:
			return 0.0
		if resource_id not in self.data:
			self.data[resource_id] = SingleResourceTradeManager(self.settlement_manager, resource_id)
		return self.data[resource_id].get_quota(quota_holder)

	def get_total_import(self, resource_id):
		if resource_id not in self.legal_resources:
			return 0.0
		if resource_id not in self.data:
			self.data[resource_id] = SingleResourceTradeManager(self.settlement_manager, resource_id)
		return self.data[resource_id].get_total_import()

	def load_resources(self, destination_settlement_manager, ship):
		""" the given ship has arrived at the source settlement to pick up the resources required by this trade manager """
		total_amount = defaultdict(lambda: 0)
		resource_manager = self.settlement_manager.resource_manager
		for resource_id, amount in resource_manager.trade_storage[destination_settlement_manager.worldid].iteritems():
			available_amount = int(min(math.floor(amount), self.settlement_manager.settlement.inventory[resource_id]))
			if available_amount > 0:
				total_amount[resource_id] += available_amount

		destination_inventory = destination_settlement_manager.settlement.inventory
		any_transferred = False
		for resource_id, amount in total_amount.iteritems():
			actual_amount = amount - ship.inventory[resource_id]
			actual_amount = min(actual_amount, destination_inventory.get_limit(resource_id) - destination_inventory[resource_id])
			if actual_amount <= 0:
				continue # TODO: consider unloading the resources if there is more than needed
			any_transferred = True
			self.log.info('Transfer %d of %d to %s for a journey from %s to %s, total amount %d', actual_amount, \
				resource_id, ship, self.settlement_manager.settlement.name, destination_settlement_manager.settlement.name, amount)
			old_amount = self.settlement_manager.settlement.inventory[resource_id]
			self.settlement_manager.owner.complete_inventory.move(ship, self.settlement_manager.settlement, resource_id, -actual_amount)
			actually_transferred = old_amount - self.settlement_manager.settlement.inventory[resource_id]
			resource_manager.trade_storage[destination_settlement_manager.worldid][resource_id] -= actually_transferred

		destination_settlement_manager.trade_manager.ships_sent[self.settlement_manager.worldid] -= 1
		return any_transferred

	def _get_source_settlement_manager(self):
		options = [] # (available resource amount, available number of resources, settlement_manager_id)
		for settlement_manager in self.owner.settlement_managers:
			if settlement_manager is self.settlement_manager:
				continue
			resource_manager = settlement_manager.resource_manager
			num_resources = 0
			total_amount = 0
			for resource_id, amount in resource_manager.trade_storage[self.settlement_manager.worldid].iteritems():
				available_amount = int(min(math.floor(amount), settlement_manager.settlement.inventory[resource_id]))
				if available_amount > 0:
					num_resources += 1
					total_amount += available_amount
			ships_needed = int(max(math.ceil(num_resources / 4.0), math.ceil(total_amount / 120.0)))
			if ships_needed > self.ships_sent[settlement_manager.worldid]:
				self.log.info('have %d ships, need %d ships, %d resource types, %d total amount', self.ships_sent[settlement_manager.worldid], ships_needed, num_resources, total_amount)
				options.append((total_amount - 120 * self.ships_sent[settlement_manager.worldid], num_resources - 4 * self.ships_sent[settlement_manager.worldid], settlement_manager.worldid))
		return None if not options else WorldObject.get_object_by_id(max(options)[2])

	def organize_shipping(self):
		source_settlement_manager = self._get_source_settlement_manager()
		if source_settlement_manager is None:
			return # no trade ships needed

		# need to get a ship
		chosen_ship = None
		for ship, ship_state in sorted(self.owner.ships.iteritems()):
			if ship_state is self.owner.shipStates.idle:
				chosen_ship = ship
		if chosen_ship is None:
			self.owner.request_ship()
			return # no available ships

		self.owner.ships[chosen_ship] = self.owner.shipStates.on_a_mission
		mission = DomesticTrade(source_settlement_manager, self.settlement_manager, chosen_ship, self.owner.report_success, self.owner.report_failure)
		self.owner.missions.add(mission)
		mission.start()
		self.ships_sent[source_settlement_manager.worldid] += 1

	def __str__(self):
		result = 'TradeManager(%s, %d)' % (self.settlement_manager.settlement.name if hasattr(self.settlement_manager, 'settlement') else 'unknown', self.worldid)
		for resource_manager in self.data.itervalues():
			result += '\n' + resource_manager.__str__()
		return result

class SingleResourceTradeManager(WorldObject):
	def __init__(self, settlement_manager, resource_id):
		super(SingleResourceTradeManager, self).__init__()
		self.__init(settlement_manager, resource_id)
		self.available = 0.0 # unused resource production available per tick
		self.total = 0.0 # total resource production imported per tick

	def __init(self, settlement_manager, resource_id):
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.quotas = {} # {quota_holder: amount, ...}
		self.partners = {} # {settlement_manager_id: amount, ...}
		self.identifier = '/%d,%d/trade' % (self.worldid, self.resource_id)
		self.building_ids = []
		for abstract_building in AbstractBuilding.buildings.itervalues():
			if self.resource_id in abstract_building.lines:
				self.building_ids.append(abstract_building.id)

	def save(self, db, trade_manager_id):
		super(SingleResourceTradeManager, self).save(db)
		db("INSERT INTO ai_single_resource_trade_manager(rowid, trade_manager, resource_id, available, total) VALUES(?, ?, ?, ?, ?)", \
			self.worldid, trade_manager_id, self.resource_id, self.available, self.total)
		for identifier, quota in self.quotas.iteritems():
			db("INSERT INTO ai_single_resource_trade_manager_quota(single_resource_trade_manager, identifier, quota) VALUES(?, ?, ?)", \
				self.worldid, identifier, quota)
		for settlement_manager_id, amount in self.partners.iteritems():
			db("INSERT INTO ai_single_resource_trade_manager_partner(single_resource_trade_manager, settlement_manager, amount) VALUES(?, ?, ?)", \
				self.worldid, settlement_manager_id, amount)

	def _load(self, db, settlement_manager, worldid):
		super(SingleResourceTradeManager, self).load(db, worldid)
		resource_id, self.available, self.total = \
			db("SELECT resource_id, available, total FROM ai_single_resource_trade_manager WHERE rowid = ?", worldid)[0]
		self.__init(settlement_manager, resource_id)

		for identifier, quota in db("SELECT identifier, quota FROM ai_single_resource_trade_manager_quota WHERE single_resource_trade_manager = ?", worldid):
			self.quotas[identifier] = quota

		db_result = db("SELECT settlement_manager, amount FROM ai_single_resource_trade_manager_partner WHERE single_resource_trade_manager = ?", worldid)
		for settlement_manager_id, amount in db_result:
			self.partners[settlement_manager_id] = amount

	@classmethod
	def load(cls, db, settlement_manager, worldid):
		self = cls.__new__(cls)
		self._load(db, settlement_manager, worldid)
		return self

	def _refresh_current_production(self):
		total = 0.0
		for settlement_manager in self.settlement_manager.owner.settlement_managers:
			if self.settlement_manager is not settlement_manager:
				resource_manager = settlement_manager.resource_manager
				resource_manager.request_deep_quota_change(self.identifier, False, self.resource_id, 100)
				total += resource_manager.get_deep_quota(self.identifier, self.resource_id)
		return total

	def refresh(self):
		currently_used = sum(self.quotas.itervalues())
		self.total = self._refresh_current_production()
		if self.total >= currently_used:
			self.available = self.total - currently_used
		else:
			self.available = 0.0
			# unable to honour current quota assignments, decreasing all equally
			multiplier = 0.0 if abs(self.total) < 1e-7 else self.total / currently_used
			for quota_holder in self.quotas:
				if self.quotas[quota_holder] > 1e-7:
					self.quotas[quota_holder] *= multiplier
				else:
					self.quotas[quota_holder] = 0

	def finalize_requests(self):
		options = []
		for settlement_manager in self.settlement_manager.owner.settlement_managers:
			if self.settlement_manager != settlement_manager:
				resource_manager = settlement_manager.resource_manager
				amount = resource_manager.get_deep_quota(self.identifier, self.resource_id)
				options.append((amount, resource_manager.worldid, resource_manager, settlement_manager))
		options.sort(reverse = True)

		self.partners = defaultdict(lambda: 0.0)
		needed_amount = self.total - self.available
		for amount, _, resource_manager, settlement_manager in options:
			if needed_amount < 1e-9:
				break
			if amount > needed_amount:
				resource_manager.request_deep_quota_change(self.identifier, False, self.resource_id, needed_amount)
				self.partners[settlement_manager.worldid] += needed_amount
				needed_amount = 0
			else:
				self.partners[settlement_manager.worldid] += amount
				needed_amount -= amount
		self.total -= self.available
		self.available = 0.0

	def get_quota(self, quota_holder):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		return self.quotas[quota_holder]

	def get_total_import(self):
		return self.total - self.available

	def request_quota_change(self, quota_holder, amount):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		amount = max(amount, 0.0)

		if abs(amount - self.quotas[quota_holder]) < 1e-7:
			pass
		elif amount < self.quotas[quota_holder]:
			# lower the amount of reserved import
			change = self.quotas[quota_holder] - amount
			self.available += change
			self.quotas[quota_holder] -= change
		else:
			# raise the amount of reserved import
			change = min(amount - self.quotas[quota_holder], self.available)
			self.available -= change
			self.quotas[quota_holder] += change

	def __str__(self):
		result = 'Resource %d import %.5f/%.5f' % (self.resource_id, self.available, self.total)
		for quota_holder, quota in self.quotas.iteritems():
			result += '\n  quota assignment %.5f to %s' % (quota, quota_holder)
		for settlement_manager_id, amount in self.partners.iteritems():
			settlement_name = 'unknown'
			try:
				settlement_name = WorldObject.get_object_by_id(settlement_manager_id).settlement.name
			except WorldObjectNotFound:
				pass
			result += '\n  import %.5f from %s' % (amount, settlement_name)
		return result

decorators.bind_all(TradeManager)
decorators.bind_all(SingleResourceTradeManager)
