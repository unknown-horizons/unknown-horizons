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

import json
import logging
from collections import defaultdict

from horizons.component.componentholder import ComponentHolder
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import BUILDINGS, TIER
from horizons.messaging import SettlementInventoryUpdated, UpgradePermissionsChanged
from horizons.scheduler import Scheduler
from horizons.util.changelistener import ChangeListener
from horizons.util.inventorychecker import InventoryChecker
from horizons.util.worldobject import WorldObject
from horizons.world.buildability.settlementcache import SettlementBuildabilityCache
from horizons.world.production.producer import GroundUnitProducer, Producer, ShipProducer
from horizons.world.resourcehandler import ResourceHandler


class Settlement(ComponentHolder, WorldObject, ChangeListener, ResourceHandler):
	"""The Settlement class describes a settlement and stores all the necessary information
	like name, current inhabitants, lists of tiles and houses, etc belonging to the village."""

	log = logging.getLogger("world.settlement")

	component_templates = (
		{
			'StorageComponent':
				{'PositiveSizedSlotStorage':
					{'limit': 0}
				}
		},
		'TradePostComponent',
		'SettlementNameComponent',
	)

	def __init__(self, session, owner):
		"""
		@param owner: Player object that owns the settlement
		"""
		super().__init__()
		self.__init(session, owner, self.make_default_upgrade_permissions(), self.make_default_tax_settings())

	def __init(self, session, owner, upgrade_permissions, tax_settings):
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.owner = owner
		self.buildings = []
		self.ground_map = {} # this is the same as in island.py. it uses hard references to the tiles too
		self.produced_res = defaultdict(int) # dictionary of all resources, produced at this settlement
		self.buildings_by_id = defaultdict(list)
		self.warehouse = None # this is set later in the same tick by the warehouse itself or load() here
		self.upgrade_permissions = upgrade_permissions
		self.tax_settings = tax_settings
		Scheduler().add_new_object(self.__init_inventory_checker, self)

	def init_buildability_cache(self, terrain_cache):
		self.buildability_cache = SettlementBuildabilityCache(terrain_cache, self.ground_map)
		self.buildability_cache.modify_area(self.ground_map.keys())

	@classmethod
	def make_default_upgrade_permissions(cls):
		upgrade_permissions = {}
		for level in range(TIER.CURRENT_MAX):
			upgrade_permissions[level] = True
		upgrade_permissions[TIER.CURRENT_MAX] = False
		return upgrade_permissions

	@classmethod
	def make_default_tax_settings(cls):
		tax_settings = {}
		for level in range(TIER.CURRENT_MAX + 1):
			tax_settings[level] = 1.0
		return tax_settings

	def set_tax_setting(self, level, tax):
		self.tax_settings[level] = tax

	def set_upgrade_permissions(self, level, allowed):
		if self.upgrade_permissions[level] != allowed:
			self.upgrade_permissions[level] = allowed

			UpgradePermissionsChanged.broadcast(self)

	@property
	def inhabitants(self):
		"""Returns number of inhabitants (sum of inhabitants of its buildings)"""
		return sum([building.inhabitants for building in self.buildings])

	@property
	def cumulative_running_costs(self):
		"""Return sum of running costs of all buildings"""
		return sum([building.running_costs for building in self.buildings])

	@property
	def cumulative_taxes(self):
		"""Return sum of all taxes paid in this settlement in 1 tax round"""
		return sum([building.last_tax_payed for building in self.buildings if
								hasattr(building, 'last_tax_payed')])

	def get_residentials_of_lvl_for_happiness(self, level, min_happiness=0, max_happiness=101):
		is_valid_residential = lambda building: (hasattr(building, 'happiness') and
		                                         min_happiness <= building.happiness < max_happiness) and \
		                                        (hasattr(building, 'level') and building.level == level)
		return len(list(filter(is_valid_residential, self.buildings)))

	@property
	def balance(self):
		"""Returns sum(income) - sum(expenses) for settlement"""
		return self.cumulative_taxes + self.get_component(TradePostComponent).sell_income \
					 - self.cumulative_running_costs - self.get_component(TradePostComponent).buy_expenses

	@property
	def island(self):
		"""Returns the island this settlement is on"""
		return self.session.world.get_island(self.warehouse.position.origin)

	def level_upgrade(self, lvl):
		"""Upgrades settlement to a new tier.
		It only delegates the upgrade to its buildings."""
		for building in self.buildings:
			building.level_upgrade(lvl)

	def save(self, db, islandid):
		super().save(db)

		db("INSERT INTO settlement (rowid, island, owner) VALUES(?, ?, ?)",
			self.worldid, islandid, self.owner.worldid)
		for res, amount in self.produced_res.items():
			db("INSERT INTO settlement_produced_res (settlement, res, amount) VALUES(?, ?, ?)",
			   self.worldid, res, amount)
		for level in range(TIER.CURRENT_MAX + 1):
			db("INSERT INTO settlement_level_properties (settlement, level, upgrading_allowed, tax_setting) VALUES(?, ?, ?, ?)",
				self.worldid, level, self.upgrade_permissions[level], self.tax_settings[level])

		# dump ground data via json, it's orders of magnitude faster than sqlite
		data = json.dumps(list(self.ground_map.keys()))
		db("INSERT INTO settlement_tiles(rowid, data) VALUES(?, ?)", self.worldid, data)

	@classmethod
	def load(cls, db, worldid, session, island):
		self = cls.__new__(cls)
		self.session = session
		super(Settlement, self).load(db, worldid)

		owner = db("SELECT owner FROM settlement WHERE rowid = ?", worldid)[0][0]
		upgrade_permissions = {}
		tax_settings = {}
		for level, allowed, tax in db("SELECT level, upgrading_allowed, tax_setting FROM settlement_level_properties WHERE settlement = ?", worldid):
			upgrade_permissions[level] = allowed
			tax_settings[level] = tax
		self.__init(session, WorldObject.get_object_by_id(owner), upgrade_permissions, tax_settings)

		# load the settlement tile map
		tile_data = db("SELECT data FROM settlement_tiles WHERE rowid = ?", worldid)[0][0]
		coords_list = [tuple(raw_coords) for raw_coords in json.loads(tile_data)] # json saves tuples as list
		for coords in coords_list:
			tile = island.ground_map[coords]
			self.ground_map[coords] = tile
			tile.settlement = self

		# load all buildings in this settlement
		from horizons.world import load_building
		for building_id, building_type in \
			  db("SELECT rowid, type FROM building WHERE location = ?", worldid):
			building = load_building(session, db, building_type, building_id)
			if building_type == BUILDINGS.WAREHOUSE:
				self.warehouse = building

		for res, amount in db("SELECT res, amount FROM settlement_produced_res WHERE settlement = ?", worldid):
			self.produced_res[res] = amount

		return self

	def get_tiles_in_radius(self, location, radius, include_self):
		"""Returns tiles in radius of location.
		This is a generator.
		@param location: anything that supports get_radius_coordinates (usually Rect).
		@param include_self: bool, whether to include the coordinates in location
		"""
		for coord in location.get_radius_coordinates(radius, include_self):
			try:
				yield self.ground_map[coord]
			except KeyError:
				pass

	def add_building(self, building, load=False):
		"""Adds a building to the settlement.
		This does not set building.settlement, it must be set beforehand.
		@see Island.add_building
		"""
		self.buildings.append(building)
		if building.id in self.buildings_by_id:
			self.buildings_by_id[building.id].append(building)
		else:
			self.buildings_by_id[building.id] = [building]
		component = building.get_component(Producer)
		if component and component.produces_resource:
			finished = self.settlement_building_production_finished
			building.get_component(Producer).add_production_finished_listener(finished)
		if not load and not building.buildable_upon and self.buildability_cache:
			self.buildability_cache.modify_area([coords for coords in building.position.tuple_iter()])
		if hasattr(self.owner, 'add_building'):
			# notify interested players of added building
			self.owner.add_building(building)

	def remove_building(self, building):
		"""Properly removes a building from the settlement"""
		if building not in self.buildings:
			self.log.debug("Building %s can not be removed from settlement", building.id)
			return
		self.buildings.remove(building)
		self.buildings_by_id[building.id].remove(building)
		component = building.get_component(Producer)
		if component and component.produces_resource:
			finished = self.settlement_building_production_finished
			building.get_component(Producer).remove_production_finished_listener(finished)
		if not building.buildable_upon and self.buildability_cache:
			self.buildability_cache.add_area([coords for coords in building.position.tuple_iter()])
		if hasattr(self.owner, 'remove_building'):
			# notify interested players of removed building
			self.owner.remove_building(building)

	def count_buildings(self, id):
		"""Returns the number of buildings in the settlement that are of the given type."""
		return len(self.buildings_by_id.get(id, []))

	def settlement_building_production_finished(self, building, produced_res):
		"""Callback function for registering the production of resources."""
		for res, amount in produced_res.items():
			self.produced_res[res] += amount

	def __init_inventory_checker(self):
		"""Check for changed inventories every 4 ticks."""
		storage = self.get_component(StorageComponent)
		self.__inventory_checker = InventoryChecker(SettlementInventoryUpdated, storage, 4)

	def end(self):
		self.buildability_cache = None
		self.session = None
		self.owner = None
		self.buildings = None
		self.ground_map = None
		self.produced_res = None
		self.buildings_by_id = None
		self.warehouse = None
		if hasattr(self, '__inventory_checker'):
			self.__inventory_checker.remove()
