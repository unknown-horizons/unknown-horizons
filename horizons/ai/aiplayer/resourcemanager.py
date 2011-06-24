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
		self.data = {} # (resource_id, building_id): SingleResourceManager

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

class SingleResourceManager:
	def __init__(self, resource_id):
		self.resource_id = resource_id
		self.quotas = {} # {quota_holder: amount, ...}
		self.buildings = [] # [building, ...]
		self.available = 0.0 # unused resource production per tick
		self.total = 0.0 # total resource production per tick

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
				multiplier = (self.total - self.available) / production
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
