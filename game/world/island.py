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
	@param x, y: int position coordinates.
	@param file: file from which the island is loaded.
	"""

	def __init__(self, x, y, file):
		"""
		@param x:
		@param y:
		@param file: db file for island
		"""
		self.file = file
		game.main.db("attach ? as island", file)
		p_x, p_y, width, height = game.main.db("select (min(x) + ?), (min(y) + ?), (1 + max(x) - min(x)), (1 + max(y) - min(y)) from island.ground", x, y)[0]
		self.rect = Rect(Point(p_x, p_y), width, height)
		self.grounds = []
		self.buildings = []
		for (rel_x, rel_y, ground_id) in game.main.db("select x, y, ground_id from island.ground"):
			ground = game.main.session.entities.grounds[ground_id](x + rel_x, y + rel_y)
			ground.settlement = None
			ground.blocked = False
			ground.object = None
			self.grounds.append(ground)
		game.main.db("detach island")
		self.settlements = []

		self.path_nodes = {}

	def save(self, db):
		from game.dbreader import DbReader
		
		islanddb = DbReader(self.file)
		save_x, save_y = islanddb("SELECT (? - min(x)), (? - min(y)) FROM ground", self.x, self.y)[0]
		
		db("INSERT INTO island (rowid, x, y, file) VALUES (?, ?, ?, ?)",
			self.getId(), save_x, save_y, self.file)
		for settlement in self.settlements:
			settlement.save(db)
		for building in self.buildings:
			building.save(db)
			
	def load(self, db, worldid):
		
		
		super(Island, self).load(db, worldid)

	def get_tile(self, point):
		"""Returns whether a tile is on island or not.
		@param point: Point containt position of the tile.
		@return: tile instance if tile is on island, else None."""
		if not self.rect.contains(point):
			return None
		for tile in self.grounds:
				if tile.x == point.x and tile.y == point.y:
					return tile
		return None

	def get_building(self, x, y):
		"""Returns the building at the position (x,y)
		@param x: int x coordinate
		@param y: int y coordinate
		@return: Building class instance or None if none is found.
		"""
		if not self.rect.contains(Point(x, y)):
			return None
		settlements = self.get_settlements(x, y)
		if len(settlements) == 0:
			for b in self.buildings:
				if b.x <= x < b.x + b.__class__.size[0] and b.y <= y < b.y + b.__class__.size[1]:
					return b
			else:
				return None
		else:
			for settlement in settlements:
				return settlement.get_building(x, y)

	def get_settlements(self, min_x, min_y, max_x = None, max_y = None):
		"""Returns the list of settlements for the coordinates describing a rect.
		@param min_x: int minimum x position.
		@param min_y: int minimum y position.
		@param max_x: int maximum x position.
		@param max_y: int maximum y position.
		@return: list of Settlement instances at that position."""
		# TODO: use a rect as argument
		if max_x is None:
			max_x = min_x
		if max_y is None:
			max_y = min_y
		rect = Rect(min_x, min_y, max_x, max_y)
		settlements = []
		# intersect returns None if the two rects do not overlap
		if not self.rect.intersect(rect):
			return []
		for tile in self.grounds:
			if min_x <= tile.x <= max_x and min_y <= tile.y <= max_y and tile.settlement is not None and tile.settlement not in settlements:
				settlements.append(tile.settlement)
		return settlements

	def add_settlement(self, min_x, min_y, max_x, max_y, radius, player):
		"""Adds a settlement to the island at the posititon x, y with radius as area of influence.
		@param x,y: int position used as center for the area of influence
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(player)
		self.settlements.append(settlement)
		self.assign_settlement(min_x, min_y, max_x, max_y, radius, settlement)
		game.main.session.ingame_gui.message_widget.add(min_x, min_y, 1, {'player':player.name})
		return settlement

	def assign_settlement(self, min_x, min_y, max_x, max_y, radius, settlement):
		"""
		@param min_x:
		@param min_y:
		@param max_x:
		@param max_y:
		@param radius:
		@param settlement:
		"""
		inherits = []
		for tile in self.grounds: # Set settlement var for all tiles in the radius.
			if (max(min_x - tile.x, 0, tile.x - max_x) ** 2) + (max(min_y - tile.y, 0, tile.y - max_y) ** 2) <= radius ** 2:
				if tile.settlement is None:
					tile.settlement = settlement
				elif tile.settlement.owner == settlement.owner:
					inherits.append(tile.settlement)
		for tile in self.grounds:
			if tile.settlement in inherits:
				tile.settlement = settlement
		#TODO: inherit resources etc

	def add_building(self, x, y, building, player):
		"""Adds a building to the island at the posititon x, y with player as the owner.
		@param x,y: int position used as center for the area of influence
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		# the lines that are commented out, were moved to UnselectableBuilding.__init__()
		#building.island = self
		for building.settlement in self.get_settlements(x, y):
			self.assign_settlement(x, y, x + building.size[0] - 1, y + building.size[1] - 1, building.radius, building.settlement)
			break
		#else:
		#	building.settlement = self.add_settlement(x, y, x + building.size[0] - 1, y + building.size[1] - 1, building.radius, player)
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
		assert (building.island == self)

		for x in xrange(building.x, building.x + building.__class__.size[0]):
			for y in xrange(building.y, building.y + building.__class__.size[1]):
				tile = self.get_tile(Point(x,y))
				tile.blocked = False
				tile.object = None
		building.settlement.buildings.remove(building)
		assert(building not in building.settlement.buildings)

	def registerPath(self, path):
		self.path_nodes[ (path.x, path.y) ] = path.__class__.speed

	def unregisterPath(self, path):
		del self.path_nodes[ (path.x, path.y) ]
