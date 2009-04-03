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

from storage import SizedSlotStorage
import horizons.main

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
		# FIXME: StorageBuildings inherit this indirectly via Consumer/Provider,
		#       but since they don't have an own storage, these methods shouldn't be applied,
		#       which is currently handled by isinstance, a rather dirty solution.
		from horizons.world.building.storages import StorageBuilding
		if not isinstance(self, StorageBuilding):
			self.inventory = SizedSlotStorage(30)
			self.inventory.addChangeListener(self._changed)

	def save(self, db):
		super(StorageHolder, self).save(db)
		from horizons.world.building.storages import StorageBuilding
		if not isinstance(self, StorageBuilding):
			self.inventory.save(db, self.getId())

	def load(self, db, worldid):
		super(StorageHolder, self).load(db, worldid)
		self.__init()
		from horizons.world.building.storages import StorageBuilding
		if not isinstance(self, StorageBuilding):
			self.inventory.load(db, worldid)
