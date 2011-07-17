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

from building import AbstractBuilding
from horizons.util import WorldObject
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, RES

class ResourceManager(WorldObject):
	"""
	An object of this class manages the resources of one settlement.
	"""

	def __init__(self, settlement_manager):
		super(ResourceManager, self).__init__()
		self.__init(settlement_manager)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self._data = {} # {(resource_id, building_id): SingleResourceManager, ...}
		self._chain = {} # {resource_id: SimpleProductionChainSubtreeChoice, ...}
		self._low_priority_requests = {} # {(quota_holder, resource_id): amount, ...}

	def save(self, db):
		super(ResourceManager, self).save(db)
		db("INSERT INTO ai_resource_manager(rowid, settlement_manager) VALUES(?, ?)", self.worldid, self.settlement_manager.worldid)
		for resource_manager in self._data.itervalues():
			resource_manager.save(db, self.worldid)

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_resource_manager WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(ResourceManager, self).load(db, worldid)
		self.__init(settlement_manager)
		for db_row in db("SELECT rowid, resource_id, building_id FROM ai_single_resource_manager WHERE resource_manager = ?", worldid):
			self._data[(db_row[1], db_row[2])] = SingleResourceManager.load(db, settlement_manager, db_row[0])

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def _get_chain(self, resource_id, resource_producer, production_ratio):
		""" Returns None or SimpleProductionChainSubtreeChoice depending on the number of options """
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
		for resource_manager in self._data.itervalues():
			resource_manager.refresh()

	def request_quota_change(self, quota_holder, priority, resource_id, building_id, amount):
		key = (resource_id, building_id)
		if key not in self._data:
			self._data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		self._data[key].request_quota_change(quota_holder, priority, amount)

	def get_quota(self, quota_holder, resource_id, building_id):
		key = (resource_id, building_id)
		if key not in self._data:
			self._data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		return self._data[key].get_quota(quota_holder)

	def request_deep_quota_change(self, quota_holder, priority, resource_id, amount):
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
		if resource_id not in self._chain:
			self._chain[resource_id] = self._make_chain(resource_id)
		return self._chain[resource_id].get_quota(quota_holder)

	def replay_deep_low_priority_requests(self):
		for (quota_holder, resource_id), amount in self._low_priority_requests.iteritems():
			self.request_deep_quota_change(quota_holder, False, resource_id, amount)

	def get_total_export(self, resource_id):
		total = 0
		for resource_manager in self._data.itervalues():
			if resource_manager.resource_id == resource_id:
				total += resource_manager.get_total_export()
		return total

	def __str__(self):
		result = 'ResourceManager(%s, %d)' % (self.settlement_manager.settlement.name, self.worldid)
		for resource_manager in self._data.itervalues():
			res = resource_manager.resource_id
			if res not in [RES.FOOD_ID, RES.TEXTILE_ID, RES.BRICKS_ID]:
				continue
			result += '\n' + resource_manager.__str__()
		return result

class SingleResourceManager(WorldObject):
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
		if self.resource_id in self.virtual_resources:
			return self.virtual_production
		buildings = self.settlement_manager.settlement.get_buildings_by_id(self.building_id)
		return sum(AbstractBuilding.buildings[building.id].get_production_level(building, self.resource_id) for building in buildings)

	def refresh(self):
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
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = (0.0, False)
		return self.quotas[quota_holder][0]

	def request_quota_change(self, quota_holder, priority, amount):
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
		# this is accurate for now because all trade is set to low priority and nothing else is
		return self.low_priority

	def __str__(self):
		result = 'Resource %d production %.5f/%.5f (%.5f low priority)' % (self.resource_id, self.available, self.total, self.low_priority)
		for quota_holder, (quota, priority) in self.quotas.iteritems():
			result += '\n  %squota assignment %.5f to %s' % ('priority ' if priority else '', quota, quota_holder)
		return result

class SimpleProductionChainSubtreeChoice(object):
	def __init__(self, options):
		self.options = options
		self.resource_id = options[0].resource_id

	def assign_identifier(self, prefix):
		self.identifier = prefix + ('/choice' if len(self.options) > 1 else '')
		for option in self.options:
			option.assign_identifier(self.identifier)

	def request_quota_change(self, quota_holder, amount, priority):
		"""
		Reserves currently available production and imports from other islands if allowed
		Returns the total amount it can reserve or import
		"""
		total_reserved = 0.0
		for option in self.options:
			total_reserved += option.request_quota_change(quota_holder, max(0.0, amount - total_reserved), priority)
		return total_reserved

	def get_quota(self, quota_holder):
		return sum(option.get_quota(quota_holder) for option in self.options)

class SimpleProductionChainSubtree:
	def __init__(self, resource_manager, resource_id, production_line, abstract_building, children, production_ratio):
		self.resource_manager = resource_manager
		self.resource_id = resource_id
		self.production_line = production_line
		self.abstract_building = abstract_building
		self.children = children
		self.production_ratio = production_ratio

	def assign_identifier(self, prefix):
		self.identifier = '%s/%d,%d' % (prefix, self.resource_id, self.abstract_building.id)
		for child in self.children:
			child.assign_identifier(self.identifier)

	def request_quota_change(self, quota_holder, amount, priority):
		"""
		Reserves currently available production and imports from other islands if allowed
		Returns the total amount it can reserve or import
		"""
		total_reserved = amount
		for child in self.children:
			total_reserved = min(total_reserved, child.request_quota_change(quota_holder, amount, priority))

		self.resource_manager.request_quota_change(quota_holder + self.identifier, priority, self.resource_id, self.abstract_building.id, amount * self.production_ratio)
		return min(total_reserved, self.resource_manager.get_quota(quota_holder + self.identifier, self.resource_id, self.abstract_building.id) / self.production_ratio)

	def get_quota(self, quota_holder):
		root_quota = self.resource_manager.get_quota(quota_holder + self.identifier, self.resource_id, self.abstract_building.id) / self.production_ratio
		if self.children:
			return min(root_quota, min(child.get_quota(quota_holder) for child in self.children))
		return root_quota

decorators.bind_all(ResourceManager)
decorators.bind_all(SingleResourceManager)
decorators.bind_all(SimpleProductionChainSubtreeChoice)
decorators.bind_all(SimpleProductionChainSubtree)
