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

import logging
from collections import defaultdict

from horizons.command.building import Tear
from horizons.constants import BUILDINGS, RES, UNITS
from horizons.entities import Entities
from horizons.gui.widgets.minimap import Minimap
from horizons.messaging import NewSettlement, SettlementRangeChanged
from horizons.scenario import CONDITIONS
from horizons.scheduler import Scheduler
from horizons.util.buildingindexer import BuildingIndexer
from horizons.util.pathfinding.pathnodes import IslandBarrierNodes, IslandPathNodes
from horizons.util.shapes import Circle, Rect
from horizons.util.worldobject import WorldObject
from horizons.world.buildability.freeislandcache import FreeIslandBuildabilityCache
from horizons.world.buildability.terraincache import TerrainBuildabilityCache, TerrainRequirement
from horizons.world.buildingowner import BuildingOwner
from horizons.world.ground import MapPreviewTile
from horizons.world.settlement import Settlement


class Island(BuildingOwner, WorldObject):
	"""The Island class represents an island. It contains a list of all things on the map
	that belong to the island. This comprises ground tiles as well as buildings,
	nature objects (which are buildings), and units.
	All those objects also have a reference to the island, making it easy to determine to which island the instance belongs.
	An Island instance is created during map creation, when all tiles are added to the map.
	@param origin: Point instance - Position of the (0, 0) ground tile.
	@param filename: file from which the island is loaded.

	Each island holds some important attributes:
	* grounds - All ground tiles that belong to the island are referenced here.
	* grounds_map -  a dictionary that binds tuples of coordinates with a reference to the tile:
	                  { (x, y): tileref, ...}
					  This is important for pathfinding and quick tile fetching.
	* position - a Rect that borders the island with the smallest possible area.
	* buildings - a list of all Building instances that are present on the island.
	* settlements - a list of all Settlement instances that are present on the island.
	* path_nodes - a special dictionary used by the pather to save paths.

	TUTORIAL:
	Why do we use a separate __init() function, and do not use the __init__() function?
	Simple: if we load the game, the class is not loaded as a new instance, so the __init__
	function is not called. Rather, the load function is called, so everything that new
	classes and loaded classes share to initialize goes into the __init() function.
	This is the common way of doing this in Unknown Horizons, so better get used to it :)
	NOTE: The components work a bit different, but this code here is mostly not component oriented.

	To continue hacking, check out the __init() function now.
	"""
	log = logging.getLogger("world.island")

	def __init__(self, db, island_id, session, preview=False):
		"""
		@param db: db instance with island table
		@param island_id: id of island in that table
		@param session: reference to Session instance
		@param preview: flag, map preview mode
		"""
		super().__init__(worldid=island_id)

		self.session = session

		self.terrain_cache = None
		self.available_land_cache = None
		self.__init(db, island_id, preview)

		if not preview:
			# Create building indexers.
			from horizons.world.units.animal import WildAnimal
			self.building_indexers = {}
			self.building_indexers[BUILDINGS.TREE] = BuildingIndexer(WildAnimal.walking_range, self, self.session.random)

		# Load settlements.
		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", island_id):
			settlement = Settlement.load(db, settlement_id, self.session, self)
			self.settlements.append(settlement)

		if preview:
			# Caches and buildings are not required for map preview.
			return

		self.terrain_cache = TerrainBuildabilityCache(self)
		flat_land_set = self.terrain_cache.cache[TerrainRequirement.LAND][(1, 1)]
		self.available_flat_land = len(flat_land_set)
		available_coords_set = set(self.terrain_cache.land_or_coast)

		for settlement in self.settlements:
			settlement.init_buildability_cache(self.terrain_cache)
			for coords in settlement.ground_map:
				available_coords_set.discard(coords)
				if coords in flat_land_set:
					self.available_flat_land -= 1

		self.available_land_cache = FreeIslandBuildabilityCache(self)

		# Load buildings.
		from horizons.world import load_building
		buildings = db("SELECT rowid, type FROM building WHERE location = ?", island_id)
		for (building_worldid, building_typeid) in buildings:
			load_building(self.session, db, building_typeid, building_worldid)

	def __init(self, db, island_id, preview):
		"""
		Load the actual island from a file
		@param preview: flag, map preview mode
		"""
		p_x, p_y, width, height = db("SELECT MIN(x), MIN(y), (1 + MAX(x) - MIN(x)), (1 + MAX(y) - MIN(y)) FROM ground WHERE island_id = ?", island_id - 1001)[0]

		self.ground_map = {}
		for (x, y, ground_id, action_id, rotation) in db("SELECT x, y, ground_id, action_id, rotation FROM ground WHERE island_id = ?", island_id - 1001): # Load grounds
			if not preview: # actual game, need actual tiles
				ground = Entities.grounds[str('{:d}-{}'.format(ground_id, action_id))](self.session, x, y)
				ground.act(rotation)
			else:
				ground = MapPreviewTile(x, y, ground_id)
			# These are important for pathfinding and building to check if the ground tile
			# is blocked in any way.
			self.ground_map[(ground.x, ground.y)] = ground

		self._init_cache()

		# Contains references to all resource deposits (but not mines)
		# on the island, regardless of the owner:
		# {building_id: {(x, y): building_instance, ...}, ...}
		self.deposits = defaultdict(dict)

		self.settlements = []
		self.wild_animals = []
		self.num_trees = 0

		# define the rectangle with the smallest area that contains every island tile its position
		min_x = min(list(zip(*self.ground_map.keys()))[0])
		max_x = max(list(zip(*self.ground_map.keys()))[0])
		min_y = min(list(zip(*self.ground_map.keys()))[1])
		max_y = max(list(zip(*self.ground_map.keys()))[1])
		self.position = Rect.init_from_borders(min_x, min_y, max_x, max_y)

		if not preview:
			# This isn't needed for map previews, but it is in actual games.
			self.path_nodes = IslandPathNodes(self)
			self.barrier_nodes = IslandBarrierNodes(self)

			# Repopulate wild animals every 2 mins if they die out.
			Scheduler().add_new_object(self.check_wild_animal_population, self,
			                           run_in=Scheduler().get_ticks(120), loops=-1)

		"""TUTORIAL:
		The next step will be an overview of the component system, which you will need
		to understand in order to see how our actual game object (buildings, units) work.
		Please proceed to horizons/component/componentholder.py.
		"""

	def save(self, db):
		super().save(db)
		for settlement in self.settlements:
			settlement.save(db, self.worldid)
		for animal in self.wild_animals:
			animal.save(db)

	def get_coordinates(self):
		"""Returns list of coordinates, that are on the island."""
		return list(self.ground_map.keys())

	def get_tile(self, point):
		"""Returns whether a tile is on island or not.
		@param point: Point contains position of the tile.
		@return: tile instance if tile is on island, else None."""
		return self.ground_map.get((point.x, point.y))

	def get_tile_tuple(self, tup):
		"""Overloaded get_tile, takes a tuple as argument"""
		return self.ground_map.get(tup)

	def get_tiles_tuple(self, tuples):
		"""Same as get_tile, but takes a list of tuples.
		@param tuples: iterable of tuples
		@return: iterable of map tiles"""
		for tup in tuples:
			if tup in self.ground_map:
				yield self.ground_map[tup]

	def add_settlement(self, position, radius, player):
		"""Adds a settlement to the island at the position x, y with radius as area of influence.
		@param position: Rect describing the position of the new warehouse
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(self.session, player)
		settlement.initialize()
		settlement.init_buildability_cache(self.terrain_cache)
		self.add_existing_settlement(position, radius, settlement)
		NewSettlement.broadcast(self, settlement, position.center)

		return settlement

	def add_existing_settlement(self, position, radius, settlement):
		"""Same as add_settlement, but uses settlement from parameter.
		May also be called for extension of an existing settlement by a new building (this
		is useful for loading, where every loaded building extends the radius of its settlement).
		@param position: Rect
		@param load: whether it has been called during load"""
		if settlement not in self.settlements:
			self.settlements.append(settlement)
		self.assign_settlement(position, radius, settlement)
		self.session.scenario_eventhandler.check_events(CONDITIONS.settlements_num_greater)
		return settlement

	def assign_settlement(self, position, radius, settlement):
		"""Assigns the settlement property to tiles within the circle defined by \
		position and radius.
		@param position: Rect
		@param radius:
		@param settlement:
		"""
		settlement_coords_changed = []
		for coords in position.get_radius_coordinates(radius, include_self=True):
			if coords not in self.ground_map:
				continue

			tile = self.ground_map[coords]
			if tile.settlement is not None:
				continue

			tile.settlement = settlement
			settlement.ground_map[coords] = tile
			settlement_coords_changed.append(coords)

			building = tile.object
			# In theory fish deposits should never be on the island but this has been
			# possible since they were turned into a 2x2 building. Since they are never
			# entirely on the island then it is easiest to just make it impossible to own
			# fish deposits.
			if building is None or building.id == BUILDINGS.FISH_DEPOSIT:
				continue

			# Assign the entire building to the first settlement that covers some of it.
			assert building.settlement is None or building.settlement is settlement
			for building_coords in building.position.tuple_iter():
				building_tile = self.ground_map[building_coords]
				if building_tile.settlement is not settlement:
					assert building_tile.settlement is None
					building_tile.settlement = settlement
					settlement.ground_map[building_coords] = building_tile
					settlement_coords_changed.append(building_coords)

			building.settlement = settlement
			building.owner = settlement.owner
			settlement.add_building(building)

		if not settlement_coords_changed:
			return

		flat_land_set = self.terrain_cache.cache[TerrainRequirement.LAND][(1, 1)]
		settlement_tiles_changed = []
		for coords in settlement_coords_changed:
			settlement_tiles_changed.append(self.ground_map[coords])
			if coords in flat_land_set:
				self.available_flat_land -= 1
		Minimap.update(None)
		self.available_land_cache.remove_area(settlement_coords_changed)

		self._register_change()
		if self.terrain_cache:
			settlement.buildability_cache.modify_area(settlement_coords_changed)

		SettlementRangeChanged.broadcast(settlement, settlement_tiles_changed)

	def abandon_buildings(self, buildings_list):
		"""Abandon all buildings in the list
		@param buildings_list: buildings to abandon
		"""
		for building in buildings_list:
			Tear(building)(building.owner)

	def remove_settlement(self, building):
		"""Removes the settlement property from tiles within the radius of the given building"""
		settlement = building.settlement
		buildings_to_abandon, settlement_coords_to_change = Tear.additional_removals_after_tear(building)
		assert building not in buildings_to_abandon
		self.abandon_buildings(buildings_to_abandon)

		flat_land_set = self.terrain_cache.cache[TerrainRequirement.LAND][(1, 1)]
		land_or_coast = self.terrain_cache.land_or_coast
		settlement_tiles_changed = []
		clean_coords = set()
		for coords in settlement_coords_to_change:
			tile = self.ground_map[coords]
			tile.settlement = None
			building = tile.object
			if building is not None:
				settlement.remove_building(building)
				building.owner = None
				building.settlement = None
			if coords in land_or_coast:
				clean_coords.add(coords)
			settlement_tiles_changed.append(self.ground_map[coords])
			del settlement.ground_map[coords]
			if coords in flat_land_set:
				self.available_flat_land += 1
		Minimap.update(None)
		self.available_land_cache.add_area(clean_coords)

		self._register_change()
		if self.terrain_cache:
			settlement.buildability_cache.modify_area(clean_coords)

		SettlementRangeChanged.broadcast(settlement, settlement_tiles_changed)

	def add_building(self, building, player, load=False):
		"""Adds a building to the island at the position x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement
		@param load: boolean, whether it has been called during loading"""
		if building.id in (BUILDINGS.CLAY_DEPOSIT, BUILDINGS.STONE_DEPOSIT, BUILDINGS.MOUNTAIN) and self.available_land_cache is not None:
			# self.available_land_cache may be None when loading a settlement
			# it is ok to skip in that case because the cache's constructor will take the deposits into account anyway
			self.deposits[building.id][building.position.origin.to_tuple()] = building
			self.available_land_cache.remove_area(list(building.position.tuple_iter()))
		super().add_building(building, player, load=load)
		if not load and building.settlement is not None:
			# Note: (In case we do not require all building tiles to lay inside settlement
			# range at some point.) `include_self` is True in get_radius_coordinates()
			# called from here, so the building area itself *is* expanded by even with
			# radius=0! Right now this has no effect (above buildability requirements).
			radius = 0 if building.id not in BUILDINGS.EXPAND_RANGE else building.radius
			self.assign_settlement(building.position, radius, building.settlement)

		if building.settlement is not None:
			building.settlement.add_building(building, load)
		if building.id in self.building_indexers:
			self.building_indexers[building.id].add(building)

		# Reset the tiles this building was covering
		for coords in building.position.tuple_iter():
			self.path_nodes.reset_tile_walkability(coords)
		if not load:
			self._register_change()

		# keep track of the number of trees for animal population control
		if building.id == BUILDINGS.TREE:
			self.num_trees += 1

		return building

	def remove_building(self, building):
		# removal code (before super call)
		if building.id in (BUILDINGS.CLAY_DEPOSIT, BUILDINGS.STONE_DEPOSIT, BUILDINGS.MOUNTAIN):
			coords = building.position.origin.to_tuple()
			if coords in self.deposits[building.id]:
				del self.deposits[building.id][coords]
		settlement = building.settlement
		if settlement is not None:
			if building.id in BUILDINGS.EXPAND_RANGE:
				self.remove_settlement(building)
			settlement.remove_building(building)
			assert building not in settlement.buildings

		super().remove_building(building)
		if building.id in self.building_indexers:
			self.building_indexers[building.id].remove(building)

		# Reset the tiles this building was covering (after building has been completely removed)
		for coords in building.position.tuple_iter():
			self.path_nodes.reset_tile_walkability(coords)
			self._register_change()

		# keep track of the number of trees for animal population control
		if building.id == BUILDINGS.TREE:
			self.num_trees -= 1

	def get_building_index(self, resource_id):
		if resource_id == RES.WILDANIMALFOOD:
			return self.building_indexers[BUILDINGS.TREE]
		return None

	def get_surrounding_tiles(self, where, radius=1, include_corners=True):
		"""Returns tiles around point with specified radius.
		@param where: instance of Point, or object with get_surrounding()"""
		if hasattr(where, "get_surrounding"):
			coords = where.get_surrounding(include_corners=include_corners)
		else: # assume Point
			coords = Circle(where, radius).tuple_iter()
		for position in coords:
			tile = self.get_tile_tuple(position)
			if tile is not None:
				yield tile

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

	def __iter__(self):
		return iter(self.ground_map.keys())

	def check_wild_animal_population(self):
		"""Creates a wild animal if they died out."""
		self.log.debug("Checking wild animal population: %s", len(self.wild_animals))
		if self.wild_animals:
			# Some animals still alive, nothing to revive.
			return

		# Find a tree where we can place a new animal.
		# We might not find a tree at all, but if that's the case,
		# wild animals would die out again anyway, so we do nothing.
		for building in self.buildings:
			if building.id == BUILDINGS.TREE:
				point = building.position.origin
				entity = Entities.units[UNITS.WILD_ANIMAL]
				animal = entity(self, x=point.x, y=point.y, session=self.session)
				animal.initialize()
				return

	def _init_cache(self):
		""" initializes the cache that knows when the last time the buildability of a rectangle may have changed on this island """
		self.last_change_id = -1

	def _register_change(self):
		""" registers the possible buildability change of a rectangle on this island """
		self.last_change_id += 1

	def end(self):
		# NOTE: killing animals before buildings is an optimization, else they would
		# keep searching for new trees every time a tree is torn down.
		for wild_animal in (wild_animal for wild_animal in self.wild_animals):
			wild_animal.remove()
		super().end()
		for settlement in self.settlements:
			settlement.end()
		self.wild_animals = None
		self.ground_map = None
		self.path_nodes = None
		self.barrier_nodes = None
		self.building_indexers = None
