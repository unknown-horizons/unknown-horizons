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

from horizons.component import Component
from horizons.world.storage import PositiveSizedSlotStorage, PositiveStorage, PositiveSizedSpecializedStorage, SettlementStorage, PositiveTotalNumSlotsStorage

class StorageComponent(Component):
	"""The StorageComponent class is used as as a parent class for everything that
	has an inventory. Examples for these classes are ships, settlements,
	buildings, etc. Basically it just adds an inventory, nothing more, nothing
	less.
	If you want something different than a PositiveSizedSlotStorage, you'll have to
	overwrite that in the subclass.

	TUTORIAL:
	Continue to horizons/world/provider.py for further digging.
	"""

	NAME = 'storagecomponent'

	storage_mapping = {
	    'PositiveStorage': PositiveStorage,
	    'PositiveSizedSlotStorage': PositiveSizedSlotStorage,
	    'PositiveTotalNumSlotStorage': PositiveTotalNumSlotsStorage,
	    'SlotsStorage': PositiveSizedSpecializedStorage,
	    'SettlementStorage': SettlementStorage # pseudo storage meaning to share settlement storage
	    }

	def __init__(self, inventory):
		super(StorageComponent, self).__init__()
		self.inventory = inventory

		# SettlementStorage is used as flag to signal using another inventory
		self.has_own_inventory = not isinstance(self.inventory, SettlementStorage)

	def initialize(self):
		# NOTE: also called on load (initialize usually isn't)
		if not self.has_own_inventory:
			self.inventory = self.instance.settlement.get_component(StorageComponent).inventory

	def remove(self):
		super(StorageComponent, self).remove()
		if self.has_own_inventory:
			# no changelister calls on remove
			self.inventory.clear_change_listeners()
			# remove inventory to prevent any action here in subclass remove
			self.inventory.reset_all()

	def save(self, db):
		super(StorageComponent, self).save(db)
		if self.has_own_inventory:
			self.inventory.save(db, self.instance.worldid)

	def load(self, db, worldid):
		super(StorageComponent, self).load(db, worldid)
		self.initialize()
		if self.has_own_inventory:
			self.inventory.load(db, worldid)

	@classmethod
	def get_instance(cls, arguments):
		key, value = arguments.iteritems().next()
		storage = cls.storage_mapping[key]
		inventory = storage(**value)
		return cls(inventory=inventory)
