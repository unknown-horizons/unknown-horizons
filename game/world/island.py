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
from stablelist import stablelist

class Island(object):
	"""The Island class represents an Island by keeping a list of all instances on the map,
	that belong to the island. The island variable is also set on every instance that belongs
	to an island, making it easy to determine to which island the instance belongs, when
	selected.
	An Island instance is created at map creation, when all tiles are added to the map.
	"""

	def __init__(self, id, x, y, file):
		self.id = id
		self.file = file
		self.x, self.y = x, y
		game.main.db("attach ? as island", file)
		self.width, self.height = game.main.db("select (1 + max(x) - min(x)), (1 + max(y) - min(y)) from island.ground")[0]
		self.grounds = []
		self.buildings = stablelist()
		for (rel_x, rel_y, ground_id) in game.main.db("select x, y, ground_id from island.ground"):
			ground = game.main.session.entities.grounds[ground_id](x + rel_x, y + rel_y)
			ground.settlement = None
			ground.blocked = False
			ground.object = None
			self.grounds.append(ground)
		game.main.db("detach island")
		self.settlements = stablelist()

	def save(self, db = 'savegame'):
		id = game.main.db(("INSERT INTO %s.island (x, y, file) VALUES (?, ?, ?)" % db), self.x, self.y, self.file).id

	def get_tile(self, x, y):
		"""Returns whether a tile is on island or not.
		@param x: int x position of the tile.
		@param y: int y position of the tile.
		@param island: id of the island that is to be checked.
		@return: tile instanze if tile is on island, else None."""
		if not (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height):
			return None
		for tile in self.grounds:
				if tile.x == x and tile.y == y:
					return tile
		return None

	def get_building(self, x, y):
		if not (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height):
			return None
		s = self.get_settlement_at_position(x, y)
		if s == None:
			for b in self.buildings:
				if b.x <= x < b.x + b.__class__.size[0] and b.y <= y < b.y + b.__class__.size[1]:
					return b
			else:
				return None
		else:
			return s.get_building(x, y)

	def get_settlement_at_position(self, x, y):
		"""Returns the settlement for that coordinate, if none is found, returns None.
		@param x: int x position.
		@param y: int y position.
		@param island: island that is to be searched.
		@return: Settlement instance at that position."""
		if not (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height):
			return None
		for tile in self.grounds:
			if tile.x == x and tile.y == y:
				return tile.settlement
		return None

	def add_settlement(self, x, y, radius, player):
		"""Adds a settlement to the island at the posititon x, y with radius as area of influence.
		@param x,y: int position used as center for the area of influence
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(player)
		self.settlements.append(settlement)
		for tile in self.grounds: # Set settlement var for all tiles in the radius.
			if abs((tile.x-x)**2+(tile.y-y)**2) <= radius**2:
				tile.settlement = settlement
		print "New settlement created at (%i:%i) for player: %s" % (x, y, player.name)

	def add_building(self, x, y, building, player):
		"""Adds a building to the island at the posititon x, y with player as the owner.
		@param x,y: int position used as center for the area of influence
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		settlement = self.get_settlement_at_position(x, y)
		if building.size[0] == 1 and building.size[1] == 1:
			tile = self.get_tile(x, y)
			tile.blocked = True 	# Set tile blocked
			tile.object = building 	# Set tile's object to the building
		else:
			for i in xrange(0, building.size[0]):
				startx = x - building.size[0]/2 + i
				for b in xrange(0, building.size[1]):
					starty = y - building.size[1]/2 + b
					tile = self.get_tile(startx, starty)
					tile.blocked = True 	# Set tile blocked
					tile.object = building 	# Set tile's object to the building
		building.island = self
		building.settlement = settlement
		settlement.buildings.append(building)
		print "New building created at (%i:%i) for player '%s' and settlement '%s'" % (x, y, player.name, settlement.name)
