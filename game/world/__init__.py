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

__all__ = ['island', 'nature', 'player', 'settlement']

import weakref

import game.main
from game.world.island import Island
from game.world.player import Player
from game.util import livingObject, Point

class World(livingObject):
	"""
	"""
	def begin(self, db):
		#load properties
		self.properties = {}
		for (name, value) in db("select name, value from map_properties"):
			self.properties[name] = value

		#load islands
		self.islands = []
		for filename, offset_x, offset_y, islandid in db("select file, x, y, rowid from island"):
			island = Island(Point(offset_x, offset_y), filename)
			island.load(db, islandid)
			self.islands.append(island)

		#calculate map dimensions
		self.min_x, self.min_y, self.max_x, self.max_y = None, None, None, None
		for i in self.islands:
			self.min_x = i.rect.left if self.min_x is None or i.rect.left < self.min_x else self.min_x
			self.min_y = i.rect.top if self.min_y is None or i.rect.top < self.min_y else self.min_y
			self.max_x = i.rect.right if self.max_x is None or i.rect.right > self.max_x else self.max_x
			self.max_y = i.rect.bottom if self.max_y is None or i.rect.bottom > self.max_y else self.max_y
		self.min_x -= 10
		self.min_y -= 10
		self.max_x += 10
		self.max_y += 10

		#add water
		print "Filling world with water..."
		self.water = [ (x,y) for x in xrange(self.min_x, self.max_x) for y in xrange(self.min_y, self.max_y) ]
		for i in self.islands:
			for g in i.grounds:
				self.water.remove((g.x,g.y))
		print "Adding %d water tiles..." % (len(self.water),)
		self.grounds = []
		self.ground_map = {}
		for x, y in self.water:
			ground = game.main.session.entities.grounds[int(self.properties.get('default_ground', 4))](x, y)
			self.grounds.append(ground)
			self.ground_map[(x,y)] = weakref.ref(ground)
		print "Done."

		# create ship position list. entries: ship_map[ship.unit_position] = ship
		self.ship_map = {}
		## TODO same for blocking units on island, as soon as such are implemented

		# create playerlist
		self.players = []

		# create shiplist
		self.ships = []

		# old code for loading ships:
		for (worldid, typeid) in db("SELECT rowid, type FROM unit"):
			# workaround to distinguish between ships and other units
			unitclass = game.main.session.entities.units[typeid]
			from game.world.units.ship import Ship
			if issubclass(unitclass, Ship):
				self.ships.append(unitclass.load(db, worldid))
				
	def setupPlayer(self, name, color):
		self.player =  Player(0, name, color)
		self.players.append(self.player)
		game.main.session.ingame_gui.update_gold()
		self.player.inventory.addChangeListener(game.main.session.ingame_gui.update_gold)
		
	def get_tile(self, point):
		"""Returns the ground at x, y. 
		@param point: coords as Point
		@return: instance of Ground at x, y
		"""
		i = self.get_island(point.x, point.y)
		if i is not None:
			return i.get_tile(point)
		assert (point.x, point.y) in self.ground_map, 'ground must be in water'
		return self.ground_map[(point.x, point.y)]()

	def get_building(self, x, y):
		"""Returns the building at the position x,y.
		@param x,y: int coordinates.
		@return: Building class instance if a building is found, else none."""
		i = self.get_island(x, y)
		return None if i is None else i.get_building(Point(x, y))

	def get_island(self, x, y):
		"""Returns the island for that coordinate, if none is found, returns None.
		@param x: int x position.
		@param y: int y position. """
		point = Point(x, y)
		for i in self.islands:
			if not i.rect.contains(point):
				continue
			for tile in i.grounds:
				if tile.x == x and tile.y == y:
					return i
		return None

	def save(self, db):
		"""Saves the current game to the specified db.
		@param db: DbReader object of the db the game is saved to."""
		print 'STARTING SAVING'
		for name, value in self.properties.iteritems():
			db("INSERT INTO map_properties (name, value) VALUES (?, ?)", name, value)
		for island in self.islands:
			island.save(db)
		for player in self.players:
			player.save(db)
		for ship in self.ships:
			ship.save(db)
		print 'FINISHED SAVING'
