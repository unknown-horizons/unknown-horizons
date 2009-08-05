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

import horizons.main

from storage import SizedSlotStorage

class StorageHolder(object):
	"""The StorageHolder class is used as as a parent class for everything that
	has an inventory. Examples for these classes are ships, settlements,
	buildings, etc. Basically it just add's an inventory, nothing more, nothing
	less.
	If you want something different than a SizedSlotStorage, you'll have to
	overwrite that in the subclass.

	TUTORIAL:
	Continue to horizons/world/provider.py for further digging.
	"""
	def __init__(self, **kwargs):
		super(StorageHolder, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		self.create_inventory()

	def create_inventory(self):
		"""Some buildings don't have an own inventory (e.g. storage building). Those can just
		overwrite this function to do nothing. see also: save_inventory() and load_inventory()"""
		self.inventory = SizedSlotStorage(30)
		self.inventory.add_change_listener(self._changed)

	def save(self, db):
		super(StorageHolder, self).save(db)
		self.save_inventory(db)

	def save_inventory(self, db):
		"""see create_inventory()"""
		self.inventory.save(db, self.getId())

	def load(self, db, worldid):
		super(StorageHolder, self).load(db, worldid)
		self.__init()
		self.load_inventory(db, worldid)

	def load_inventory(self, db, worldid):
		self.inventory.load(db, worldid)
