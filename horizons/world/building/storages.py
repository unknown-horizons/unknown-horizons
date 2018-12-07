# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.component.collectingcomponent import CollectingComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.world.building.buildable import BuildableSingle, BuildableSingleFromShip
from horizons.world.building.building import BasicBuilding
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.building.path import Path
from horizons.world.building.production import ProductionBuilding
from horizons.world.resourcehandler import StorageResourceHandler
from horizons.world.status import InventoryFullStatus


class StorageBuilding(StorageResourceHandler,
                      BuildingResourceHandler, BasicBuilding):
	"""Building that gets pickups and provides them for anyone.
	Inherited eg. by warehouse, storage tent.
	These objects don't have a storage themselves, but use the settlement storage.
	"""
	def __init__(self, x, y, owner, instance=None, **kwargs):
		super().__init__(x=x, y=y, owner=owner, instance=instance, **kwargs)

	def initialize(self):
		super().initialize()
		self.get_component(StorageComponent).inventory.add_change_listener(self._changed)
		# add limit, it will be saved so don't set on load()
		inv = self.get_component(StorageComponent).inventory
		inv.adjust_limit(self.session.db.get_storage_building_capacity(self.id))

	def remove(self):
		inv = self.get_component(StorageComponent).inventory
		inv.remove_change_listener(self._changed)
		inv.adjust_limit(-self.session.db.get_storage_building_capacity(self.id))
		super().remove()

	def load(self, db, worldid):
		super().load(db, worldid)
		# limit will be save/loaded by the storage, don't do anything here
		self.get_component(StorageComponent).inventory.add_change_listener(self._changed)

	def get_utilization_history_length(self):
		collecting_comp = self.get_component(CollectingComponent)
		if collecting_comp.get_local_collectors():
			return collecting_comp.get_local_collectors()[0].get_utilization_history_length()

	def get_collector_utilization(self):
		collectors = self.get_component(CollectingComponent).get_local_collectors()
		if not collectors:
			return None
		return sum(collector.get_utilization() for collector in collectors) / float(len(collectors))


class StorageTent(StorageBuilding, BuildableSingle):
	"""Can't inherit from Buildable* in StorageBuilding because of mro issues."""
	pass


class Warehouse(StorageBuilding, BuildableSingleFromShip):
	tearable = False

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settlement.warehouse = self
		# we never need to unset this since warehouses are indestructible
		# settlement warehouse setting is done at the settlement for loading

	def get_status_icons(self):
		banned_classes = (InventoryFullStatus,)
		return [i for i in super().get_status_icons() if
		        i.__class__ not in banned_classes]


class MainSquare(Path, StorageBuilding, ProductionBuilding):
	walkable = True

	def recalculate_orientation(self):
		# change gfx according to roads here
		pass

	def _load_provided_resources(self):
		"""Storages provide every res.
		"""
		return self.session.db.get_res(only_tradeable=False)
