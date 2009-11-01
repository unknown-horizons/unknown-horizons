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
from buildable import BuildableSingle, BuildableSingleOnCoast

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
		self.__init(self.settlement)
		self.inventory.adjust_limits(30)

	def __init(self, settlement):
		self.inventory = settlement.inventory
		self.inventory.add_change_listener(self._changed)

	def remove(self):
		super(StorageBuilding, self).remove()

	def __del__(self):
		self.inventory.adjust_limits(-30)

	def load(self, db, worldid):
		super(StorageBuilding, self).load(db, worldid)
		# workaround to get settlement (self.settlement is assigned just after loading)
		settlement_id = db("SELECT location FROM building WHERE rowid = ?", worldid)[0][0]
		settlement = WorldObject.get_object_by_id(int(settlement_id))
		self.__init(settlement)

	def select(self):
		"""Runs necessary steps to select the unit."""
		# TODO Think about if this should go somewhere else (island, world)
		self.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		for tile in self.island.grounds:
			if tile.settlement == self.settlement and any(x in tile.__class__.classes for x in ('constructible', 'coastline')):
				self.session.view.renderer['InstanceRenderer'].addColored(tile._instance, 255, 255, 255)
				if tile.object is not None:
					self.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)

	def deselect(self):
		"""Runs neccassary steps to deselect the unit."""
		self.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		self.session.view.renderer['InstanceRenderer'].removeAllColored()

class BranchOffice(StorageBuilding, BuildableSingleOnCoast):
	tearable = False
	@classmethod
	def _is_settlement_build_requirement_satisfied(cls, x, y, island, ship, **state):
		for settlement in island.settlements:
			if settlement.owner.id == ship.owner.id:
				return {'buildable' : False}
		#ship check
		if (max(x - ship.position.x, 0, ship.position.x - x - cls.size[0] + 1) ** 2) + \
		   (max(y - ship.position.y, 0, ship.position.y - y - cls.size[1] + 1) ** 2) > 25:
			return {'buildable' : False}
		return {'settlement' : None}


class MarketPlace(StorageBuilding):
	tabs = (MarketPlaceOverviewTab, AccountTab, MarketPlaceSettlerTabSettlerTab)

	def select(self):
		# storage buildings select whole settlement; market place should behave normally
		return SelectableBuilding.select(self)
