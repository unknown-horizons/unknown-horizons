# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

import weakref
import logging
import re

from horizons.entities import Entities
from horizons.scheduler import Scheduler

from horizons.util import WorldObject, Point, Rect, Circle, WeakList, DbReader, decorators, random_map
from settlement import Settlement
from horizons.world.pathfinding.pathnodes import IslandPathNodes
from horizons.constants import BUILDINGS, UNITS
from horizons.campaign import CONDITIONS
from horizons.world.buildingowner import BuildingOwner

class Island(BuildingOwner, WorldObject):
	"""The Island class represents an Island by keeping a list of all instances on the map,
	that belong to the island. The island variable is also set on every instance that belongs
	to an island, making it easy to determine to which island the instance belongs, when
	selected.
	An Island instance is created at map creation, when all tiles are added to the map.
	@param origin: Point instance - Position of the (0, 0) ground tile.
	@param filename: file from which the island is loaded.

	Each island holds some important attributes:
	* grounds - All grounds that belong to the island are referenced here.
	* grounds_map -  a dictionary that binds tuples of coordinates with a reference to the tile:
	                  { (x, y): tileref, ...}
					  This is important for pathfinding and quick tile fetching.
	* buildings - a list of all Building instances that are present on the island.
	* settlements - a list of all Settlement instances that are present on the island.
	* path_nodes - a special dictionary used by the pather to save paths.

	TUTORIAL:
	Why do we use a separate __init() function, and do not use the __init__() function?
	Simple, if we load the game, the class is not loaded as new instance, so the __init__
	function is not called. Rather the load function is called. So everything that new
	classes and loaded classes share to initialize, comes into the __init() function.
	This is the common way of doing this in Unknown Horizons, so better get used to it :)

	To continue hacking, check out the __init() function now.
	"""
	log = logging.getLogger("world.island")

	def __init__(self, db, islandid, session):
		"""
		@param db: db instance with island table
		@param islandid: id of island in that table
		@param session: reference to Session instance
		"""
		super(Island, self).__init__(worldid=islandid)
		self.session = session

		x, y, filename = db("SELECT x, y, file FROM island WHERE rowid = ? - 1000", islandid)[0]
		self.__init(Point(x, y), filename)

		# load settlements
		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", islandid):
			Settlement.load(db, settlement_id, self.session)

		# load buildings
		from horizons.world import load_building
		for (building_worldid, building_typeid) in \
		    db("SELECT rowid, type FROM building WHERE location = ?", islandid):
			load_building(self.session, db, building_typeid, building_worldid)

	def __init(self, origin, filename):
		"""
		Load the actual island from a file
		@param origin: Point
		@param filename: String, filename of island db or random map id
		"""
		self.file = filename
		self.origin = origin

		# check if filename is a random map
		if random_map.is_random_island_id_string(filename):
			# it's a random map id, create this map and load it
			db = random_map.create_random_island(filename)
		else:
			db = DbReader(filename) # Create a new DbReader instance to load the maps file.

		p_x, p_y, width, height = db("SELECT (MIN(x) + ?), (MIN(y) + ?), (1 + MAX(x) - MIN(x)), (1 + MAX(y) - MIN(y)) FROM ground", self.origin.x, self.origin.y)[0]

		# rect for quick checking if a tile isn't on this island
		# NOTE: it contains tiles, that are not on the island!
		self.rect = Rect(Point(p_x, p_y), width, height)

		self.ground_map = {}
		for (rel_x, rel_y, ground_id) in db("SELECT x, y, ground_id FROM ground"): # Load grounds
			ground = Entities.grounds[ground_id](self.session, self.origin.x + rel_x, self.origin.y + rel_y)
			# These are important for pathfinding and building to check if the ground tile
			# is blocked in any way.
			self.ground_map[(ground.x, ground.y)] = ground

		self.settlements = []
		self.wild_animals = []

		self.path_nodes = IslandPathNodes(self)

		# repopulate wild animals every 2 mins if they die out.
		Scheduler().add_new_object(self.check_wild_animal_population, self, Scheduler().get_ticks(120), -1)

		"""TUTORIAL:
		To continue hacking, you should now take off to the real fun stuff and check out horizons/world/building/__init__.py.
		"""

	def save(self, db):
		super(Island, self).save(db)
		db("INSERT INTO island (rowid, x, y, file) VALUES (? - 1000, ?, ?, ?)",
			self.worldid, self.origin.x, self.origin.y, self.file)
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

	def get_building(self, point):
		"""Returns the building at the point
		@param point: position of the tile to look on
		@return: Building class instance or None if none is found.
		"""
		try:
			return self.ground_map[point.to_tuple()].object
		except KeyError:
			return None

	def get_settlement(self, point):
		"""Look for a settlement on a specific tile
		@param point: Point to look on
		@return: Settlement at point, or None"""
		try:
			return self.get_tile(point).settlement
			# some tiles might be none, so we have to catch that error here
		except AttributeError:
			return None

	def get_settlements(self, rect, player = None):
		"""Returns the list of settlements for the coordinates describing a rect.
		@param rect: Area to search for settlements
		@return: list of Settlement instances at that position."""
		settlements = set()
		if self.rect.intersects(rect):
			for point in rect:
				try:
					if player is None or self.get_tile(point).settlement.owner == player:
						settlements.add( self.get_tile(point).settlement )
				except AttributeError:
					# some tiles don't have settlements, we don't explicitly check for them cause
					# its faster this way.
					pass
			settlements.discard(None) # None values might have been added, we don't want them
		return list(settlements)

	def add_settlement(self, position, radius, player):
		"""Adds a settlement to the island at the position x, y with radius as area of influence.
		@param position: Rect describing the position of the new branch office
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(self.session, player)
		self.add_existing_settlement(position, radius, settlement)
		# TODO: Move this to command, this message should not appear while loading
		self.session.ingame_gui.message_widget.add(position.center().x, \
		                                           position.center().y, \
		                                           'NEW_SETTLEMENT', \
		                                           {'player':player.name}, \
		                                           self.session.world.player == player)

		self.session.world.notify_new_settlement()

		return settlement

	def add_existing_settlement(self, position, radius, settlement):
		"""Same as add_settlement, but uses settlement from parameter.
		May also be called for extension of an existing settlement by a new building. (this
		is useful for loading, where every loaded building extends the radius of its settlement).
		@param position: Rect"""
		if settlement not in self.settlements:
			self.settlements.append(settlement)
		self.assign_settlement(position, radius, settlement)
		self.session.campaign_eventhandler.check_events(CONDITIONS.settlements_num_greater)
		return settlement

	def assign_settlement(self, position, radius, settlement):
		"""Assigns the settlement property to tiles within the circle defined by \
		position and radius.
		@param position: Rect
		@param radius:
		@param settlement:
		"""
		for coord in position.get_radius_coordinates(radius, include_self=True):
			tile = self.get_tile_tuple(coord)
			if tile is not None:
				if tile.settlement == settlement:
					continue
				if tile.settlement is None:
					tile.settlement = settlement
					settlement.ground_map[coord] = tile
					self.session.ingame_gui.minimap.update(coord)

				building = tile.object
				# assign buildings on tiles to settlement
				if building is not None and building.settlement is None and \
				   building.island == self: # don't steal from other islands
					building.settlement = settlement
					building.owner = settlement.owner
					settlement.add_building(building)

		#TODO: inherit resources etc


	def add_building(self, building, player):
		"""Adds a building to the island at the position x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		building = super(Island, self).add_building(building, player)
		for building.settlement in self.get_settlements(building.position, player):
			self.assign_settlement(building.position, building.radius, building.settlement)
			break

		if building.settlement is not None:
			building.settlement.add_building(building)
		building.init()
		return building

	def remove_building(self, building):
		if building.settlement is not None:
			building.settlement.remove_building(building)
			assert(building not in building.settlement.buildings)

		# Reset the tiles this building was covering
		for point in building.position:
			self.path_nodes.reset_tile_walkability(point.to_tuple())
		super(Island, self).remove_building(building)

	def get_surrounding_tiles(self, point, radius = 1):
		"""Returns tiles around point with specified radius.
		@param point: instance of Point"""
		for position in Circle(point, radius):
			tile = self.get_tile(position)
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
		for i in self.get_coordinates():
			yield i

	def check_wild_animal_population(self):
		"""Creates a wild animal if they died out."""
		self.log.debug("Checking wild animal population: %s", len(self.wild_animals))
		if len(self.wild_animals) == 0:
			# find a tree where we can place it
			for building in self.buildings:
				if building.id == BUILDINGS.TREE_CLASS:
					point = building.position.origin
					Entities.units[UNITS.WILD_ANIMAL_CLASS](self, x=point.x, y=point.y, session=self.session)
					return
		# we might not find a tree, but if that's the case, wild animals would die out anyway again,
		# so do nothing in this case.

