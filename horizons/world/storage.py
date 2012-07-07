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


"""
Here we define how the inventories work, that are used by world objects.
These storage classes exist:

- GenericStorage (abstract): Defines general interface for storage.

Storages with certain properties:
- PositiveStorage: Doesn't allow negative values.
- TotalStorage: Sum of all stored res must be <= a certain limit.
- SpecializedStorage: Allows only certain resources to be stored here.
- SizedSpecializedStorage: Like SpecializedStorage, but each res has an own limit.

Combinations:
- SizedSlottedStorage: One limit, each res value must be <= the limit and >= 0.
- PositiveTotalStorage: use case: ship inventory
- PositiveSizedSlotStorage: every res has the same limit, only positive values (warehouse, collectors)
- PositiveSizedSpecializedStorage: Like SizedSpecializedStorage, plus only positive values.
"""

import sys
import copy
from collections import defaultdict

from horizons.util import ChangeListener

class GenericStorage(ChangeListener):
	"""The GenericStorage represents a storage for buildings/units/players/etc. for storing
	resources. The GenericStorage is the general form and is mostly used as baseclass to
	derive storages with special function from it. Normally there should be no need to
	use the GenericStorage. Rather use a specialized version that is suitable for the job.
	"""
	def __init__(self):
		super(GenericStorage, self).__init__()
		self._storage = defaultdict(lambda : 0)

	def save(self, db, ownerid):
		for slot in self._storage.iteritems():
			db("INSERT INTO storage (object, resource, amount) VALUES (?, ?, ?) ",
				ownerid, slot[0], slot[1])

	def load(self, db, ownerid):
		for (res, amount) in db.get_storage_rowids_by_ownerid(ownerid):
			self.alter(res, amount)

	def alter(self, res, amount):
		"""alter() will return the amount of resources that did not fit into the storage or
		if altering in a negative way to remove resources, the amount of resources that was
		not available in the storage. The totalstorage always returns 0 as there are not
		limits as to what can be in the storage.
		@param res: int res id that is to be altered
		@param amount: int amount that is to be changed. Can be negative to remove resources.
		@return: int - amount that did not fit or was not available, depending on context.
		"""
		self._storage[res] += amount # defaultdict
		self._changed()
		return 0

	def reset(self, res):
		"""Resets a resource slot to zero, removing all it's contents."""
		if res in self._storage:
			self._storage[res] = 0
			self._changed()

	def reset_all(self):
		"""Removes every resource from this inventory"""
		for res in self._storage:
			self._storage[res] = 0
		self._changed()

	def get_limit(self, res=None):
		"""Returns the current limit of the storage. Please not that this value can have
		different meanings depending on the context. See the storage descriptions on what
		the value does.
		@param res: int res that the limit should be returned for.
		@return: int
		"""
		return sys.maxint # should not be used for generic storage

	def get_free_space_for(self, res):
		"""Returns how much of res we can still store here (limit - current amount)."""
		return self.get_limit(res) - self[res]

	def get_sum_of_stored_resources(self):
		return sum(self._storage.itervalues())

	def get_dump(self):
		"""Returns a dump of the inventory as dict"""
		return copy.deepcopy(self._storage)

	def __getitem__(self, res):
		return self._storage.get(res, 0)

	def iterslots(self):
		return self._storage.iterkeys()

	def itercontents(self):
		return self._storage.iteritems()

	def __str__(self):
		return "%s(%s)" % (self.__class__, self._storage if hasattr(self, "_storage") else None)

class SpecializedStorage(GenericStorage):
	"""Storage where only certain resources can be stored. If you want to store a resource here,
	you have to call add_resource_slot() before calling alter()."""
	def alter(self, res, amount):
		if self.has_resource_slot(res): # res can be stored, propagate call
			return super(SpecializedStorage, self).alter(res, amount)
		else:
			return amount # we couldn't store any of this

	def add_resource_slot(self, res):
		"""Creates a slot for res. Does nothing if the slot exists."""
		super(SpecializedStorage, self).alter(res, 0)
		self._changed()

	def has_resource_slot(self, res):
		return (res in self._storage)

class SizedSpecializedStorage(SpecializedStorage):
	"""Just like SpecializedStorage, but each res has an own limit.
	Can take a dict {res: size, res2: size2, ...} to init slots
	"""
	def __init__(self, slot_sizes=None):
		super(SizedSpecializedStorage, self).__init__()
		slot_sizes = slot_sizes or {}
		self.__slot_limits = {}
		for res, size in slot_sizes.iteritems():
			self.add_resource_slot(res, size)

	def alter(self, res, amount):
		if not self.has_resource_slot(res):
			# TODO: this is also checked in the super class, refactor one of them away
			return amount

		if amount > 0: # can only reach limit if > 0
			storeable_amount = self.get_free_space_for(res)
			if amount > storeable_amount: # tried to store more than limit allows
				ret = super(SizedSpecializedStorage, self).alter(res, storeable_amount)
				return (amount - storeable_amount ) + ret

		# no limit breach, just propagate call
		return super(SizedSpecializedStorage, self).alter(res, amount)

	def get_limit(self, res):
		return self.__slot_limits.get(res, 0)

	def add_resource_slot(self, res, size):
		"""Add a resource slot for res for the size size.
		If the slot already exists, just update it's size to size.
		NOTE: THIS IS NOT SAVE/LOADED HERE. It must be restored manually."""
		super(SizedSpecializedStorage, self).add_resource_slot(res)
		assert size >= 0
		self.__slot_limits[res] = size

	def save(self, db, ownerid):
		super(SizedSpecializedStorage, self).save(db, ownerid)
		assert len(self._storage) == len(self.__slot_limits) # we have to have limits for each res

	def load(self, db, ownerid):
		super(SizedSpecializedStorage, self).load(db, ownerid)

class GlobalLimitStorage(GenericStorage):
	"""Storage with some kind of global limit. This limit has to be interpreted in the subclass,
	it has not predefined meaning here. (This class is used for infrastructure, such as save/load for the limit)"""
	def __init__(self, limit):
		super(GlobalLimitStorage, self).__init__()
		self.limit = limit

	def save(self, db, ownerid):
		super(GlobalLimitStorage, self).save(db, ownerid)
		db("INSERT INTO storage_global_limit(object, value) VALUES(?, ?)", ownerid, self.limit)

	def load(self, db, ownerid):
		self.limit = db.get_storage_global_limit(ownerid)
		super(GlobalLimitStorage, self).load(db, ownerid)

	def adjust_limit(self, amount):
		"""Adjusts the limit of the storage by amount.
		If the limit is reduced, every resource that doesn't fit in the storage anymore is dropped!
		@param amount: int, difference to current limit (positive or negative)
		"""
		self.limit += amount
		if self.limit < 0:
			self.limit = 0
		# remove res that don't fit anymore
		for res, amount in self._storage.iteritems():
			if amount > self.limit:
				self._storage[res] = self.limit
		self._changed()

	def get_limit(self, res=None):
		return self.limit

class TotalStorage(GlobalLimitStorage):
	"""The TotalStorage represents a storage with a general limit to the sum of resources
	that can be stored in it. The limit is a general limit, not specialized to one resource.
	E.g. if the limit is 10, you can have 4 items of res A and 6 items of res B, then nothing
	else can be stored here.

	NOTE: Negative values will increase storage size, so consider using PositiveTotalStorage.
	"""
	def __init__(self, limit):
		super(TotalStorage, self).__init__(limit)

	def alter(self, res, amount):
		check =  max(0, amount + self.get_sum_of_stored_resources() - self.limit)
		return check + super(TotalStorage, self).alter(res, amount - check)

	def get_free_space_for(self, res):
		return self.limit - self.get_sum_of_stored_resources()

class PositiveStorage(GenericStorage):
	"""The positive storage doesn't allow to have negative values for resources."""
	def alter(self, res, amount):
		subtractable_amount = amount
		if amount < 0 and ( amount + self[res] < 0 ): # tried to subtract more than we have
			subtractable_amount = - self[res] # only amount where we keep a positive value
		ret = super(PositiveStorage, self).alter(res, subtractable_amount)
		return (amount - subtractable_amount) + ret

class PositiveTotalStorage(PositiveStorage, TotalStorage):
	"""A combination of the Total and Positive storage. Used to set a limit and ensure
	there are no negative amounts in the storage."""
	def alter(self, res, amount):
		ret = super(PositiveTotalStorage, self).alter(res, amount)
		if self[res] == 0:
			# remove empty slots, cause else they will get displayed in the ship inventory
			del self._storage[res]
		return ret

class PositiveTotalNumSlotsStorage(PositiveStorage, TotalStorage):
	"""A combination of the Total and Positive storage which only has a limited number of slots.
	Used to set a limit and ensure there are no negative amounts in the storage."""
	def __init__(self, limit, slotnum):
		super(PositiveTotalNumSlotsStorage, self).__init__(limit)
		self.slotnum = slotnum

	def alter(self, res, amount):
		if amount == 0:
			return 0
		if not res in self._storage and len(self._storage) >= self.slotnum:
			return amount
		ret = super(PositiveTotalNumSlotsStorage, self).alter(res, amount)
		if self[res] == 0:
			# remove empty slots, cause else they will get displayed in the ship inventory
			del self._storage[res]
		return ret

	def get_free_space_for(self, res):
		if not res in self._storage and len(self._storage) >= self.slotnum:
			return 0
		else:
			return super(PositiveTotalNumSlotsStorage, self).get_free_space_for(res)

class PositiveSizedSlotStorage(GlobalLimitStorage, PositiveStorage):
	"""A storage consisting of a slot for each resource, all slots have the same size 'limit'
	Used by the warehouse for example. So with a limit of 30 you could have a max of
	30 from each resource."""
	def __init__(self, limit=0):
		super(PositiveSizedSlotStorage, self).__init__(limit)

	def alter(self, res, amount):
		check = max(0, amount + self[res] - self.limit)
		ret = super(PositiveSizedSlotStorage, self).alter(res, amount - check)
		if res in self._storage and self[res] == 0:
			del self._storage[res]
		return check + ret

class PositiveSizedSpecializedStorage(PositiveStorage, SizedSpecializedStorage):
	pass

class PositiveSizedNumSlotStorage(PositiveSizedSlotStorage):
	"""A storage consisting of a number of slots, all slots have the same size 'limit'
	Used by ship (huker) for example. So with a limit of 50 and a slot num of 4 you could have a max of 50
	from each resource and only slotnum resources."""
	def __init__(self, limit, slotnum):
		super(PositiveSizedNumSlotStorage, self).__init__(limit)
		self.slotnum = slotnum

	def alter(self, res, amount):
		if amount == 0:
			return 0
		if not res in self._storage and len(self._storage) >= self.slotnum:
			return amount
		result = super(PositiveSizedNumSlotStorage, self).alter(res, amount)
		return result

	def get_free_space_for(self, res):
		if not res in self._storage and len(self._storage) >= self.slotnum:
			return 0
		else:
			return super(PositiveSizedNumSlotStorage, self).get_free_space_for(res)

########################################################################
class SettlementStorage:
	"""Dummy class to signal the storagecomponent to use the settlements inventory"""
