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

import logging

from horizons.entities import Entities
from horizons.scheduler import Scheduler

from horizons.util import WorldObject, Point, Rect, Circle, DbReader, random_map, BuildingIndexer
from horizons.messaging import SettlementRangeChanged, NewSettlement
from settlement import Settlement
from horizons.util.pathfinding.pathnodes import IslandPathNodes
from horizons.constants import BUILDINGS, RES, UNITS
from horizons.scenario import CONDITIONS
from horizons.world.buildingowner import BuildingOwner
from horizons.gui.widgets.minimap import Minimap

class Island(BuildingOwner, WorldObject):
	"""The Island class represents an island. It contains a list of all things on the map
	that belong to the island. This comprises ground tiles as well as buildings,
	nature objects (which are buildings) and units.
	All those objects also have a reference to the island, making it easy to determine to which island the instance belongs.
	An Island instance is created during map creation, when all tiles are added to the map.
	@param origin: Point instance - Position of the (0, 0) ground tile.
	@param filename: file from which the island is loaded.

	Each island holds some important attributes:
	* grounds - All ground tiles that belong to the island are referenced here.
	* grounds_map -  a dictionary that binds tuples of coordinates with a reference to the tile:
	                  { (x, y): tileref, ...}
					  This is important for pathfinding and quick tile fetching.
	* position - a Rect that borders the island with the smallest possible area
	* buildings - a list of all Building instances that are present on the island.
	* settlements - a list of all Settlement instances that are present on the island.
	* path_nodes - a special dictionary used by the pather to save paths.

	TUTORIAL:
	Why do we use a separate __init() function, and do not use the __init__() function?
	Simple, if we load the game, the class is not loaded as new instance, so the __init__
	function is not called. Rather the load function is called. So everything that new
	classes and loaded classes share to initialize, comes into the __init() function.
	This is the common way of doing this in Unknown Horizons, so better get used to it :)
	NOTE: The components work a bit different, but this code here is mostly not component oriented.

	To continue hacking, check out the __init() function now.
	"""
	log = logging.getLogger("world.island")

	def __init__(self, db, islandid, session, preview=False):
		"""
		@param db: db instance with island table
		@param islandid: id of island in that table
		@param session: reference to Session instance
		@param preview: flag, map preview mode
		"""
		super(Island, self).__init__(worldid=islandid)

		if False:
			from horizons.session import Session
			assert isinstance(session, Session)
		self.session = session

		x, y, filename = db("SELECT x, y, file FROM island WHERE rowid = ? - 1000", islandid)[0]
		self.__init(Point(x, y), filename, preview=preview)

		if not preview:
			# create building indexers
			from horizons.world.units.animal import WildAnimal
			self.building_indexers = {}
			self.building_indexers[BUILDINGS.TREE] = BuildingIndexer(WildAnimal.walking_range, self, self.session.random)

		# load settlements
		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", islandid):
			settlement = Settlement.load(db, settlement_id, self.session, self)
			self.settlements.append(settlement)

		if not preview:
			# load buildings
			from horizons.world import load_building
			for (building_worldid, building_typeid) in \
				  db("SELECT rowid, type FROM building WHERE location = ?", islandid):
				load_building(self.session, db, building_typeid, building_worldid)

	def _get_island_db(self):
		# check if filename is a random map
		if random_map.is_random_island_id_string(self.file):
			# it's a random map id, create this map and load it
			return random_map.create_random_island(self.file)
		return DbReader(self.file) # Create a new DbReader instance to load the maps file.

	def __init(self, origin, filename, preview=False):
		"""
		Load the actual island from a file
		@param origin: Point
		@param filename: String, filename of island db or random map id
		@param preview: flag, map preview mode
		"""
		self.file = filename
		self.origin = origin
		db = self._get_island_db()

		p_x, p_y, width, height = db("SELECT (MIN(x) + ?), (MIN(y) + ?), (1 + MAX(x) - MIN(x)), (1 + MAX(y) - MIN(y)) FROM ground", self.origin.x, self.origin.y)[0]

		# rect for quick checking if a tile isn't on this island
		# NOTE: it contains tiles, that are not on the island!
		self.rect = Rect(Point(p_x, p_y), width, height)

		self.ground_map = {}
		for (rel_x, rel_y, ground_id, action_id, rotation) in db("SELECT x, y, ground_id, action_id, rotation FROM ground"): # Load grounds
			if not preview: # actual game, need actual tiles
				ground = Entities.grounds[ground_id](self.session, self.origin.x + rel_x, self.origin.y + rel_y)
				ground.act(action_id, rotation)
			else:
				ground = Point(self.origin.x + rel_x, self.origin.y + rel_y)
				ground.classes = tuple()
				ground.settlement = None
			# These are important for pathfinding and building to check if the ground tile
			# is blocked in any way.
			self.ground_map[(ground.x, ground.y)] = ground

		self._init_cache()

		self.settlements = []
		self.wild_animals = []
		self.num_trees = 0

		# define the rectangle with the smallest area that contains every island tile its position
		min_x = min(zip(*self.ground_map.keys())[0])
		max_x = max(zip(*self.ground_map.keys())[0])
		min_y = min(zip(*self.ground_map.keys())[1])
		max_y = max(zip(*self.ground_map.keys())[1])
		self.position = Rect.init_from_borders(min_x, min_y, max_x, max_y)

		if not preview: # this isn't needed for previews, but it is in actual games
			self.path_nodes = IslandPathNodes(self)

			# repopulate wild animals every 2 mins if they die out.
			Scheduler().add_new_object(self.check_wild_animal_population, self, Scheduler().get_ticks(120), -1)

		"""TUTORIAL:
		The next step will be an overview of the component system, which you will need
		to understand in order to see how our actual game object (buildings, units) work. Please proceed to horizons/world/componentholder.py
		"""

	def save(self, db):
		super(Island, self).save(db)
		db("INSERT INTO island (rowid, x, y, file) VALUES (? - 1000, ?, ?, ?)",
			self.worldid, self.origin.x, self.origin.y, self.file)
		for settlement in self.settlements:
			settlement.save(db, self.worldid)
		for animal in self.wild_animals:
			animal.save(db)

	def save_map(self, db):
		"""Saves the ground into the given database (used for saving maps, not saved games)."""
		db('CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL, action_id TEXT NOT NULL, rotation INTEGER NOT NULL)')
		db('CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)')
		source_db = self._get_island_db()
		db('BEGIN')
		db.execute_many('INSERT INTO ground VALUES(?, ?, ?, ?, ?)', source_db('SELECT x, y, ground_id, action_id, rotation FROM ground'))
		db('COMMIT')

	def get_coordinates(self):
		"""Returns list of coordinates, that are on the island."""
		return self.ground_map.keys()

	def get_tile(self, point):
		"""Returns whether a tile is on island or not.
		@param point: Point contains position of the tile.
		@return: tile instance if tile is on island, else None."""
		try:
			return self.ground_map[(point.x, point.y)]
		except KeyError:
			return None

	def get_tile_tuple(self, tup):
		"""Overloaded get_tile, takes a tuple as argument"""
		try:
			return self.ground_map[tup]
		except KeyError:
			return None

	def get_tiles_tuple(self, tuples):
		"""Same as get_tile, but takes a list of tuples.
		@param tuples: iterable of tuples
		@return: list of tiles"""
		for tup in tuples:
			if tup in self.ground_map:
				yield self.ground_map[tup]

	def add_settlement(self, position, radius, player, load=False):
		"""Adds a settlement to the island at the position x, y with radius as area of influence.
		@param position: Rect describing the position of the new warehouse
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(self.session, player)
		settlement.initialize()
		self.add_existing_settlement(position, radius, settlement, load)
		# TODO: Move this to command, this message should not appear while loading
		self.session.ingame_gui.message_widget.add(position.center().x, \
		                                           position.center().y, \
		                                           'NEW_SETTLEMENT', \
		                                           {'player':player.name}, \
		                                           self.session.world.player == player)

		NewSettlement.broadcast(self, settlement)

		return settlement

	def add_existing_settlement(self, position, radius, settlement, load=False):
		"""Same as add_settlement, but uses settlement from parameter.
		May also be called for extension of an existing settlement by a new building. (this
		is useful for loading, where every loaded building extends the radius of its settlement).
		@param position: Rect
		@param load: whether it has been called during load"""
		if settlement not in self.settlements:
			self.settlements.append(settlement)
		if not load:
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
		settlement_tiles_changed = []
		for coord in position.get_radius_coordinates(radius, include_self=True):
			tile = self.get_tile_tuple(coord)
			if tile is not None:
				if tile.settlement == settlement:
					continue
				if tile.settlement is None:
					tile.settlement = settlement
					settlement.ground_map[coord] = tile
					Minimap.update(coord)
					self._register_change(coord[0], coord[1])
					settlement_tiles_changed.append(tile)

					# notify all AI players when land ownership changes
					for player in self.session.world.players:
						if hasattr(player, 'on_settlement_expansion'):
							player.on_settlement_expansion(settlement, coord)

				building = tile.object
				# found a new building, that is now in settlement radius
				# assign buildings on tiles to settlement
				if building is not None and building.settlement is None and \
				   building.island == self: # don't steal from other islands
					building.settlement = settlement
					building.owner = settlement.owner
					settlement.add_building(building)

		if settlement_tiles_changed:
			SettlementRangeChanged.broadcast(settlement, settlement_tiles_changed)


	def add_building(self, building, player, load=False):
		"""Adds a building to the island at the position x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement
		@param load: boolean, whether it has been called during loading"""
		building = super(Island, self).add_building(building, player, load=load)
		if not load:
			for building.settlement in self.get_settlements(building.position, player):
				self.assign_settlement(building.position, building.radius, building.settlement)
				break

		if building.settlement is not None:
			building.settlement.add_building(building)
		if building.id in self.building_indexers:
			self.building_indexers[building.id].add(building)

		# Reset the tiles this building was covering
		for point in building.position:
			self.path_nodes.reset_tile_walkability(point.to_tuple())
			if not load:
				self._register_change(point.x, point.y)

		# keep track of the number of trees for animal population control
		if building.id == BUILDINGS.TREE:
			self.num_trees += 1

		return building

	def remove_building(self, building):
		# removal code (before super call)
		if building.settlement is not None:
			building.settlement.remove_building(building)
			assert(building not in building.settlement.buildings)

		super(Island, self).remove_building(building)
		if building.id in self.building_indexers:
			self.building_indexers[building.id].remove(building)

		# Reset the tiles this building was covering (after building has been completely removed)
		for point in building.position:
			self.path_nodes.reset_tile_walkability(point.to_tuple())
			self._register_change(point.x, point.y)

		# keep track of the number of trees for animal population control
		if building.id == BUILDINGS.TREE:
			self.num_trees -= 1

	def get_building_index(self, resource_id):
		if resource_id == RES.WILDANIMALFOOD:
			return self.building_indexers[BUILDINGS.TREE]
		return None

	def get_surrounding_tiles(self, where, radius = 1):
		"""Returns tiles around point with specified radius.
		@param point: instance of Point, or object with get_surrounding()"""
		if hasattr(where, "get_surrounding"):
			coords = where.get_surrounding(include_corners=False)
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
		return self.ground_map.iterkeys()

	def check_wild_animal_population(self):
		"""Creates a wild animal if they died out."""
		self.log.debug("Checking wild animal population: %s", len(self.wild_animals))
		if len(self.wild_animals) == 0:
			# find a tree where we can place it
			for building in self.buildings:
				if building.id == BUILDINGS.TREE:
					point = building.position.origin
					animal = Entities.units[UNITS.WILD_ANIMAL](self, x=point.x, y=point.y, session=self.session)
					animal.initialize()
					return
		# we might not find a tree, but if that's the case, wild animals would die out anyway again,
		# so do nothing in this case.

	def _init_cache(self):
		""" initialises the cache that knows when the last time the buildability of a rectangle may have changed on this island """
		self.last_change_id = -1

		def calc_cache(size_x, size_y):
			d = {}
			for (x, y) in self.ground_map:
				all_on_island = True
				for dx in xrange(size_x):
					for dy in xrange(size_y):
						if (x + dx, y + dy) not in self.ground_map:
							all_on_island = False
							break
					if not all_on_island:
						break
				if all_on_island:
					d[ (x, y) ] = self.last_change_id
			return d

		class LazyDict(dict):
			def __getitem__(self, x):
				try:
					return super(LazyDict, self).__getitem__(x)
				except KeyError:
					val = self[x] = calc_cache(*x)
					return val

		self.last_changed = LazyDict()

	def _register_change(self, x, y):
		""" registers the possible buildability change of a rectangle on this island """
		self.last_change_id += 1
		for (area_size_x, area_size_y), building_areas in self.last_changed.iteritems():
			for dx in xrange(area_size_x):
				for dy in xrange(area_size_y):
					coords = (x - dx, y - dy)
					# building area with origin at coords affected
					if coords in building_areas:
						building_areas[coords] = self.last_change_id

	def end(self):
		# NOTE: killing animals before buildings is an optimisation, else they would
		# keep searching for new trees every time a tree is torn down.
		for wild_animal in (wild_animal for wild_animal in self.wild_animals):
			wild_animal.remove()
		super(Island, self).end()
		for settlement in self.settlements:
			settlement.end()
		self.wild_animals = None
		self.ground_map = None
		self.path_nodes = None
		self.building_indexers = None
