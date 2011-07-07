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

	def request_quota_change(self, quota_holder, resource_id, building_id, amount):
		key = (resource_id, building_id)
		if key not in self.data:
			self.data[key] = SingleResourceManager(self.settlement_manager, resource_id, building_id)
		self.data[key].request_quota_change(quota_holder, amount)

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
	def __init__(self, settlement_manager, resource_id, building_id):
		super(SingleResourceManager, self).__init__()
		self.__init(settlement_manager, resource_id, building_id)
		self.available = 0.0 # unused resource production per tick
		self.total = 0.0 # total resource production per tick

	def __init(self, settlement_manager, resource_id, building_id):
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.building_id = building_id
		self.quotas = {} # {quota_holder: amount, ...}

	def save(self, db, resource_manager_id):
		db("INSERT INTO ai_single_resource_manager(rowid, resource_manager, resource_id, building_id, available, total) VALUES(?, ?, ?, ?, ?, ?)", \
			self.worldid, resource_manager_id, self.resource_id, self.building_id, self.available, self.total)
		for identifier, quota in self.quotas.iteritems():
			db("INSERT INTO ai_single_resource_manager_quota(single_resource_manager, identifier, quota) VALUES(?, ?, ?)", self.worldid, identifier, quota)

	def _load(self, db, settlement_manager, worldid):
		super(SingleResourceManager, self).load(db, worldid)
		(resource_id, building_id, self.available, self.total) = db("SELECT resource_id, building_id, available, total FROM ai_single_resource_manager WHERE rowid = ?", worldid)[0]
		self.__init(settlement_manager, resource_id, building_id)

		for (identifier, quota) in db("SELECT identifier, quota FROM ai_single_resource_manager_quota WHERE single_resource_manager = ?", worldid):
			self.quotas[identifier] = quota

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
		currently_used = sum(self.quotas.itervalues())
		self.total = self._get_current_production()
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

	def get_quota(self, quota_holder):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		return self.quotas[quota_holder]

	def request_quota_change(self, quota_holder, amount):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		amount = max(amount, 0.0)

		if abs(amount - self.quotas[quota_holder]) < 1e-7:
			pass
		elif amount < self.quotas[quota_holder]:
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
		for quota_holder, quota in self.quotas.iteritems():
			result += '\n  quota assignment %.5f to %s' % (quota, quota_holder)
		return result

decorators.bind_all(ResourceManager)
decorators.bind_all(SingleResourceManager)
