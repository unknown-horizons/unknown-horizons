# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main
from game.dbreader import DbReader
from game.world.settlement import Settlement
from pathfinding import findPath
from game.util import WorldObject, Point, Rect

class Island(WorldObject):
	"""The Island class represents an Island by keeping a list of all instances on the map,
	that belong to the island. The island variable is also set on every instance that belongs
	to an island, making it easy to determine to which island the instance belongs, when
	selected.
	An Island instance is created at map creation, when all tiles are added to the map.
	@param id: island id.
	@param origin: Position of the (0, 0) ground tile.
	@param filename: file from which the island is loaded.
	"""
	
	def __init__(self, origin, filename):
	
		x, y = origin.x, origin.y
		
		self.file = filename
		self.origin = origin
		db = DbReader(filename)
		p_x, p_y, width, height = db("select (min(x) + ?), (min(y) + ?), (1 + max(x) - min(x)), (1 + max(y) - min(y)) from ground", x, y)[0]
		self.rect = Rect(Point(p_x, p_y), width, height)
		self.grounds = []
		self.buildings = []
		for (rel_x, rel_y, ground_id) in db("select x, y, ground_id from ground"):
			ground = game.main.session.entities.grounds[ground_id](x + rel_x, y + rel_y)
			ground.settlement = None
			ground.blocked = False
			ground.object = None
			self.grounds.append(ground)
		
		self.settlements = []

		self.path_nodes = {}

	def save(self, db):
		db("INSERT INTO island (rowid, x, y, file) VALUES (?, ?, ?, ?)",
			self.getId(), self.origin.x, self.origin.y, self.file)
		for building in self.buildings:
			building.save(db)
		for settlement in self.settlements:
			settlement.save(db)

	def load(self, db, worldid):
		super(Island, self).load(db, worldid)
		
		for (settlement_id,) in db("SELECT rowid FROM settlement WHERE island = ?", worldid):
			settlement = Settlement.load(db, settlement_id)
			self.settlements.append(settlement)
		
		for (building_worldid, building_typeid) in \
			db("SELECT rowid, type FROM building WHERE location = ?", worldid):
				
			buildingclass = game.main.session.entities[building_typeid]
			building = buildingclass.load(db, building_worldid)
			self.add_building(building)

	def get_tile(self, point):
		"""Returns whether a tile is on island or not.
		@param point: Point containt position of the tile.
		@return: tile instance if tile is on island, else None."""
		# TODO: Reimplement this horribly slow linear search with a better container, like dict
		if not self.rect.contains(point):
			return None
		for tile in self.grounds:
				if tile.x == point.x and tile.y == point.y:
					return tile
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
					return b
		return None

	def get_settlement(self, point):
		"""Look for a settlement on a specific tile
		@param point: Point to look on
		@return: Settlement at point, or None"""
		
		settlements = self.get_settlements(Rect(point, 1, 1))
		
		if settlements:
			assert len(settlements) == 1
			return settlements[0]
		return None

	def get_settlements(self, rect):
		"""Returns the list of settlements for the coordinates describing a rect.
		@param rect: Area to search for settlements
		@return: list of Settlement instances at that position."""
		settlements = []
		if self.rect.intersects(rect):
			for tile in self.grounds:
				if rect.contains(tile) and tile.settlement is not None and tile.settlement not in settlements:
					settlements.append(tile.settlement)
		return settlements

	def add_settlement(self, position, radius, player):
		"""Adds a settlement to the island at the posititon x, y with radius as area of influence.
		@param position: Rect describing the position of the new branch office
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(player)
		self.settlements.append(settlement)
		self.assign_settlement(position, radius, settlement)
		# TODO: Move this to command, this message should not appear while loading
		game.main.session.ingame_gui.message_widget.add(position.center().x, position.center().y, 1, {'player':player.name})
		return settlement

	def assign_settlement(self, position, radius, settlement):
		"""
		@param position: Rect
		@param radius:
		@param settlement:
		"""
		inherits = []
		for tile in self.grounds: # Set settlement var for all tiles in the radius.
			# TODO: make this readable
			if (max(position.left - tile.x, 0, tile.x - position.right) ** 2) + (max(position.top - tile.y, 0, tile.y - position.bottom) ** 2) <= radius ** 2:
				if tile.settlement is None:
					tile.settlement = settlement
				elif tile.settlement.owner == settlement.owner:
					inherits.append(tile.settlement)
		for tile in self.grounds:
			if tile.settlement in inherits:
				tile.settlement = settlement
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
		building.settlement.buildings.append(building)
		building.init()
		building.start()
		#print "New building created at (%i:%i) for player '%s' and settlement '%s'" % (x, y, player.name, building.settlement.name)
		return building

	def remove_building(self, building):
		assert (building.island() == self)

		for point in building.position:
				tile = self.get_tile(point)
				tile.blocked = False
				tile.object = None
		building.settlement.buildings.remove(building)
		assert(building not in building.settlement.buildings)

	def registerPath(self, path):
		origin = path.position.origin
		self.path_nodes[ (origin.x, origin.y) ] = path.__class__.speed

	def unregisterPath(self, path):
		origin = path.position.origin
		del self.path_nodes[ (origin.x, origin.y) ]

	def get_surrounding_tiles(self, point):
		tile_offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
		return [self.get_tile(point.offset(*offset)) for offset in tile_offsets]
