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

from horizons.util import WorldObject

class GenericStorage(WorldObject): # TESTED, WORKS
	"""The GenericStorage represents a storage for buildings/units/players/etc. for storing
	resources. The GenericStorage is the general form and is mostly used as baseclass to
	derive storages with special function from it. Normally there should be no need to
	use the GenericStorage. Rather use a specialized version that is suitable for the job.
	"""
	def __init__(self, **kwargs):
		super(GenericStorage, self).__init__(**kwargs)
		self._storage = {}
		self.limit = None

	def save(self, db, ownerid):
		super(GenericStorage, self).save(db)
		for slot in self._storage.iteritems():
			db("INSERT INTO storage (object, resource, amount) VALUES (?, ?, ?) ",
				ownerid, slot[0], slot[1])
		db("INSERT INTO storage_properties(object, name, value) VALUES(?, ?, ?)",
			 ownerid, "limit", self.limit)

	def load(self, db, ownerid):
		# load a limit, if we have one
		# this is only useful for limits, that have been changed after construction,
		# all static limits will be set on storage construction, which happens before load
		result = db("SELECT value FROM storage_properties WHERE object = ? AND name = ?", \
										ownerid, "limit")
		if(len(result) != 0):
			self.limit = result[0][0]
			if self.limit is not None:
				self.limit = int(self.limit)

		for (res, amount) in db("SELECT resource, amount FROM storage WHERE object = ?", ownerid):
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

	def get_limit(self, res):
		"""Returns the current limit of the storage. Please not that this value can have
		different meanings depending on the context. See the storage descriptions on what
		the value does.
		@param res: int res that the limit should be returned for.
		@return: int
		"""
		return self.limit # should not be used for generic storage

	def adjust_limits(self, amount):
		"""Adjusts the limit of the storage by amount
		@param amount: int - value of how much is to be adjusted
		"""
		self.limit += amount
		if self.limit < 0:
			self.limit = 0

	def __getitem__(self, res):
		return self._storage[res] if res in self._storage else 0

	def __iter__(self):
		return self._storage.iteritems()

	def __str__(self):
		if hasattr(self, "_storage"):
			return str(self._storage)
		else:
			return "Not inited"

class SpecializedStorage(GenericStorage): # NOT TESTED! NEEDS WORK!
	def alter(self, res, amount):
		assert False, "Test this before using, it hasn't been correctly implemented"
		return super(SpecializedStorage, self).alter(res, amount) if res in self._storage else amount

	def addResourceSlot(self, res):
		super(SpecializedStorage, self).alter(res, 0)

	def hasResourceSlot(self, res):
		return res in self._storage

class SizedSpecializedStorage(SpecializedStorage): # NOT TESTED, NEEDS WORK!
	def __init__(self, **kwargs):
		assert False, "Test this before using, it hasn't been correlty implemented"
		super(SizedSpecializedStorage, self).__init__(**kwargs)
		self.__size = {}

	def alter(self, res, amount):
		return amount - super(SizedSpecializedStorage, self).alter(res, amount - max(0, amount + self[res] - self.__size.get(res, 0)))

	def get_limit(self, res):
		return self.__size[res]

	def addResourceSlot(self, res, size, **kwargs):
		super(SizedSpecializedStorage, self).addResourceSlot(res = res, size = size, **kwargs)
		self.__size[res] = size

	def save(self, db, ownerid):
		super(SizedSpecializedStorage, self).save(db, ownerid)
		assert False, "Saving of SizedSpecializedStorage hasn't been implemented"

	def load(self, db, ownerid):
		super(SizedSpecializedStorage, self).save(db, ownerid)
		assert False, "Loading of SizedSpecializedStorage hasn't been implemented"


class TotalStorage(GenericStorage): # TESTED AND WORKING
	"""The TotalStorage represents a storage with a general limit to the amount of resources
	that can be stored in it. The limit is a general limit, not specialized to one resource.
	So with a limit of 200 you could have 199 resource A and 1 resource or any other
	combination totaling 200.
	"""
	def __init__(self, space, **kwargs):
		super(TotalStorage, self).__init__(space = space, **kwargs)
		self.limit = space

	def alter(self, res, amount):
		check =  max(0, amount + sum(self._storage.values()) - self.limit)
		return check + super(TotalStorage, self).alter(res, amount - check)

class PositiveStorage(GenericStorage): # TESTED AND WORKING
	"""The positive storage doesn't allow to have negative values for resources."""
	def alter(self, res, amount):
		ret = min(0, amount + self[res]) + super(PositiveStorage, self).alter(res, amount - min(0, amount + self[res]))
		if res in self._storage and self._storage[res] <= 0:
			del self._storage[res]
		return ret

class PositiveTotalStorage(PositiveStorage, TotalStorage): # TESTED AND WORKING
	"""A combination of the Total and Positive storage. Used to set a limit and ensure
	there are no negative amounts in the storage."""
	def __init__(self, space, **kwargs):
		super(PositiveTotalStorage, self).__init__(space = space, **kwargs)
		self.limit = space

class SizedSlotStorage(PositiveStorage): # TESTED AND WORKING
	"""A storage consisting of a slot for each ressource, all slots have the same size 'limit'
	Used by the branch office for example. So with a limit of 30 you could have a max of
	30 from each resource."""
	def __init__(self, limit, **kwargs):
		super(SizedSlotStorage, self).__init__(**kwargs)
		self.limit = limit

	def alter(self, res, amount):
		check = max(0, amount + self[res] - self.limit)
		return check + super(SizedSlotStorage, self).alter(res, amount - check)


class PositiveSizedSpecializedStorage(PositiveStorage, SizedSpecializedStorage):
	pass
