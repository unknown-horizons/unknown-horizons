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
import random
import logging

import horizons.main

from island import Island
from player import Player
from horizons.util import Point, Color, Rect, LivingObject, Circle
from horizons.constants import UNITS, BUILDINGS, RES
from horizons.ai.trader import Trader
from horizons.entities import Entities
from horizons.util import decorators
from horizons.settings import Settings

class World(LivingObject):
	"""The World class represents an Unknown Horizons map with all its units, grounds, buildings, etc.

	   * players - a list of all the session's players - Player instances
	   * islands - a list of all the map's islands - Island instances
	   * grounds - a list of all the map's groundtiles
	   * ground_map - a dictionary that binds tuples of coordinates with a reference to the tile:
	                  { (x, y): tileref, ...}
					  This is important for pathfinding and quick tile fetching.
	   * ships - a list of all the ships ingame - horizons.world.units.ship.Ship instances
	   * ship_map - same as ground_map, but for ships
	   TUTORIAL: You should now check out the _init() function.
	"""
	log = logging.getLogger("world")
	def __init__(self, session):
		"""
		@param session: instance of session the world belongs to.
		"""
		self.inited = False
		self.session = session
		super(World, self).__init__()

	def end(self):
		self.session = None
		self.properties = None
		self.players = None
		self.player = None
		self.min_x, self.min_y, self.max_x, self.max_y = None, None, None, None
		self.grounds = None
		self.ground_map = None
		self.ship_map = None
		self.ships = None
		self.trader = None
		super(World, self).end()

	@decorators.make_constants()
	def _init(self, savegame_db):
		"""
		@param savegame_db: Dbreader with loaded savegame database
		"""
		#load properties
		self.properties = {}
		for (name, value) in savegame_db("SELECT name, value FROM map_properties"):
			self.properties[name] = value

		# create playerlist
		self.players = []
		self.player = None # player sitting in front of this machine
		self.trader = None

		# load player
		human_players = []
		for player_id, client_id in savegame_db("SELECT rowid, client_id FROM player WHERE is_trader = 0"):
			player = None
			ai_data = self.session.db("SELECT class_package, class_name FROM ai WHERE id = ?", client_id)
			if len(ai_data) > 0:
				# import ai class and call load on it
				module = __import__('horizons.ai.'+ai_data[0][0], fromlist=[ai_data[0][1]])
				ai_class = getattr(module, ai_data[0][1])
				player = ai_class.load(self.session, savegame_db ,player_id)
			else: # no ai
				player = Player.load(self.session, savegame_db, player_id)
			self.players.append(player)

			if client_id == Settings().client_id:
				self.player = player
			elif client_id is not None and len(ai_data) == 0:
				# possible human player candidate with different client id
				human_players.append(player)

		if self.player is None:
			# we have no human player.
			# check if there is only one player with an id (i.e. human player)
			# this would be the case if the savegame originates from a different installation.
			# if there's more than one of this kind, we can't be sure what to select.
			# TODO: create interface for selecting player, if we want this
			if(len(human_players) == 1):
				# exactly one player, we can quite safely use this one
				self.player = human_players[0]

		if self.player is None and self.session.is_game_loaded():
			self.log.warning('WARNING: Cannot autoselect a player because there are no \
			or multiple candidates.')

		#load islands
		self.islands = []
		for (islandid,) in savegame_db("SELECT rowid FROM island"):
			island = Island(savegame_db, islandid, self.session)
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

		self.map_dimensions = Rect(self.min_x, self.min_y, self.max_x, self.max_y)

		#add water
		self.log.debug("Filling world with water...")
		self.grounds = []
		self.ground_map = {}
		default_grounds = Entities.grounds[int(self.properties.get('default_ground', 4))]
		for x in xrange(self.min_x, self.max_x):
			for y in xrange(self.min_y, self.max_y):
				ground = default_grounds(self.session, x, y)
				self.grounds.append(ground)
				self.ground_map[(x, y)] = weakref.ref(ground)
		for i in self.islands:
			for g in i.grounds:
				if (g.x, g.y) in self.ground_map:
					del self.ground_map[(g.x, g.y)]

		self.num_water = len(self.ground_map)
		self.water = list(self.ground_map)

		# create ship position list. entries: ship_map[(x, y)] = ship
		self.ship_map = {}

		# create shiplist, which is currently used for saving ships
		# and having at least one reference to them
		self.ships = []

		if self.session.is_game_loaded():
			# for now, we have one trader in every game, so this is safe:
			trader_id = savegame_db("SELECT rowid FROM player WHERE is_trader = 1")[0][0]
			self.trader = Trader.load(self.session, savegame_db, trader_id)

		# load all units (we do it here cause all buildings are loaded by now)
		for (worldid, typeid) in savegame_db("SELECT rowid, type FROM unit ORDER BY rowid"):
			Entities.units[typeid].load(self.session, savegame_db, worldid)

		if self.session.is_game_loaded():
			# let trader command it's ships. we have to do this here cause ships have to be
			# initialised for this, and trader has to exist before ships are loaded.
			self.trader.load_ship_states(savegame_db)

		self.inited = True
		"""TUTORIAL:
		To dig deeper, you should now continue to horizons/world/island.py,
		to check out how buildings and settlements are added to the map"""

	@decorators.make_constants()
	def init_new_world(self):
		"""This should be called if a new map is loaded (not a savegame, a fresh
		map). In other words when it is loaded for the first time.

		@return: Returs the coordinates of the players first ship
		"""
		# workaround: the creation of all the objects causes a lot of logging output, we don't need
		#             therefore, reset the levels for now
		loggers_to_silence = { 'world.production' : None }
		for logger_name in loggers_to_silence:
			logger = logging.getLogger(logger_name)
			loggers_to_silence[logger_name] = logger.getEffectiveLevel()
			logger.setLevel( logging.WARN )

		from horizons.command.building import Build
		from horizons.command.unit import CreateUnit
		# add a random number of trees to the gameworld
		if int(self.properties.get('RandomTrees', 1)) == 1:
			tree = Entities.buildings[BUILDINGS.TREE_CLASS]
			for island in self.islands:
				for tile in island.ground_map.iterkeys():
					# add tree to about every third tile
					if random.randint(0, 10) < 3 and "constructible" in island.ground_map[tile]().classes:
						building = Build(self.session, tree, tile[0], tile[1], ownerless=True, island=island).execute()
						building.finish_production_now() # make trees big and fill their inventory
						if random.randint(0, 40) < 1: # add animal to every nth tree
							CreateUnit(island.getId(), UNITS.WILD_ANIMAL_CLASS, *tile).execute()

		# reset loggers, see above
		for logger_name, level in loggers_to_silence.iteritems():
			logging.getLogger(logger_name).setLevel(level)

		# add free trader
		self.trader = Trader(self.session, 99999, "Free Trader", Color())
		ret_coords = None
		for player in self.players:
			# Adding ships for the players
			point = self.get_random_possible_ship_position()
			ship = CreateUnit(player.getId(), UNITS.PLAYER_SHIP_CLASS, point.x, point.y).execute()
			# give ship basic resources
			for res, amount in self.session.db("SELECT resource, amount FROM start_resources"):
				ship.inventory.alter(res, amount)
			if player is self.player:
				ret_coords = (point.x, point.y)
		# Fire a message for new world creation
		self.session.ingame_gui.message_widget.add(self.max_x/2, self.max_y/2, 'NEW_WORLD')
		assert ret_coords is not None, "Return coords are none. No players loaded?"
		return ret_coords

	@decorators.make_constants()
	def get_random_possible_ship_position(self):
		"""Returns a position in water, that is not at the border of the world"""
		rand_water_id = random.randint(0, self.num_water-1)
		ground_iter = self.ground_map.iterkeys()
		for i in xrange(0, rand_water_id-1):
			ground_iter.next()
		x, y = ground_iter.next()

		offset = 2
		position_possible = True
		if x - offset < self.min_x or x + offset > self.max_x or \
			 y - offset < self.min_y or y + offset > self.max_y:
			# we're too near to the border
			position_possible = False

		if (x, y) in self.ship_map:
			position_possible = False

		# check if there is an island nearby (check only important)
		for first_sign in (-1, 0, 1):
			for second_sign in (-1, 0, 1):
				point_to_check = Point( x + offset*first_sign, y + offset*second_sign )
				if self.get_island(point_to_check) is not None:
					position_possible = False
					break
			if not position_possible: # propagate break
				break

		if not position_possible:
			# in theory, this might result in endless loop, but in practice, it doesn't
			return self.get_random_possible_ship_position()
		return Point(x, y)

	#----------------------------------------------------------------------
	def get_tiles_in_radius(self, position, radius):
		"""Returns a all tiles in the radius around the point.
		This is a generator, make sure you use it appropriately.
		@param position: Point instance
		@return List of tiles in radius.
		"""
		assert isinstance(position, Point)
		for point in Circle(position, radius):
			if self.map_dimensions.contains_without_border(point):
				# don't yield if point is not in map, those points don't exist
				yield self.get_tile(point)

	def setup_player(self, name, color):
		"""Sets up a new Player instance and adds him to the active world."""
		self.player =  Player(self.session, 0, name, color, inventory={RES.GOLD_ID: 20000})
		self.players.append(self.player)
		self.session.ingame_gui.update_gold()
		self.player.inventory.add_change_listener(self.session.ingame_gui.update_gold)

	def get_tile(self, point):
		"""Returns the ground at x, y.
		@param point: coords as Point
		@return: instance of Ground at x, y
		"""
		i = self.get_island(point)
		if i is not None:
			return i.get_tile(point)
		assert (point.x, point.y) in self.ground_map, 'ground is not on island or water. invalid coord: %s'%point
		return self.ground_map[(point.x, point.y)]()

	def get_settlement(self, point):
		"""Returns settlement on point.
		@param point: instance of Point
		@return: instance of Settlement or None"""
		return self.get_tile(point).settlement

	def get_building(self, point):
		"""Returns the building at the position x, y.
		@param point: Point instance
		@return: Building class instance if a building is found, else None."""
		i = self.get_island(point)
		return None if i is None else i.get_building(point)

	def get_island(self, point):
		"""Returns the island for that coordinate, if none is found, returns None.
		@param point: instance of Point"""
		for island in self.islands:
			if not island.rect.contains(point):
				continue
			if point.to_tuple() in island.ground_map:
				return island
		return None

	def get_islands_in_radius(self, point, radius):
		"""Returns all islands in a certain radius around a point.
		@return List of islands in radius"""
		islands = []
		for island in self.islands:
			for tile in island.get_surrounding_tiles(point, radius):
				islands.append(island)
				break
		return islands

	@decorators.make_constants()
	def get_branch_offices(self, position=None, radius=None):
		"""Returns all branch offices on the map. Optionally only those in range
		around the specified position.
		@param position: Point or Rect instance.
		@param radius: int radius to use.
		@return: List of branch offices.
		"""
		branchoffices = []
		islands = []
		if radius is not None and position is not None:
			islands = self.get_islands_in_radius(position, radius)
		else:
			islands = self.islands
		for island in islands:
			for settlement in island.settlements:
				for building in settlement.buildings:
					if isinstance(building, horizons.world.building.storages.BranchOffice):
						if radius is None or position is None or \
						   building.position.distance(position) <= radius:
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
		if self.trader is not None:
			self.trader.save(db)
		for ship in self.ships:
			ship.save(db)


def load_building(session, db, typeid, worldid):
	"""Loads a saved building. Don't load buildings yourself in the game code."""
	Entities.buildings[typeid].load(session, db, worldid)
