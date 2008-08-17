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

from game.util.stablelist import stablelist
from game.util import WorldObject
import game.main

class Storage(WorldObject):
	"""Class that represent a storage compartment with fixed resources slots

	Used e.g. by production buildings (e.g. PrimaryProducer)
	"""
	def __init__(self, **kwargs):
		super(Storage, self).__init__(**kwargs)
		# inventory: a dict with this pattern: _inventory[res_id] = [amount, size]
		self._inventory = {}

	def addSlot(self, res_id, size):
		""" Add the possibility to save size amount of res_id
		@param res_id: id of the resource
		@param size: maximum amount of res_id that can be stored here; -1 for infinity
		"""
		self._inventory[res_id] = [0, size]
		self._changed()

	def hasSlot(self, res_id):
		""" Returns wether slot for res_id exists"""
		return (res_id in self._inventory.keys())

	def alter_inventory(self, res_id, amount):
		"""Alters the inventory for the resource res_id with amount.
		@param res_id: int resource_id
		@param amount: amount that is to be added.
		@return: amount that couldn't be stored in this storage"""
		new_amount = 0
		try:
			new_amount = self._inventory[res_id][0] + amount
		except KeyError:
			return amount
		if new_amount > self.get_size(res_id) and self.get_size(res_id) != -1:
			# stuff doesn't fit in inventory
			ret = new_amount - self.get_size(res_id)
			self._inventory[res_id][0] = self.get_size(res_id)
			self._changed()
			return ret
		elif new_amount < 0:
			# trying to take more stuff than inventory contains
			ret = new_amount
			self._inventory[res_id][0] = 0
			self._changed()
			return ret
		else:
			# new amount is in boundaries
			self._inventory[res_id][0] = new_amount
			self._changed()
			return 0

	def get_value(self, res_id):
		"""Returns amount of resource res_id in the storage
		NOTE: this returns "false" value depending on carriages, that are on their way
					alter_inventory always returns acctual value of res currently in the building
		@param res_id: int resource_id
		@return: int amount of resources for res_id in inventory.
		"""
		try:
			value = self._inventory[res_id][0]

			# subtract/add carriage stuff
			"""
			for carriage in self.building.pickup_carriages:
				if len(carriage.target) > 0:
					if carriage.target[1] == res_id:
						value -= carriage.target[2]
			for carriage in self.building.local_carriages:
				if len(carriage.target) > 0:
					if carriage.target[1] == res_id:
						value += carriage.target[2]
			"""

			return value
		except KeyError:
			return 0

	def get_size(self, res_id):
		""" Returns the capacity of the storage for resource res_id
		@param res_id: int resource_id
		"""
		return self._inventory[res_id][1]

	def __repr__(self):
		return repr(self._inventory)

	def __str__(self):
		return str(self._inventory)
	
	def save(self, db, ownerid):
		super(Storage, self).save(db)
		for (res, (value, size)) in self._inventory.iteritems():
			db("INSERT INTO storage (object, resource, amount) VALUES (?, ?, ?) ",
				ownerid, res, value)
				
	def load(self, db, ownerid):
		super(Storage, self).save(db)
		for (res, amount) in db("SELECT resource, amount FROM storage WHERE object = ?", ownerid):
			self.alter_inventory(res, amount)
		

class ArbitraryStorage(WorldObject):
	"""Class that represents a storage compartment for ships
	Storages have a certain number of slots and a certain maximum number of
	resources that they can store for a certain slot.
	"""
	def __init__(self, slots, size):
		self._inventory = stablelist()
		self.slots = slots
		self.size = size

	def alter_inventory(self, res_id, amount):
		# try using existing slots
		for slot in self._inventory:
			if slot[0] == res_id:
				new_amount = slot[1] + amount
				if new_amount < 0:
					slot[1] = 0
					amount = new_amount
				elif new_amount > self.size:
					slot[1] = self.size
					amount = new_amount - self.size
				else:
					slot[1] = new_amount
					self._changed()
					return 0

		# handle stuff that couldn't be handled with existing slots
		if amount > 0:
			if len(self._inventory) < self.slots:
				if amount > self.size:
					self._inventory.append([res_id, self.size])
					self._changed()
					return self.alter_inventory(res_id, amount - self.size)
				else:
					self._inventory.append([res_id, amount])
					amount = 0

		# return what couldn't be added/taken
		self._changed()
		return amount

	def get_value(self, res_id):
		ret = 0
		for slot in self._inventory:
			if slot[0] == res_id:
				ret += slot[1]
		return ret

	def get_size(self, res_id):
		"""This just ensures compatibility with Storage"""
		## TODO: if carriage is on the way, ensure that other slots won't get filled
		size = 0
		for slot in self._inventory:
			if slot[0] == res_id and slot[1] < self.size:
				size += self.size - slot[1]

		size += (self.slots - len(self._inventory)) * self.size
		return size
	
	def save(self, db, ownerid):
		super(Storage, self).save(db)
		for slot in self._inventory:
			db("INSERT INTO storage (object, resource, amount) VALUES (?, ?, ?) ",
				ownerid, slot[0], slot[1])
			
	def load(self, db, ownerid):
		super(Storage, self).load(db)
		for (res, amount) in db("SELECT resource, amount FROM storage WHERE object = ?", ownerid):
			self.alter_inventory(res, amount)
		
			
class GenericStorage(object):
	def __init__(self, **kwargs):
		super(GenericStorage, self).__init__(**kwargs)
		self._storage = {}

	def alter(res, amount):
		if res in self._storage:
			self._storage[res] += amount
		else:
			self._storage[res] = amount
		return 0

	def __getitem__(self, res):
		return self._storage[res] if res in self._storage else 0

class SpecializedStorage(GenericStorage):
	def alter(res, amount):
		return super(SpecializedStorage, self).alter(res, amount) if res in self._storage else amount

	def addResourceSlot(res):
		super(SpecializedStorage, self).alter(res, 0)

	def hasResourceSlot(res):
		return res in self._storage

class SizedSpecializedStorage(SpecializedStorage):
	def __init__(self, **kwargs):
		super(SizedSpecializedStorage, self).__init__(**kwargs)
		self.__size = {}
	
	def alter(res, amount):
		return amount - super(SizedSpecializedStorage, self).alter(res, amount - max(0, amount + self[res] - self.__size.get(res,0)))

	def addResourceSlot(res, size, **kwargs):
		super(SpecializedStorage, self).addResourceSlot(res = res, size = size, **kwargs)
		self.__size[res] = size

class TotalStorage(GenericStorage):
	def __init__(self, space, **kwargs):
		super(TotalStorage, self).__init__(space = space, **kwargs)
		self.__space = space

	def alter(self, res, amount):
		return amount - super(TotalStorage, self).alter(res, amount - max(0, amount + sum(self._storage.values()) - self.__space))

class PositiveStorage(GenericStorage):
	def alter(res, amount):
		return amount - super(PositiveStorage, self).alter(res, amount - min(0, amount + self[res]))

class PositiveTotalStorage(PositiveStorage, TotalStorage):
	pass

class PositiveSizedSpecializedStorage(PositiveStorage, SizedSpecializedStorage):
	pass
