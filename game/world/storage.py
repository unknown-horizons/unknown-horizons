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

class Storage(object):
	"""Class that represent a storage compartment for ships/houses/players.
	Storages have a certain number of slots and a certain maximum number of
	ressources that they can store for a certain slot.
	"""
	def __init__(self, slots=None, size=None):
		self._inventory = {}
		self.slots = slots
		self.size = size

	def alter_inventory(self, res_id, amount):
		"""Alters the inventory for the ressource res_id with amount.
		@param res_id: int ressource_id
		@param amount: amount that is to be added."""

		if res_id not in self._inventory:
			if amount > 0 and (self.slots == None or len(self._inventory) < self.slots):
				self._inventory[res_id] = amount if self.size is None else min(amount, self.size)
				return amount - self._inventory[res_id]
			else:
				return amount
		elif amount > 0:
			self._inventory[res_id] = self._inventory[res_id] + amount
			if self.size != None and self._inventory[res_id] > self.size:
				ret = self._inventory[res_id] - self.size
				self._inventory[res_id] = self.size
				return ret
			else:
				return 0
		elif amount < 0:
			self._inventory[res_id] = self._inventory[res_id] + amount
			if self._inventory[res_id] <= 0:
				ret = self._inventory[res_id]
				del self._inventory[res_id]
				return ret
			else:
				return 0
		return 0

	def get_value(self, key):
		"""@param key: int ressource_id
		@return int amount of ressources for key in inventory. If not in inventory 0."""
		return self._inventory.get(key, 0)

	def __repr__(self):
		return repr(self._inventory)

	def __str__(self):
		return str(self._inventory)


