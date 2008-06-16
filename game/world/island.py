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
		for (rel_x, rel_y, ground_id) in game.main.db("select x, y, ground_id from island.ground"):
			ground = game.main.session.entities.grounds[ground_id](x + rel_x, y + rel_y)
			ground.settlement = None
			self.grounds.append(ground)
		game.main.db("detach island")
		self.settlements = []

	def save(self, db = 'savegame'):
		id = game.main.db(("INSERT INTO %s.island (x, y, file) VALUES (?, ?, ?)" % db), self.x, self.y, self.file).id

	def contains_tile_at(self, x, y):
		"""Returns whether a tile is on island or not.
		@param x: int x position of the tile.
		@param y: int y position of the tile.
		@param island: id of the island that is to be checked.
		@return: bool True if tile is on island, else false."""
		for tile in self.grounds:
				if tile.x == x and tile.y == y:
					return True
		return False

	def get_settlement_at_position(self, x, y):
		"""Returns the settlement for that coordinate, if non is found, returns None.
		@param x: int x position.
		@param y: int y position.
		@param island: island that is to be searched.
		@return: Settlement instance at that position."""
		for tile in self.grounds:
			if tile.x == x and tile.y == y:
				return tile.settlement
		return None

	def add_settlement(self, x, y, radius, player):
		"""Adds a settlement to the island at the posititon x, y with radius as area of influence.
		@param x,y: int position used as center for the area of influence
		@param radius: int radius of the area of influence.
		@param player: int id of the player that owns the settlement"""
		settlement = Settlement(game.main.session.world.players[player])
		self.settlements.append(settlement)
		print radius**2
		for tile in self.grounds: # Set settlement var for all tiles in the radius.
			if abs((tile.x-x)**2-(tile.y-y)**2) <= radius**2:
				tile.settlement = settlement