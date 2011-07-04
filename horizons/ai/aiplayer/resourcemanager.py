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

class ResourceManager(WorldObject):
	"""
	An object of this class manages the resources of one settlement.
	"""

	def __init__(self):
		super(ResourceManager, self).__init__()
		self.__init()

	def __init(self):
		self.data = {} # (resource_id, building_id): SingleResourceManager

	def save(self, db, settlement_manager):
		super(ResourceManager, self).save(db)
		db("INSERT INTO ai_resource_manager(rowid, settlement_manager) VALUES(?, ?)", self.worldid, settlement_manager.worldid)
		for (_, building_id), resource_manager in self.data.iteritems():
			resource_manager.save(db, self, building_id)

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_resource_manager WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(ResourceManager, self).load(db, worldid)
		self.__init()
		for db_row in db("SELECT rowid, resource_id, building_id FROM ai_single_resource_manager WHERE resource_manager = ?", worldid):
			self.data[(db_row[1], db_row[2])] = SingleResourceManager.load(db, db_row[0])

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def refresh(self):
		for resource_manager in self.data.itervalues():
			resource_manager.refresh()

	def add_building(self, building, resource_id):
		key = (resource_id, building.id)
		if key not in self.data:
			self.data[key] = SingleResourceManager(resource_id)
		self.data[key].add_building(building)

	def request_quota_change(self, quota_holder, resource_id, building_id, amount):
		key = (resource_id, building_id)
		if key not in self.data:
			self.data[key] = SingleResourceManager(resource_id)
		self.data[key].request_quota_change(quota_holder, amount)

	def get_quota(self, quota_holder, resource_id, building_id):
		key = (resource_id, building_id)
		if key not in self.data:
			self.data[key] = SingleResourceManager(resource_id)
		return self.data[key].get_quota(quota_holder)

	def __str__(self):
		result = 'ResourceManager(%d)' % self.worldid
		for resource_manager in self.data.itervalues():
			result += '\n' + resource_manager.__str__()
		return result

class SingleResourceManager(WorldObject):
	def __init__(self, resource_id):
		super(SingleResourceManager, self).__init__()
		self.__init(resource_id)
		self.available = 0.0 # unused resource production per tick
		self.total = 0.0 # total resource production per tick

	def __init(self, resource_id):
		self.resource_id = resource_id
		self.quotas = {} # {quota_holder: amount, ...}
		self.buildings = [] # [building, ...]

	def save(self, db, resource_manager, building_id):
		db("INSERT INTO ai_single_resource_manager(rowid, resource_manager, resource_id, building_id, available, total) VALUES(?, ?, ?, ?, ?, ?)", \
			self.worldid, resource_manager.worldid, self.resource_id, building_id, self.available, self.total)
		for building in self.buildings:
			db("INSERT INTO ai_single_resource_manager_building(single_resource_manager, building_id) VALUES(?, ?)", self.worldid, building.worldid)
		for identifier, quota in self.quotas.iteritems():
			db("INSERT INTO ai_single_resource_manager_quota(single_resource_manager, identifier, quota) VALUES(?, ?, ?)", self.worldid, identifier, quota)

	def _load(self, db, worldid):
		super(SingleResourceManager, self).load(db, worldid)
		(resource_id, self.available, self.total) = db("SELECT resource_id, available, total FROM ai_single_resource_manager WHERE rowid = ?", worldid)[0]
		self.__init(resource_id)

		for (building_worldid,) in db("SELECT building_id FROM ai_single_resource_manager_building WHERE single_resource_manager = ?", worldid):
			self.buildings.append(WorldObject.get_object_by_id(building_worldid))

		for (identifier, quota) in db("SELECT identifier, quota FROM ai_single_resource_manager_quota WHERE single_resource_manager = ?", worldid):
			self.quotas[identifier] = quota

	@classmethod
	def load(cls, db, worldid):
		self = cls.__new__(cls)
		self._load(db, worldid)
		return self

	def _get_current_production(self):
		total = 0.0
		for building in self.buildings:
			total += AbstractBuilding.buildings[building.id].get_production_level(building, self.resource_id)
		return total

	def refresh(self):
		production = self._get_current_production()
		if production >= self.total:
			self.available += production - self.total
		else:
			change = self.total - production
			if change > self.available and self.total - self.available > 1e-7:
				# unable to honour current quota assignments, decreasing all equally
				multiplier = 0.0 if abs(production) < 1e-7 else (self.total - self.available) / production
				for quota_holder in self.quotas:
					amount = self.quotas[quota_holder]
					if amount > 1e-7:
						amount *= multiplier
				self.available = 0.0
			else:
				self.available -= change
		self.total = production

	def add_building(self, building):
		self.buildings.append(building)
		self.refresh()

	def get_quota(self, quota_holder):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		return self.quotas[quota_holder]

	def request_quota_change(self, quota_holder, amount):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		amount = max(amount, 0.0)

		if amount <= self.quotas[quota_holder]:
			# lower the amount of reserved production
			change = self.quotas[quota_holder] - amount
			self.available += change
			self.quotas[quota_holder] -= change
		else:
			# raise the amount of reserved production
			change = min(amount - self.quotas[quota_holder], self.available)
			self.available -= change
			self.quotas[quota_holder] += change

	def __str__(self):
		result = 'Resource %d production %.5f/%.5f' % (self.resource_id, self.available, self.total)
		for quota in self.quotas.itervalues():
			result += '\n  quota assignment %.5f' % quota
		return result

decorators.bind_all(ResourceManager)
decorators.bind_all(SingleResourceManager)
