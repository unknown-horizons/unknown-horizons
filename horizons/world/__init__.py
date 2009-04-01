# -*- coding: utf-8 -*-
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

__all__ = ['island', 'nature', 'player', 'settlement', 'ambientsound']

import weakref

import horizons.main

from island import Island
from player import Player
from horizons.util import Point, Color
from horizons.util.living import LivingObject

class World(LivingObject):
	"""The World class represents an Unknown Horizons map with all its units, grounds, buildings, etc.

	   * players - a list of all the sessios's players - Player instances
	   * islands - a list of all the map's islands - Island instances
	   * grounds - a list of all the map's groundtiles
	   * ground_map - a dictionary that binds tuples of coordinates with a reference to the tile:
	                  { (x,y): tileref, ...}
					  This is important for pathfinding and quick tile fetching.
	   * ships - a list of all the ships ingame - horizons.world.units.ship.Ship instances
	   * ship_map - same as ground_map, but for ships
	   TUTORIAL: You should now check out the _init() function.
	"""
	def __init__(self, **kwargs):
		"""@param db: DbReader instance with the map/savegame that is to be loaded
		"""
		super(World, self).__init__()

	def end(self):
		self.properties = None
		self.players = None
		self.player = None
		self.min_x, self.min_y, self.max_x, self.max_y = None, None, None, None
		self.grounds = None
		self.ground_map = None
		self.water = None
		self.ship_map = None
		self.ships = None
		self.trader = None
		super(World, self).end()

	def _init(self, db):
		#load properties
		self.properties = {}
		for (name, value) in db("select name, value from map_properties"):
			self.properties[name] = value

		# create playerlist
		self.players = []

		# load player
		for player_id, client_id in db("SELECT rowid, client_id FROM player"):
			player = Player.load(db, player_id)
			self.players.append(player)
			if client_id == horizons.main.settings.client_id or client_id == "":
				self.player = player

		#load islands
		self.islands = []
		for filename, offset_x, offset_y, islandid in db("select file, x, y, rowid from island"):
			island = Island(Point(offset_x, offset_y), filename)
			island.load(db, islandid)

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
		self.water = {}
		for x in xrange(self.min_x, self.max_x):
			for y in xrange(self.min_y, self.max_y):
				self.water[(x,y)] = 1
		for i in self.islands:
			for g in i.grounds:
				del self.water[(g.x,g.y)]
		self.water = self.water.keys()
		print "Adding %d water tiles..." % (len(self.water),)
		self.grounds = []
		self.ground_map = {}
		default_grounds = horizons.main.session.entities.grounds[int(self.properties.get('default_ground', 4))]
		for x, y in self.water:
			ground = default_grounds(x, y)
			self.grounds.append(ground)
			self.ground_map[(x,y)] = weakref.ref(ground)
		print "Done."

		# Add a random number of trees to the gameworld
		if not horizons.main.session.is_game_loaded():
			if int(self.properties.get('RandomTrees', 1)) == 1:
				print "Adding trees to the world..."
				import random
				from horizons.command.building import Build
				for island in self.islands:
					for tile in island.ground_map.keys():
						if random.randint(0,10) < 3 and "constructible" in island.ground_map[tile]().classes:
							horizons.main.session.manager.execute(Build(horizons.main.session.entities.buildings[17],tile[0],tile[1],45, ownerless=True, island=island))
					for building in island.buildings:
						building.production_step()
				print "Done."

		# create ship position list. entries: ship_map[(x, y)] = ship
		self.ship_map = {}
		## TODO same for blocking units on island, as soon as such are implemented

		# create shiplist, which is currently used for saving ships
		# and having at least one reference to them
		self.ships = []

		# load all units (we do it here cause all buildings are loaded by now)
		for (worldid, typeid) in db("SELECT rowid, type FROM unit ORDER BY rowid"):
			horizons.main.session.entities.units[typeid].load(db, worldid)

		if not horizons.main.session.is_game_loaded():
			# for initiateing a new game:

			# add free trader
			from horizons.ai.trader import Trader
			self.trader = Trader(99999, "Free Trader", Color())

			# Fire a message for new world creation
			horizons.main.session.ingame_gui.message_widget.add(self.max_x/2, self.max_y/2, 2)
		"""TUTORIAL:
		To digg deaper, you should now continue to game/world/island.py,
		to check out how buildings and settlements are added to the map"""

	def setupPlayer(self, name, color):
		"""Sets up a new Player instance and adds him to the active world."""
		self.player =  Player(0, name, color)
		self.players.append(self.player)
		horizons.main.session.ingame_gui.update_gold()
		self.player.inventory.addChangeListener(horizons.main.session.ingame_gui.update_gold)

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
		@return: Building class instance if a building is found, else None."""
		if horizons.main.debug:
			print "World get_building"
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
			if point.get_coordinates()[0] in i.ground_map:
				return i
		return None

	def get_branch_offices(self):
		"""Returns all branch offices on the map."""
		branchoffices = []
		for island in horizons.main.session.world.islands:
			for settlement in island.settlements:
				for building in settlement.buildings:
					if isinstance(building,horizons.world.building.storages.BranchOffice):
						branchoffices.append(building)
		return branchoffices

	def save(self, db):
		"""Saves the current game to the specified db.
		@param db: DbReader object of the db the game is saved to."""
		for name, value in self.properties.iteritems():
			db("INSERT INTO map_properties (name, value) VALUES (?, ?)", name, value)
		for island in self.islands:
			island.save(db)
		for player in self.players:
			player.save(db)
		for ship in self.ships:
			ship.save(db)
