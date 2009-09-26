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

from horizons.entities import Entities
from horizons.scheduler import Scheduler

from horizons.util import WorldObject, Point, Rect, Circle, WeakList, DbReader
from settlement import Settlement
from horizons.world.pathfinding.pathnodes import IslandPathNodes
from horizons.constants import BUILDINGS, UNITS

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
		self.session = session
		# an island is always loaded from db, so __init__() basically is load()
		super(Island, self).load(db, islandid)

		x, y, filename = db("SELECT x, y, file FROM island WHERE rowid = ?", islandid)[0]
		self.__init(Point(x, y), filename)

		# load settlements and buildings, if there are any
		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", islandid):
			Settlement.load(db, settlement_id, self.session)


		from horizons.world import load_building
		for (building_worldid, building_typeid) in \
		    db("SELECT rowid, type FROM building WHERE location = ?", islandid):
			load_building(self.session, db, building_typeid, building_worldid)

	def __init(self, origin, filename):
		"""
		Load the actual island from a file
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
		self.provider_buildings = WeakList() # list of all buildings, that are providers
		self.wild_animals = []
		for (rel_x, rel_y, ground_id) in db("select x, y, ground_id from ground"): # Load grounds
			ground = Entities.grounds[ground_id](self.session, self.origin.x + rel_x, self.origin.y + rel_y)
			# These are important for pathfinding and building to check if the ground tile
			# is blocked in any way.
			self.grounds.append(ground)
			self.ground_map[(ground.x, ground.y)] = weakref.ref(ground)

		self.settlements = [] # List of settlements

		self.path_nodes = IslandPathNodes(self)

		# repopulate wild animals every 2 mins if they die out.
		Scheduler().add_new_object(self.check_wild_animal_population, self, \
																									 16*120, -1)

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
			return self.ground_map[(point.x, point.y)]()
		except KeyError:
			return None

	def get_tile_tuple(self, tup):
		"""Overloaded get_tile, takes a tuple as argument"""
		try:
			return self.ground_map[tup]()
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
		try:
			return self.get_tile(point).settlement
			# some tiles might be none, so we have to catch that error here
		except AttributeError:
			return None

	def get_settlements(self, rect):
		"""Returns the list of settlements for the coordinates describing a rect.
		@param rect: Area to search for settlements
		@return: list of Settlement instances at that position."""
		settlements = set()
		if self.rect.intersects(rect):
			for point in rect:
				try:
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
																												{'player':player.name})
		return settlement

	def add_existing_settlement(self, position, radius, settlement):
		"""Same as add_settlement, but uses settlement from parameter.
		May also be called for extension of an existing settlement by a new building. (this
		is useful for loading, where every loaded building extends the radius of its settlement).
		@param position: Rect"""
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
		for coord in position.get_radius_coordinates(radius, include_self=True):
			tile = self.get_tile(Point(coord[0], coord[1]))
			if tile is not None:
				if tile.settlement == settlement:
					continue
				if (tile.settlement is None) or (tile.settlement.owner == settlement.owner):
					tile.settlement = settlement
					self.session.ingame_gui.minimap.update(coord)

				building = tile.object
				# assign buildings on tiles to settlement
				if building is not None and building.settlement is None:
					building.settlement = settlement
					settlement.buildings.append(building)

		#TODO: inherit resources etc


	def add_building(self, building, player):
		"""Adds a building to the island at the position x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		for building.settlement in self.get_settlements(building.position):
			self.assign_settlement(building.position, building.radius, building.settlement)
			break

		# Set all tiles in the buildings position(rect)
		for point in building.position:
			tile = self.get_tile(point)
			tile.blocked = True # Set tile blocked
			tile.object = building # Set tile's object to the building
			self.path_nodes.reset_tile_walkability(point.to_tuple())
		self.buildings.append(building)
		if building.settlement is not None:
			building.settlement.buildings.append(building)
		building.init()
		return building

	def remove_building(self, building):
		assert building.island == self

		# Reset the tiles this building was covering
		for point in building.position:
			tile = self.get_tile(point)
			tile.blocked = False
			tile.object = None
			self.path_nodes.reset_tile_walkability(point.to_tuple())

		if building.settlement is not None:
			building.settlement.buildings.remove(building)
			assert(building not in building.settlement.buildings)

		# Remove this building from the buildings list
		self.buildings.remove(building)
		assert building not in self.buildings

	def get_surrounding_tiles(self, point, radius = 1):
		"""Returns tiles around point with specified radius.
		@param point: instance of Point"""
		for position in Circle(point, radius):
			tile = self.get_tile(position)
			if tile is not None:
				yield tile

	def get_providers_in_range(self, circle):
		"""Returns all instances of provider within the specified circle.
		@param circle: instance of Circle
		@return: list of providers"""
		providers = []
		for provider in self.provider_buildings:
			if provider.position.distance_to_circle(circle) <= 0:
				providers.append(provider)
		return providers

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

