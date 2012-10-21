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

from horizons.util.buildingindexer import BuildingIndexer
from horizons.util.dbreader import DbReader
from horizons.util.pathfinding.pathnodes import IslandPathNodes
from horizons.util.shapes import Circle, Point, Rect
from horizons.util.worldobject import WorldObject
from horizons.messaging import SettlementRangeChanged, NewSettlement
from horizons.world.settlement import Settlement
from horizons.constants import BUILDINGS, RES, UNITS
from horizons.scenario import CONDITIONS
from horizons.world.buildingowner import BuildingOwner
from horizons.gui.widgets.minimap import Minimap
from horizons.world.ground import MapPreviewTile

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
		super(Island, self).__init__(worldid=island_id)

		if False:
			from horizons.session import Session
			assert isinstance(session, Session)
		self.session = session

		self.__init(db, island_id, preview)

		if not preview:
			# create building indexers
			from horizons.world.units.animal import WildAnimal
			self.building_indexers = {}
			self.building_indexers[BUILDINGS.TREE] = BuildingIndexer(WildAnimal.walking_range, self, self.session.random)

		# load settlements
		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", island_id):
			settlement = Settlement.load(db, settlement_id, self.session, self)
			self.settlements.append(settlement)

		if not preview:
			# load buildings
			from horizons.world import load_building
			for (building_worldid, building_typeid) in \
				  db("SELECT rowid, type FROM building WHERE location = ?", island_id):
				load_building(self.session, db, building_typeid, building_worldid)

	def __init(self, db, island_id, preview):
		"""
		Load the actual island from a file
		@param preview: flag, map preview mode
		"""
		p_x, p_y, width, height = db("SELECT MIN(x), MIN(y), (1 + MAX(x) - MIN(x)), (1 + MAX(y) - MIN(y)) FROM ground WHERE island_id = ?", island_id - 1001)[0]

		# rect for quick checking if a tile isn't on this island
		# NOTE: it contains tiles, that are not on the island!
		self.rect = Rect(Point(p_x, p_y), width, height)

		self.ground_map = {}
		for (x, y, ground_id, action_id, rotation) in db("SELECT x, y, ground_id, action_id, rotation FROM ground WHERE island_id = ?", island_id - 1001): # Load grounds
			if not preview: # actual game, need actual tiles
				ground = Entities.grounds[ground_id](self.session, x, y)
				ground.act(action_id, rotation)
			else:
				ground = MapPreviewTile(x, y, ground_id)
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
		to understand in order to see how our actual game object (buildings, units) work.
		Please proceed to horizons/component/componentholder.py.
		"""

	def save(self, db):
		super(Island, self).save(db)
		for settlement in self.settlements:
			settlement.save(db, self.worldid)
		for animal in self.wild_animals:
			animal.save(db)

	def get_coordinates(self):
		"""Returns list of coordinates, that are on the island."""
		return self.ground_map.keys()

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
		self.session.ingame_gui.message_widget.add(string_id='NEW_SETTLEMENT',
		                                           point=position.center,
		                                           message_dict={'player':player.name},
		                                           play_sound=player.is_local_player)

		NewSettlement.broadcast(self, settlement)

		return settlement

	def add_existing_settlement(self, position, radius, settlement, load=False):
		"""Same as add_settlement, but uses settlement from parameter.
		May also be called for extension of an existing settlement by a new building (this
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

	def get_surrounding_tiles(self, where, radius=1, include_corners=True):
		"""Returns tiles around point with specified radius.
		@param point: instance of Point, or object with get_surrounding()"""
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
		return self.ground_map.iterkeys()

	def check_wild_animal_population(self):
		"""Creates a wild animal if they died out."""
		self.log.debug("Checking wild animal population: %s", len(self.wild_animals))
		if not self.wild_animals:
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
