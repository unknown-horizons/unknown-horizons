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
	def __init__(self, slots=4, size=50):
		self._inventory = {}
		self.slots = slots
		self.size = size

	def alter_inventory(self, res_id, amount):
		"""Alters the inventory for the ressource res_id with amount.
		@param res_id: int ressource_id
		@param amount: amount that is to be added."""
		back = None
		try:
			if amount > 0 and self._inventory[res_id] < self.size:
				self._inventory[res_id] += amount
				res = divmod(self._inventory[res_id], self.size)
				back = res[1] if res[0] >= 1 else 0
				if back > 0:
					self._inventory[res_id] = self.size
			elif amount < 0:
				self._inventory[res_id] += amount
				back = 0 if self._inventory[res_id] >= 0 else abs(self._inventory[res_id])
				if self._inventory[res_id] <= 0:
					del self._inventory[res_id]
		except KeyError:
			if len(self._inventory) < self.slots:
				self._inventory[res_id] = amount
				res = divmod(self._inventory[res_id], self.size)
				back = res[1] if res[0] >= 1 else 0
				if back > 0:
					self._inventory[res_id] = self.size
		finally:
			return back

	def get_value(self, key):
		"""@param key: int ressource_id
		@return int amount of ressources for key in inventory. If not in inventory 0."""
		try:
			return self._inventory[key]
		except KeyError:
			return 0

