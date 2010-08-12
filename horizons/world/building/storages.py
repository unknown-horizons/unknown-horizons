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

from horizons.world.resourcehandler import StorageResourceHandler
from horizons.world.building.collectingbuilding import CollectingBuilding
from horizons.gui.tabs import BranchOfficeOverviewTab, BuySellTab, InventoryTab, \
		 MarketPlaceOverviewTab, AccountTab, MarketPlaceSettlerTabSettlerTab
from horizons.util import WorldObject
from building import BasicBuilding, SelectableBuilding
from buildable import BuildableSingle, BuildableSingleFromShip
from horizons.constants import STORAGE
from horizons.world.production.producer import ProducerBuilding

class StorageBuilding(SelectableBuilding, BuildableSingle, StorageResourceHandler, \
                      CollectingBuilding, BasicBuilding):
	"""Building that gets pickups and provides them for anyone.
	Inherited eg. by branch office, storage tent.
	These objects don't have a storage themselves, but use the settlement storage.
	"""
	tabs = (BranchOfficeOverviewTab, InventoryTab, BuySellTab, AccountTab)
	has_own_inventory = False # we share island inventory
	def __init__(self, x, y, owner, instance = None, **kwargs):
		super(StorageBuilding, self).__init__(x = x, y = y, owner = owner, instance = instance, **kwargs)
		self.__init()

	def __init(self):
		self.inventory.adjust_limit(STORAGE.DEFAULT_STORAGE_SIZE)

	def create_inventory(self):
		self.inventory = self.settlement.inventory
		self.inventory.add_change_listener(self._changed)

	def remove(self):
		# this shouldn't be absolutely necessary since the changelistener uses weak references
		self.inventory.remove_change_listener(self._changed)
		self.inventory.adjust_limit(-STORAGE.DEFAULT_STORAGE_SIZE)
		super(StorageBuilding, self).remove()

	def load(self, db, worldid):
		super(StorageBuilding, self).load(db, worldid)
		self.__init()

class BranchOffice(StorageBuilding, BuildableSingleFromShip):
	tearable = False

class MarketPlace(ProducerBuilding, StorageBuilding):
	tabs = (MarketPlaceOverviewTab, AccountTab, MarketPlaceSettlerTabSettlerTab)

	def _load_provided_resources(self):
		"""Storages provide every res.
		"""
		return self.session.db.get_res(only_tradeable=False)
