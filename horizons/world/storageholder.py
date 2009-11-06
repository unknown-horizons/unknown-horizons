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

from storage import PositiveSizedSlotStorage, PositiveSizedSpecializedStorage
from horizons.constants import STORAGE

class StorageHolder(object):
	"""The StorageHolder class is used as as a parent class for everything that
	has an inventory. Examples for these classes are ships, settlements,
	buildings, etc. Basically it just adds an inventory, nothing more, nothing
	less.
	If you want something different than a PositiveSizedSlotStorage, you'll have to
	overwrite that in the subclass.

	TUTORIAL:
	Continue to horizons/world/provider.py for further digging.
	"""
	has_own_inventory = True # some objs share inventory, which requires different handling here.

	def __init__(self, **kwargs):
		super(StorageHolder, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		if self.has_own_inventory:
			self.create_inventory()
			self.inventory.add_change_listener(self._changed)

	def remove(self):
		super(StorageHolder, self).remove()
		if self.has_own_inventory:
			# no changelister calls on remove
			self.inventory.clear_change_listeners()
			# remove inventory to prevent any action here in subclass remove
			self.inventory.reset_all()

	def create_inventory(self):
		"""Some buildings don't have an own inventory (e.g. storage building). Those can just
		overwrite this function to do nothing. see also: save_inventory() and load_inventory()"""
		db_data = horizons.main.db("SELECT resource, size FROM balance.storage WHERE object_id = ?", \
		                           self.id)

		if len(db_data) == 0:
			# no db data about inventory. Create default inventory.
			self.inventory = PositiveSizedSlotStorage(STORAGE.DEFAULT_STORAGE_SIZE)
		else:
			# specialised storage; each res and limit is stored in db.
			self.inventory = PositiveSizedSpecializedStorage()
			for res, size in db_data:
				self.inventory.add_resource_slot(res, size)

	def save(self, db):
		super(StorageHolder, self).save(db)
		if self.has_own_inventory:
			self.inventory.save(db, self.getId())

	def load(self, db, worldid):
		super(StorageHolder, self).load(db, worldid)
		self.__init()
		if self.has_own_inventory:
			self.inventory.load(db, worldid)

