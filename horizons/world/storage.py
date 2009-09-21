# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
- PositiveSizedSlotStorage: every res has the same limit, only positive values (branch office)
- PositiveSizedSpecializedStorage: Like SizedSpecializedStorage, plus only positive values.
"""

import sys

from horizons.util import Changelistener

class GenericStorage(Changelistener):
	"""The GenericStorage represents a storage for buildings/units/players/etc. for storing
	resources. The GenericStorage is the general form and is mostly used as baseclass to
	derive storages with special function from it. Normally there should be no need to
	use the GenericStorage. Rather use a specialized version that is suitable for the job.
	"""
	def __init__(self, **kwargs):
		super(GenericStorage, self).__init__(**kwargs)
		self._storage = {}
		self.limit = sys.maxint

	def save(self, db, ownerid):
		for slot in self._storage.iteritems():
			db("INSERT INTO storage (object, resource, amount) VALUES (?, ?, ?) ",
				ownerid, slot[0], slot[1])
		db("INSERT INTO storage_properties(object, name, value) VALUES(?, ?, ?)",
			 ownerid, "limit", self.limit)

	def load(self, db, ownerid):
		# load a limit, if we have one
		# this is only useful for limits, that have been changed after construction,
		# all static limits will be set on storage construction, which happens before load
		result = db("SELECT value FROM storage_properties WHERE object = ? AND \
		          name = \"limit\"", ownerid)
		if(len(result) != 0):
			self.limit = result[0][0]
			if self.limit is not None:
				self.limit = int(self.limit)

		for (res, amount) in db("SELECT resource, amount FROM storage WHERE object = ?", ownerid):
			assert self[res] == 0
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
		assert isinstance(res, int)
		assert isinstance(amount, int)
		if res in self._storage:
			self._storage[res] += amount
		else:
			self._storage[res] = amount
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
		return self.limit # should not be used for generic storage

	def get_free_space_for(self, res):
		"""Returns how much of res we can still store here (limit - current amount)."""
		return self.get_limit(res) - self[res]

	def adjust_limits(self, amount):
		"""Adjusts the limit of the storage by amount
		@param amount: int, difference to current limit (positive or negative)
		"""
		self.limit += amount
		if self.limit < 0:
			self.limit = 0
		self._changed()

	def get_sum_of_stored_resources(self):
		return sum(self._storage.itervalues())

	def __getitem__(self, res):
		return self._storage[res] if res in self._storage else 0

	def __iter__(self):
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
	"""Just like SpecializedStorage, but each res has an own limit."""
	def __init__(self, **kwargs):
		super(SizedSpecializedStorage, self).__init__(**kwargs)
		self.__slot_limits = {}

	def alter(self, res, amount):
		if not self.has_resource_slot(res):
			return amount

		storeable_amount = self.get_free_space_for(res)
		if amount > storeable_amount: # tried to store more than limit allows
			amount = storeable_amount
			ret = super(SizedSpecializedStorage, self).alter(res, storeable_amount)
			return (amount - storeable_amount ) + ret

		# no limit breach, just propagate call
		return super(SizedSpecializedStorage, self).alter(res, amount)

	def get_limit(self, res):
		if res in self.__slot_limits:
			return self.__slot_limits[res]
		else:
			return 0

	def add_resource_slot(self, res, size):
		"""Add a resource slot for res for the size size.
		If the slot already exists, just update it's size to size."""
		super(SizedSpecializedStorage, self).add_resource_slot(res)
		assert size >= 0
		self.__slot_limits[res] = size

	def save(self, db, ownerid):
		super(SizedSpecializedStorage, self).save(db, ownerid)
		assert len(self._storage) == len(self.__slot_limits) # we have to have limits for each res
		for res in self._storage:
			assert res in self.__slot_limits
			db("INSERT INTO storage_properties(object, name, value) VALUES(?, ?, ?)", \
				 ownerid, 'limit_%s' % res, self.__slot_limits[res])

	def load(self, db, ownerid):
		super(SizedSpecializedStorage, self).load(db, ownerid)
		for res in self._storage:
			limit = db("SELECT value FROM storage_properties WHERE object = ? AND name = ?", \
								 ownerid, 'limit_%s' % res)[0][0]
			self.__slot_limits[res] = int(limit)

class TotalStorage(GenericStorage):
	"""The TotalStorage represents a storage with a general limit to the sum of resources
	that can be stored in it. The limit is a general limit, not specialized to one resource.
	E.g. if the limit is 10, you can have 4 items of res A and 6 items of res B, then nothing
	else can be stored here.

	NOTE: Negative values will increase storage size, so consider using PositiveTotalStorage.
	"""
	def __init__(self, space, **kwargs):
		super(TotalStorage, self).__init__(space = space, **kwargs)
		self.limit = space

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

class PositiveSizedSlotStorage(PositiveStorage):
	"""A storage consisting of a slot for each resource, all slots have the same size 'limit'
	Used by the branch office for example. So with a limit of 30 you could have a max of
	30 from each resource."""
	def __init__(self, limit, **kwargs):
		super(PositiveSizedSlotStorage, self).__init__(**kwargs)
		self.limit = limit

	def alter(self, res, amount):
		check = max(0, amount + self[res] - self.limit)
		return check + super(PositiveSizedSlotStorage, self).alter(res, amount - check)


class PositiveSizedSpecializedStorage(PositiveStorage, SizedSpecializedStorage):
	pass
