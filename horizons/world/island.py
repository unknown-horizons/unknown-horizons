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

import weakref
import logging

import horizons.main

from horizons.dbreader import DbReader
from horizons.util import WorldObject, Point, Rect, Circle
from settlement import Settlement

class Island(WorldObject):
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
	                  { (x,y): tileref, ...}
					  This is important for pathfinding and quick tile fetching.
	* buildings - a list of all Building instances that are present on the island.
	* settlements - a list of all Settlement instances that are present on the island.
	* path_nodes - a special dictionary used by the pather to save paths.

	TUTORIAL:
	Why do we use a seperate __init() function, and do not use the __init__() function?
	Simple, if we load the game, the class is not loaded as new instance, so the __init__
	function is not called. Rather the load function is called. So everything that new
	classes and loaded classes share to initialize, comes into the __init() function.
	This is the common way of doing this in Unknown Horizons, so better get used to it :)

	To continue hacking, check out the __init() function now.
	"""
	log = logging.getLogger("world.island")

	def __init__(self, origin, filename):
		self.__init(origin, filename)

	def __init(self, origin, filename):
		"""
		@param origin: Point
		@param filename: String
		"""
		self.file = filename
		self.origin = origin
		db = DbReader(filename) # Create a new DbReader instance to load the maps file.
		p_x, p_y, width, height = db("select (min(x) + ?), (min(y) + ?), (1 + max(x) - min(x)), (1 + max(y) - min(y)) from ground", self.origin.x, self.origin.y)[0]
		self.rect = Rect(Point(p_x, p_y), width, height)
		self.grounds = []
		self.ground_map = {}
		self.buildings = []
		self.wild_animals = []
		for (rel_x, rel_y, ground_id) in db("select x, y, ground_id from ground"): # Load grounds
			ground = horizons.main.session.entities.grounds[ground_id](self.origin.x + rel_x, self.origin.y + rel_y)
			# Each ground has a set of attributes:
			ground.settlement = None
			ground.blocked = False
			ground.object = None
			# These are important for pathfinding and building to check if the ground tile is blocked in any way.
			self.grounds.append(ground)
			self.ground_map[(ground.x, ground.y)] = weakref.ref(ground)

		#self.a = False
		# generate list of walkable tiles
		self.walkable_tiles = []
		for i in self.get_coordinates():
			if self.is_walkable(i, False):
				self.walkable_tiles.append(i)

		#self.a = True
		self.settlements = [] # List of settlements

		self.path_nodes = {} # Paths are saved here for usage by the pather.
		"""TUTORIAL:
		To continue hacking, you should now take of to the real fun stuff and check out horizons/world/building/__init__.py.
		"""

	def save(self, db):
		db("INSERT INTO island (rowid, x, y, file) VALUES (?, ?, ?, ?)",
			self.getId(), self.origin.x, self.origin.y, self.file)
		for building in self.buildings:
			building.save(db)
		for settlement in self.settlements:
			settlement.save(db, self.getId())

	def load(self, db, worldid):
		super(Island, self).load(db, worldid)

		x, y, filename = db("SELECT x, y, file FROM island WHERE rowid = ?", worldid)[0]
		self.__init(Point(x, y), filename)

		horizons.main.session.world.islands.append(self)

		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", worldid):
			settlement = Settlement.load(db, settlement_id)

		for (building_worldid, building_typeid) in \
			db("SELECT rowid, type FROM building WHERE location = ?", worldid):

			buildingclass = horizons.main.session.entities.buildings[building_typeid]
			building = buildingclass.load(db, building_worldid)

	def get_coordinates(self):
		"""Returns list of coordinates, that are on the island."""
		return self.ground_map.keys()

	def get_walkable_coordinates(self):
		"""Get list of tiles, which are acctually walkable right now."""
		return self.walkable_tiles

	def get_tile(self, point):
		"""Returns whether a tile is on island or not.
		@param point: Point containt position of the tile.
		@return: tile instance if tile is on island, else None."""
		# this creates too much output, uncomment if you need this message:
		#if horizons.main.debug: print "Island get_tile"
		if not self.rect.contains(point):
			return None
		try:
			return self.ground_map[(point.x, point.y)]()
		except KeyError:
			return None

	def get_building(self, point):
		"""Returns the building at the point
		@param point: position of the tile to look on
		@return: Building class instance or None if none is found.
		"""
		if not self.rect.contains(point):
			return None
		settlement = self.get_settlement(point)
		if settlement:
			return settlement.get_building(point)
		else:
			for building in self.buildings:
				if building.position.contains(point):
					return building
		return None

	def get_settlement(self, point):
		"""Look for a settlement on a specific tile
		@param point: Point to look on
		@return: Settlement at point, or None"""
		settlements = self.get_settlements(Rect(point, 1, 1))
		if len(settlements)>0:
			assert len(settlements) == 1
			return settlements[0]
		return None

	def get_settlements(self, rect):
		"""Returns the list of settlements for the coordinates describing a rect.
		@param rect: Area to search for settlements
		@return: list of Settlement instances at that position."""
		settlements = []
		if self.rect.intersects(rect):
			for x,y in rect.get_coordinates():
				tile = self.get_tile(Point(x,y))
				if tile is not None and tile.settlement is not None and tile.settlement not in settlements:
					settlements.append(tile.settlement)
			#for tile in self.grounds:
			#	if rect.contains(tile) and tile.settlement is not None and tile.settlement not in settlements:
			#		settlements.append(tile.settlement)
		return settlements

	def add_settlement(self, position, radius, player):
		"""Adds a settlement to the island at the posititon x, y with radius as area of influence.
		@param position: Rect describing the position of the new branch office
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(player)
		self.add_existing_settlement(position, radius, settlement)
		# TODO: Move this to command, this message should not appear while loading
		horizons.main.session.ingame_gui.message_widget.add(position.center().x, position.center().y, 1, {'player':player.name})
		return settlement

	def add_existing_settlement(self, position, radius, settlement):
		"""Same as add_settlement, but uses settlement from parameter.
		May also be called for extension of an existing settlement by a new building. (this
		is useful for loading, where every loaded buiding extends the radius of its settlement) """
		if settlement not in self.settlements:
			self.settlements.append(settlement)
		self.assign_settlement(position, radius, settlement)
		return settlement

	def assign_settlement(self, position, radius, settlement):
		"""Assigns the settlement property to tiles within the circle defined by \
		position and radius.
		@param position: Rect
		@param radius:
		@param settlement:
		"""
		for coord in position.get_radius_coordinates(radius):
			tile = self.get_tile(Point(coord[0], coord[1]))
			if tile is not None:
				if tile.settlement == settlement:
					continue
				if (tile.settlement is None) or (tile.settlement.owner == settlement.owner):
					tile.settlement = settlement
		#for tile in self.grounds: # Set settlement var for all tiles in the radius.
		#	if tile.settlement == settlement:
		#		continue
			## TODO: make this readable
			##       check if it's faster to calcuate the coords in radius and use
			##       settlement.get_tile() on large maps
			#if (max(position.left - tile.x, 0, tile.x - position.right) ** 2) + \
			#   (max(position.top - tile.y, 0, tile.y - position.bottom) ** 2) <= radius ** 2:
			#	if (tile.settlement is None) or (tile.settlement.owner == settlement.owner):
			#		tile.settlement = settlement
		for building in self.buildings: # Check if any buildings come into range, like unowned trees
			if (max(position.left - building.position.center().x, 0, building.position.center().x - position.right) ** 2) + \
			   (max(position.top - building.position.center().y, 0, building.position.center().y - position.bottom) ** 2) <= radius ** 2:
				if building.settlement is None:
					building.settlement = settlement
					settlement.buildings.append(building)
				elif building.settlement.owner == settlement.owner:
					building.settlement = settlement
		#TODO: inherit resources etc

	def add_building(self, building, player):
		"""Adds a building to the island at the posititon x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		# the lines that are commented out, were moved to UnselectableBuilding.__init__()
		#building.island = self
		for building.settlement in self.get_settlements(building.position):
			self.assign_settlement(building.position, building.radius, building.settlement)
			break
		#else:
		#	building.settlement = self.add_settlement(x, y, x + building.size[0] - 1, y + building.size[1] - 1, building.radius, player)

		x, y = building.position.left, building.position.top
		for xx in xrange(x, x + building.size[0]):
			for yy in xrange(y, y + building.size[1]):
				tile = self.get_tile(Point(xx, yy))
				tile.blocked = True # Set tile blocked
				tile.object = building # Set tile's object to the building
				self.reset_tile_walkability((xx, yy))
		self.buildings.append(building)
		if building.settlement is not None:
			building.settlement.buildings.append(building)
		building.init()
		building.start()
		#print "New building created at (%i:%i) for player '%s' and settlement '%s'" % (x, y, player.name, building.settlement.name)
		return building

	def remove_building(self, building):
		assert (building.island() == self)

		# Reset the tiles this building was covering
		for point in building.position:
			tile = self.get_tile(point)
			tile.blocked = False
			tile.object = None
			self.reset_tile_walkability(point.to_tuple())

		if building.settlement is not None:
			building.settlement.buildings.remove(building)
			assert(building not in building.settlement.buildings)

		# Remove this building from the buildings list
		self.buildings.remove(building)
		assert building not in self.buildings

	def registerPath(self, path):
		"""Tell the island that there is a new street, where street-walkers can move on"""
		origin = path.position.origin
		# TODO: currently all paths have speed 1, since we don't have a real velocity-system yet.
		#       this value here is only used for pathfinding.
		self.path_nodes[ (origin.x, origin.y) ] = 1

	def unregisterPath(self, path):
		"""Opposite of registerPath"""
		origin = path.position.origin
		del self.path_nodes[ (origin.x, origin.y) ]

	def get_surrounding_tiles(self, point, radius = 1):
		"""Returns tiles arround point with specified radius
		@param point: instance of Point"""
		tiles = []
		for position in Circle(point, radius).get_coordinates():
			tile = self.get_tile(Point(*position))
			if tile is not None:
				tiles.append(tile)
		return tiles

	def is_walkable(self, coord, check_coord_is_on_island = True):
		"""Check if a unit make walk on the tile specified by coord
		@param coord: tuple: (x,y)
		@param check_coord_is_on_island: bool, wether to check if coord is on this island
		"""
		#if self.a:self.log.debug("is_walkable 0")
		if check_coord_is_on_island:
			if not coord in self.get_coordinates():
				return False

		#if self.a:self.log.debug("is_walkable 1")
		tile_object = self.ground_map[coord]()
		# if it's not constructible, it is usually also not walkable
		# NOTE: this isn't really a clean implementation, but it works for now
		# it eliminates e.g. water and beaches, that shouldn't be walked on
		if not "constructible" in tile_object.classes:
			return False
		#if self.a:self.log.debug("is_walkable 2")
		if tile_object.blocked:
			return False
		#if self.a:self.log.debug("is_walkable 3")
		return True

	def reset_tile_walkability(self, coord):
		"""Reset the status of the walkability of a coordinate in the list of walkable tiles
		of the island. Does not change the tile itself.
		You need to call this when a tile changes, e.g. when a building is built on it. this
		is currently done in add/remove_building
		@param coord: tuple: (x,y)"""
		self.log.debug("reset tile walkability on %s %s", coord[0], coord[1])
		acctually_walkable = self.is_walkable(coord)
		in_list = (coord in self.walkable_tiles)
		if not in_list and acctually_walkable:
			self.walkable_tiles.append(coord)
		if in_list and not acctually_walkable:
			self.walkable_tiles.remove(coord)

