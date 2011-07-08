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
		self.data = {} # (resource_id, building_id): SingleResourceManager

	def save(self, db):
		super(ResourceManager, self).save(db)
		db("INSERT INTO ai_resource_manager(rowid, settlement_manager) VALUES(?, ?)", self.worldid, self.settlement_manager.worldid)
		for resource_manager in self.data.itervalues():
			resource_manager.save(db, self.worldid)

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_resource_manager WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(ResourceManager, self).load(db, worldid)
		self.__init(settlement_manager)
		for db_row in db("SELECT rowid, resource_id, building_id FROM ai_single_resource_manager WHERE resource_manager = ?", worldid):
			self.data[(db_row[1], db_row[2])] = SingleResourceManager.load(db, settlement_manager, db_row[0])

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def refresh(self):
		for resource_manager in self.data.itervalues():
			resource_manager.refresh()

	def request_quota_change(self, quota_holder, priority, resource_id, building_id, amount):
		key = (resource_id, building_id)
		if key not in self.data:
			self.data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		self.data[key].request_quota_change(quota_holder, priority, amount)

	def get_quota(self, quota_holder, resource_id, building_id):
		key = (resource_id, building_id)
		if key not in self.data:
			self.data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		return self.data[key].get_quota(quota_holder)

	def __str__(self):
		result = 'ResourceManager(%s, %d)' % (self.settlement_manager.settlement.name, self.worldid)
		for resource_manager in self.data.itervalues():
			result += '\n' + resource_manager.__str__()
		return result

class SingleResourceManager(WorldObject):
	epsilon = 1e-7 # epsilon for avoiding problems with miniscule values

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
		buildings = self.settlement_manager.settlement.get_buildings_by_id(self.building_id)
		if not buildings:
			return 0.0
		total = 0.0
		if self.resource_id == RES.FOOD_ID and self.building_id == BUILDINGS.FARM_CLASS:
			# TODO: make this block of code work in a better way
			# return the production of the potato fields because the farm is not the limiting factor
			buildings = self.settlement_manager.settlement.get_buildings_by_id(BUILDINGS.POTATO_FIELD_CLASS)
			if not buildings:
				return 0.0
			return len(buildings) * AbstractBuilding.buildings[buildings[0].id].get_production_level(buildings[0], RES.POTATOES_ID)
		else:
			for building in buildings:
				total += AbstractBuilding.buildings[building.id].get_production_level(building, self.resource_id)
		return total

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
				for quota_holder, (quota, priority) in self.quotas.iteritems():
					if quota > self.epsilon and not priority:
						self.quotas[quota_holder] = (quota * multiplier, priority)
					elif not priority:
						self.quotas[quota_holder] = (0.0, priority)
				self.available += self.low_priority - new_low_priority
				self.low_priority = new_low_priority

			# raise the amount of reserved production as much as possible
			change = min(amount - self.quotas[quota_holder][0], self.available)
			self.available -= change
			self.quotas[quota_holder] = (self.quotas[quota_holder][0] + change, priority)
			if not priority:
				self.low_priority += change

	def __str__(self):
		result = 'Resource %d production %.5f/%.5f' % (self.resource_id, self.available, self.total)
		for quota_holder, (quota, priority) in self.quotas.iteritems():
			result += '\n  %squota assignment %.5f to %s' % ('priority ' if priority else '', quota, quota_holder)
		return result

decorators.bind_all(ResourceManager)
decorators.bind_all(SingleResourceManager)
