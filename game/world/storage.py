# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

from game.util import WorldObject
import game.main

class GenericStorage(WorldObject): # TESTED, WORKS
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
		if res in self._storage:
			self._storage[res] += amount
		else:
			self._storage[res] = amount
		self._changed()
		return 0

	def get_limit(self, res):
		return self.limit # should not be used for generic storage

	def __getitem__(self, res):
		return self._storage[res] if res in self._storage else 0

	def __str__(self):
		return str(self._storage)

class SpecializedStorage(GenericStorage): # NOT TESTED! NEEDS WORK!
	def alter(self, res, amount):
		return super(SpecializedStorage, self).alter(res, amount) if res in self._storage else amount

	def addResourceSlot(res):
		super(SpecializedStorage, self).alter(res, 0)

	def hasResourceSlot(res):
		return res in self._storage

class SizedSpecializedStorage(SpecializedStorage): # NOT TESTED, NEEDS WORK!
	def __init__(self, **kwargs):
		super(SizedSpecializedStorage, self).__init__(**kwargs)
		self.__size = {}

	def alter(self, res, amount):
		return amount - super(SizedSpecializedStorage, self).alter(res, amount - max(0, amount + self[res] - self.__size.get(res,0)))

	def get_limit(self, res):
		return self.__size[res]

	def addResourceSlot(self, res, size, **kwargs):
		super(SpecializedStorage, self).addResourceSlot(res = res, size = size, **kwargs)
		self.__size[res] = size
		
	def save(self, db, ownerid):
		super(SizedSpecializedStorage, self).save(db, ownerid)
		assert False, "Saving of SizedSpecializedStorage hasn't been implemented"
		
	def load(self, db, ownerid):
		super(SizedSpecializedStorage, self).save(db, ownerid)
		assert False, "Loading of SizedSpecializedStorage hasn't been implemented"


class TotalStorage(GenericStorage): # TESTED AND WORKING
	def __init__(self, space, **kwargs):
		super(TotalStorage, self).__init__(space = space, **kwargs)
		self.limit = space

	def alter(self, res, amount):
		check =  max(0, amount + sum(self._storage.values()) - self.limit)
		return check + super(TotalStorage, self).alter(res, amount - check)

class PositiveStorage(GenericStorage): # TESTED AND WORKING
	def alter(self, res, amount):
		ret = min(0, amount + self[res]) + super(PositiveStorage, self).alter(res, amount - min(0, amount + self[res]))
		if res in self._storage and self._storage[res] <= 0:
			del self._storage[res]
		return ret

class PositiveTotalStorage(PositiveStorage, TotalStorage): # TESTED AND WORKING
	def __init__(self, space, **kwargs):
		super(TotalStorage, self).__init__(space = space, **kwargs)
		self.limit = space

class SizedSlotStorage(PositiveStorage): # TESTED AND WORKING
	"""A storage consisting of a slot for each ressource, all slots have the same size 'limit'
	Used by the branch office for example."""
	def __init__(self, limit, **kwargs):
		super(SizedSlotStorage, self).__init__(**kwargs)
		self.limit = limit

	def alter(self, res, amount):
		check = max(0, amount + self[res] - self.limit)
		return check + super(SizedSlotStorage, self).alter(res, amount - check)

	def adjust_limits(self, amount):
		self.limit += amount
		if self.limit < 0:
			self.limit = 0

class PositiveSizedSpecializedStorage(PositiveStorage, SizedSpecializedStorage):
	pass
