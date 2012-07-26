# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import logging
import json
import copy

from collections import deque

import horizons.main
from horizons.world.island import Island
from horizons.world.player import HumanPlayer
from horizons.util import Point, Rect, Circle, WorldObject
from horizons.util.color import Color
from horizons.constants import UNITS, BUILDINGS, RES, GROUND, GAME
from horizons.ai.trader import Trader
from horizons.ai.pirate import Pirate
from horizons.ai.aiplayer import AIPlayer
from horizons.entities import Entities
from horizons.util import decorators, BuildingIndexer
from horizons.world.buildingowner import BuildingOwner
from horizons.world.diplomacy import Diplomacy
from horizons.world.units.bullet import Bullet
from horizons.world.units.weapon import Weapon
from horizons.command.unit import CreateUnit
from horizons.component.healthcomponent import HealthComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.world.disaster.disastermanager import DisasterManager
from horizons.world import worldutils

class World(BuildingOwner, WorldObject):
	"""The World class represents an Unknown Horizons map with all its units, grounds, buildings, etc.

	It inherits from BuildingOwner, among other things, so it has building management capabilities.
	There is always one big reference per building, which is stored in either the world, the island,
	or the settlement.

	The main components of the world are:
	   * players - a list of all the session's players - Player instances
	   * islands - a list of all the map's islands - Island instances
	   * grounds - a list of all the map's groundtiles
	   * ground_map - a dictionary that binds tuples of coordinates with a reference to the tile:
	                  { (x, y): tileref, ...}
	                 This is important for pathfinding and quick tile fetching.
	   * island_map - a dictionary that binds tuples of coordinates with a reference to the island
	   * ships - a list of all the ships ingame - horizons.world.units.ship.Ship instances
	   * ship_map - same as ground_map, but for ships
	   * session - reference to horizons.session.Session instance of the current game
	   * trader - The world's ingame free trader player instance (can control multiple ships)
	   * pirate - The world's ingame pirate player instance
	   TUTORIAL: You should now check out the _init() function.
	"""
	log = logging.getLogger("world")
	def __init__(self, session):
		"""
		@param session: instance of session the world belongs to.
		"""
		self.inited = False
		if False:
			assert isinstance(session, horizons.session.Session)
		self.session = session
		super(World, self).__init__(worldid=GAME.WORLD_WORLDID)

	def end(self):
		# destructor-like thing.
		super(World, self).end()

		for ship in [ship for ship in self.ships]:
			ship.remove()
		for island in self.islands:
			island.end()
		for player in self.players:
			player.end() # end players after game entities, since they usually depend on players

		self.session = None
		self.properties = None
		self.players = None
		self.player = None
		self.ground_map = None
		self.full_map = None
		self.island_map = None
		self.water = None
		self.ships = None
		self.ship_map = None
		self.fish_indexer = None
		self.ground_units = None
		self.trader = None
		self.pirate = None
		self.islands = None
		self.diplomacy = None
		self.bullets = None

	def _init(self, savegame_db, force_player_id=None, disasters_enabled=True):
		"""
		@param savegame_db: Dbreader with loaded savegame database
		@param force_player_id: the worldid of the selected human player or default if None (debug option)
		"""
		"""
		All essential and non-essential parts of the world are set up here, you don't need to
		know everything that happens.
		"""
		# load properties
		self.properties = {}
		for (name, value) in savegame_db("SELECT name, value FROM map_properties"):
			self.properties[name] = json.loads(value)
		if not 'disasters_enabled' in self.properties:
			# set on first init
			self.properties['disasters_enabled'] = disasters_enabled

		# create playerlist
		self.players = []
		self.player = None # player sitting in front of this machine
		self.trader = None
		self.pirate = None

		self._load_players(savegame_db, force_player_id)

		# all static data
		self.load_raw_map(savegame_db)

		# load world buildings (e.g. fish)
		for (building_worldid, building_typeid) in \
		    savegame_db("SELECT rowid, type FROM building WHERE location = ?", self.worldid):
			load_building(self.session, savegame_db, building_typeid, building_worldid)

		# use a dict because it's directly supported by the pathfinding algo
		self.water = dict.fromkeys(list(self.ground_map), 1.0)
		self._init_water_bodies()
		self.sea_number = self.water_body[(self.min_x, self.min_y)]

		# assemble list of water and coastline for ship, that can drive through shallow water
		# NOTE: this is rather a temporary fix to make the fisher be able to move
		# since there are tile between coastline and deep sea, all non-constructible tiles
		# are added to this list as well, which will contain a few too many
		self.water_and_coastline = copy.copy(self.water)
		for island in self.islands:
			for coord, tile in island.ground_map.iteritems():
				if 'coastline' in tile.classes or 'constructible' not in tile.classes:
					self.water_and_coastline[coord] = 1.0

		# create ship position list. entries: ship_map[(x, y)] = ship
		self.ship_map = {}
		self.ground_unit_map = {}

		# create shiplist, which is currently used for saving ships
		# and having at least one reference to them
		self.ships = []
		self.ground_units = []

		# create bullets list, used for saving bullets in ongoing attacks
		self.bullets = []

		if self.session.is_game_loaded():
			# there are 0 or 1 trader AIs so this is safe
			trader_data = savegame_db("SELECT rowid FROM player WHERE is_trader = 1")
			if trader_data:
				self.trader = Trader.load(self.session, savegame_db, trader_data[0][0])
			# there are 0 or 1 pirate AIs so this is safe
			pirate_data = savegame_db("SELECT rowid FROM player WHERE is_pirate = 1")
			if pirate_data:
				self.pirate = Pirate.load(self.session, savegame_db, pirate_data[0][0])

		# load all units (we do it here cause all buildings are loaded by now)
		for (worldid, typeid) in savegame_db("SELECT rowid, type FROM unit ORDER BY rowid"):
			Entities.units[typeid].load(self.session, savegame_db, worldid)

		if self.session.is_game_loaded():
			# let trader and pirate command their ships. we have to do this here
			# because ships have to be initialised for this, and they have
			# to exist before ships are loaded.
			if self.trader:
				self.trader.load_ship_states(savegame_db)
			if self.pirate:
				self.pirate.load_ship_states(savegame_db)

			# load the AI stuff only when we have AI players
			if any(isinstance(player, AIPlayer) for player in self.players):
				AIPlayer.load_abstract_buildings(self.session.db) # TODO: find a better place for this

			# load the AI players
			# this has to be done here because otherwise the ships and other objects won't exist
			for player in self.players:
				if not isinstance(player, HumanPlayer):
					player.finish_loading(savegame_db)

		self._load_combat(savegame_db)
		self._load_diplomacy(savegame_db)
		self._load_disasters(savegame_db)

		self.inited = True
		"""TUTORIAL:
		To dig deeper, you should now continue to horizons/world/island.py,
		to check out how buildings and settlements are added to the map."""



	def _load_combat(self, savegame_db):
		# load bullets
		if self.session.is_game_loaded():
			for (worldid, sx, sy, dx, dy, speed, img) in savegame_db("SELECT worldid, startx, starty, destx, desty, speed, image FROM bullet"):
				Bullet(img, Point(sx, sy), Point(dx, dy), speed, self.session, False, worldid)

		# load ongoing attacks
		if self.session.is_game_loaded():
			Weapon.load_attacks(self.session, savegame_db)

	def _load_diplomacy(self, savegame_db):
		self.diplomacy = Diplomacy()
		if self.session.is_game_loaded():
			self.diplomacy.load(self, savegame_db)

		# add diplomacy notification listeners
		def notify_change(caller, old_state, new_state, a, b):
			player1 = u"%s" % a.name
			player2 = u"%s" % b.name

			data = {'player1' : player1, 'player2' : player2}

			self.session.ingame_gui.message_widget.add(point=None,
                string_id='DIPLOMACY_STATUS_'+old_state.upper()+"_"+new_state.upper(), message_dict=data)

		self.diplomacy.add_diplomacy_status_changed_listener(notify_change)

	def _load_disasters(self, savegame_db):
		# disasters are only enabled if they are explicitly set to be enabled
		disasters_disabled = not ('disasters_enabled' in self.properties and
		                          self.properties['disasters_enabled'])
		self.disaster_manager = DisasterManager(self.session, disabled=disasters_disabled)
		if self.session.is_game_loaded():
			self.disaster_manager.load(savegame_db)

	def load_raw_map(self, savegame_db, preview=False):
		# load islands
		self.islands = []
		for (islandid,) in savegame_db("SELECT rowid + 1000 FROM island"):
			island = Island(savegame_db, islandid, self.session, preview=preview)
			self.islands.append(island)

		#calculate map dimensions
		self.min_x, self.min_y, self.max_x, self.max_y = 0, 0, 0, 0
		for i in self.islands:
			self.min_x = i.rect.left if self.min_x is None or i.rect.left < self.min_x else self.min_x
			self.min_y = i.rect.top if self.min_y is None or i.rect.top < self.min_y else self.min_y
			self.max_x = i.rect.right if self.max_x is None or i.rect.right > self.max_x else self.max_x
			self.max_y = i.rect.bottom if self.max_y is None or i.rect.bottom > self.max_y else self.max_y
		self.min_x -= 10
		self.min_y -= 10
		self.max_x += 10
		self.max_y += 10

		self.map_dimensions = Rect.init_from_borders(self.min_x, self.min_y, self.max_x, self.max_y)

		#add water
		self.log.debug("Filling world with water...")
		self.ground_map = {}

		# big sea water tile class
		if not preview:
			default_grounds = Entities.grounds[int(self.properties.get('default_ground', GROUND.WATER[0]))]

		# extra world size that is added so that the player can't see the "black void"
		border = 30
		fake_tile_class = Entities.grounds[-1]
		for x in xrange(self.min_x-border, self.max_x+border, 10):
			for y in xrange(self.min_y-border, self.max_y+border, 10):
				if not preview:
					# we don't need no references, we don't need no mem control
					default_grounds(self.session, x, y)
				for x_offset in xrange(0, 10):
					if x+x_offset < self.max_x and x+x_offset >= self.min_x:
						for y_offset in xrange(0, 10):
							if y+y_offset < self.max_y and y+y_offset >= self.min_y:
								self.ground_map[(x+x_offset, y+y_offset)] = fake_tile_class(self.session, x, y)

		# remove parts that are occupied by islands, create the island map and the full map
		self.island_map = {}
		self.full_map = copy.copy(self.ground_map)
		for island in self.islands:
			for coords in island.ground_map:
				if coords in self.ground_map:
					self.full_map[coords] = island.ground_map[coords]
					del self.ground_map[coords]
					self.island_map[coords] = island


	def _load_players(self, savegame_db, force_player_id):
		human_players = []
		for player_worldid, client_id in savegame_db("SELECT rowid, client_id FROM player WHERE is_trader = 0 and is_pirate = 0 ORDER BY rowid"):
			player = None
			# check if player is an ai
			ai_data = self.session.db("SELECT class_package, class_name FROM ai WHERE client_id = ?", client_id)
			if ai_data:
				class_package, class_name = ai_data[0]
				# import ai class and call load on it
				module = __import__('horizons.ai.'+class_package, fromlist=[str(class_name)])
				ai_class = getattr(module, class_name)
				player = ai_class.load(self.session, savegame_db, player_worldid)
			else: # no ai
				player = HumanPlayer.load(self.session, savegame_db, player_worldid)
			self.players.append(player)

			if client_id == horizons.main.fife.get_uh_setting("ClientID"):
				self.player = player
			elif client_id is not None and not ai_data:
				# possible human player candidate with different client id
				human_players.append(player)
		self.owner_highlight_active = False
		self.health_visible_for_all_health_instances = False

		if self.player is None:
			# we have no human player.
			# check if there is only one player with an id (i.e. human player)
			# this would be the case if the savegame originates from a different installation.
			# if there's more than one of this kind, we can't be sure what to select.
			# TODO: create interface for selecting player, if we want this
			if len(human_players) == 1:
				# exactly one player, we can quite safely use this one
				self.player = human_players[0]
			elif not human_players and self.players:
				# the first player should be the human-ai hybrid
				self.player = self.players[0]

		# set the human player to the forced value (debug option)
		self.set_forced_player(force_player_id)

		if self.player is None and self.session.is_game_loaded():
			self.log.warning('WARNING: Cannot autoselect a player because there are no \
			or multiple candidates.')

	def _init_water_bodies(self):
		"""This function runs the flood fill algorithm on the water to make it easy
		to recognise different water bodies."""
		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

		n = 0
		self.water_body = dict.fromkeys(self.water)
		for coords, num in self.water_body.iteritems():
			if num is not None:
				continue

			self.water_body[coords] = n
			queue = deque([coords])
			while queue:
				x, y = queue[0]
				queue.popleft()
				for dx, dy in moves:
					coords2 = (x + dx, y + dy)
					if coords2 in self.water_body and self.water_body[coords2] is None:
						self.water_body[coords2] = n
						queue.append(coords2)
			n += 1

	def init_fish_indexer(self):
		radius = Entities.buildings[ BUILDINGS.FISHER ].radius
		buildings = self.provider_buildings.provider_by_resources[RES.FISH]
		self.fish_indexer = BuildingIndexer(radius, self.full_map, buildings=buildings)

	def init_new_world(self, trader_enabled, pirate_enabled, natural_resource_multiplier):
		"""
		This should be called if a new map is loaded (not a savegame, a fresh
		map). In other words, when it is loaded for the first time.

		NOTE: commands for creating the world objects are executed directly,
		      bypassing the manager.
		      This is necessary because else the commands would be transmitted
		      over the wire in network games.

		@return: the coordinates of the players first ship
		"""

		# workaround: the creation of all the objects causes a lot of logging output we don't need.
		#             therefore, reset the levels for now
		loggers_to_silence = { 'world.production' : None }
		for logger_name in loggers_to_silence:
			logger = logging.getLogger(logger_name)
			loggers_to_silence[logger_name] = logger.getEffectiveLevel()
			logger.setLevel( logging.WARN )

		# add a random number of environmental objects
		if natural_resource_multiplier != 0:
			self._add_nature_objects(natural_resource_multiplier)

		# reset loggers, see above
		for logger_name, level in loggers_to_silence.iteritems():
			logging.getLogger(logger_name).setLevel(level)

		# add free trader
		if trader_enabled:
			self.trader = Trader(self.session, 99999, u"Free Trader", Color())

		ret_coords = None
		for player in self.players:
			# Adding ships for the players
			# hack to place the ship on the development map
			point = self.get_random_possible_ship_position()
			# Execute command directly, not via manager, because else it would be transmitted over the
			# network to other players. Those however will do the same thing anyways.
			ship = CreateUnit(player.worldid, UNITS.PLAYER_SHIP, point.x, point.y)(issuer=self.session.world.player)
			# give ship basic resources
			for res, amount in self.session.db("SELECT resource, amount FROM start_resources"):
				ship.get_component(StorageComponent).inventory.alter(res, amount)
			if player is self.player:
				ret_coords = point.to_tuple()

		# load the AI stuff only when we have AI players
		if any(isinstance(player, AIPlayer) for player in self.players):
			AIPlayer.load_abstract_buildings(self.session.db) # TODO: find a better place for this

		# add a pirate ship
		if pirate_enabled:
			self.pirate = Pirate(self.session, 99998, "Captain Blackbeard", Color())

		# Fire a message for new world creation
		self.session.ingame_gui.message_widget.add(point=None, string_id='NEW_WORLD')
		assert ret_coords is not None, "Return coords are None. No players loaded?"
		return ret_coords

	def _add_nature_objects(self, natural_resource_multiplier):
		worldutils.add_nature_objects(self, natural_resource_multiplier)

	def set_forced_player(self, force_player_id):
		if force_player_id is not None:
			for player in self.players:
				if player.worldid == force_player_id:
					self.player = player
					break

	def get_random_possible_ground_unit_position(self):
		"""Returns a position in water that is not at the border of the world.
		@return: Point"""
		return worldutils.get_random_possible_ground_unit_position(self)

	def get_random_possible_ship_position(self):
		"""Returns a position in water that is not at the border of the world.
		@return: Point"""
		return worldutils.get_random_possible_ship_position(self)

	def get_random_possible_coastal_ship_position(self):
		"""Returns a position in water that is not at the border of the world
		but on the coast of an island.
		@return: Point"""
		return worldutils.get_random_possible_coastal_ship_position(self)

	#----------------------------------------------------------------------
	def get_tiles_in_radius(self, position, radius, shuffle=False):
		"""Returns all tiles in the radius around the point.
		This is a generator; make sure you use it appropriately.
		@param position: Point instance
		@return List of tiles in radius.
		"""
		for point in self.get_points_in_radius(position, radius, shuffle):
			yield self.get_tile(point)

	def get_points_in_radius(self, position, radius, shuffle=False):
		"""Returns all points in the radius around the point.
		This is a generator; make sure you use it appropriately.
		@param position: Point instance
		@return List of points in radius.
		"""
		assert isinstance(position, Point)
		points = Circle(position, radius)
		if shuffle:
			points = list(points)
			self.session.random.shuffle(points)
		for point in points:
			if self.map_dimensions.contains_without_border(point):
				# don't yield if point is not in map, those points don't exist
				yield point

	def setup_player(self, id, name, color, clientid, local, is_ai, difficulty_level):
		"""Sets up a new Player instance and adds her to the active world.
		Only used for new games. Loading old players is done in _init().
		@param local: bool, whether the player is the one sitting on front of this machine."""
		inv = self.session.db.get_player_start_res()
		player = None
		if is_ai: # a human controlled AI player
			player = AIPlayer(self.session, id, name, color, clientid, difficulty_level)
		else:
			player = HumanPlayer(self.session, id, name, color, clientid, difficulty_level)
		player.initialize(inv)  # Componentholder init
		if local:
			self.player = player
		self.players.append(player)

	def get_tile(self, point):
		"""Returns the ground at x, y.
		@param point: coords as Point
		@return: instance of Ground at x, y
		"""
		return self.full_map.get( (point.x, point.y) )

	@property
	def settlements(self):
		"""Returns all settlements on world"""
		settlements = []
		for i in self.islands:
			settlements.extend(i.settlements)
		return settlements

	def get_island(self, point):
		"""Returns the island for that coordinate. If none is found, returns None.
		@param point: instance of Point"""
		# NOTE: keep code synchronised with duplicated code below
		return self.island_map.get(point.to_tuple())

	def get_island_tuple(self, tup):
		"""Overloaded from above"""
		return self.island_map.get(tup)

	def get_islands_in_radius(self, point, radius):
		"""Returns all islands in a certain radius around a point.
		@return set of islands in radius"""
		islands = set()
		for island in self.islands:
			for tile in island.get_surrounding_tiles(point, radius):
				islands.add(island)
				break
		return islands

	def get_warehouses(self, position=None, radius=None, owner=None, include_tradeable=False):
		"""Returns all warehouses on the map, optionally only those in range
		around the specified position.
		@param position: Point or Rect instance.
		@param radius: int radius to use.
		@param owner: Player instance, list only warehouses belonging to this player.
		@param include_tradeable also list the warehouses the owner can trade with
		@return: List of warehouses.
		"""
		warehouses = []
		islands = []
		if radius is not None and position is not None:
			islands = self.get_islands_in_radius(position, radius)
		else:
			islands = self.islands

		for island in islands:
			for settlement in island.settlements:
				warehouse = settlement.warehouse
				if (radius is None or position is None or
				    warehouse.position.distance(position) <= radius) and \
				   (owner is None or warehouse.owner == owner or
				    (include_tradeable and self.diplomacy.can_trade(warehouse.owner, owner))):
					warehouses.append(warehouse)
		return warehouses

	def get_ships(self, position=None, radius=None):
		"""Returns all ships on the map, optionally only those in range
		around the specified position.
		@param position: Point or Rect instance.
		@param radius: int radius to use.
		@return: List of ships.
		"""
		if position is not None and radius is not None:
			circle = Circle(position, radius)
			ships = []
			for ship in self.ships:
				if circle.contains(ship.position):
					ships.append(ship)
			return ships
		else:
			return self.ships

	def get_ground_units(self, position=None, radius=None):
		"""@see get_ships"""
		if position is not None and radius is not None:
			circle = Circle(position, radius)
			units = []
			for unit in self.ground_units:
				if circle.contains(unit.position):
					units.append(unit)
			return units
		else:
			return self.ground_units

	def get_buildings(self, position=None, radius=None):
		"""@see get_ships"""
		buildings = []
		if position is not None and radius is not None:
			circle = Circle(position, radius)
			for island in self.islands:
				for building in island.buildings:
					if circle.contains(building.position.center()):
						buildings.append(building)
		else:
			for island in self.islands:
				for building in island.buildings:
					buildings.append(building)
		return buildings

	def get_all_buildings(self):
		"""Yields all buildings independent of owner"""
		for island in self.islands:
			for b in island.buildings:
				yield b
			for s in island.settlements:
				for b in s.buildings:
					yield b

	def get_health_instances(self, position=None, radius=None):
		"""Returns all instances that have health"""
		instances = []
		for instance in self.get_ships(position, radius)+\
				self.get_ground_units(position, radius):
			if instance.has_component(HealthComponent):
				instances.append(instance)
		return instances

	def save(self, db):
		"""Saves the current game to the specified db.
		@param db: DbReader object of the db the game is saved to."""
		super(World, self).save(db)
		for name, value in self.properties.iteritems():
			db("INSERT INTO map_properties (name, value) VALUES (?, ?)", name, json.dumps(value))
		for island in self.islands:
			island.save(db)
		for player in self.players:
			player.save(db)
		if self.trader is not None:
			self.trader.save(db)
		if self.pirate is not None:
			self.pirate.save(db)
		for ship in self.ships:
			ship.save(db)
		for ground_unit in self.ground_units:
			ground_unit.save(db)
		for bullet in self.bullets:
			bullet.save(db)
		self.diplomacy.save(db)
		Weapon.save_attacks(db)
		self.disaster_manager.save(db)

	def save_map(self, path, prefix):
		"""Save the current map as map file + island files"""
		worldutils.save_map(self, path, prefix)

	def get_checkup_hash(self):
		"""Returns a collection of important game state values. Used to check if two mp games have diverged.
		Not designed to be reliable."""
		# NOTE: don't include float values, they are represented differently in python 2.6 and 2.7
		# and will differ at some insignificant place. Also make sure to handle them correctly in the game logic.
		data = {
			'rngvalue': self.session.random.random(),
			'settlements': [],
			'ships': [],
		}
		for island in self.islands:
			# dicts usually aren't hashable, this makes them
			# since defaultdicts appear, we discard values that can be autogenerated
			# (those are assumed to default to something evaluating False)
			dict_hash = lambda d : sorted( i for i in d.iteritems() if i[1] )
			for settlement in island.settlements:
				storage_dict =settlement.get_component(StorageComponent).inventory._storage
				entry = {
					'owner': str(settlement.owner.worldid),
					'inhabitants': str(settlement.inhabitants),
					'cumulative_running_costs': str(settlement.cumulative_running_costs),
					'cumulative_taxes': str(settlement.cumulative_taxes),
					'inventory': str( dict_hash(storage_dict) )
				}
				data['settlements'].append(entry)
		for ship in self.ships:
			entry = {
				'owner': str(ship.owner.worldid),
				'position': ship.position.to_tuple(),
			}
			data['ships'].append(entry)
		return data

	def toggle_owner_highlight(self):
		renderer = self.session.view.renderer['InstanceRenderer']
		self.owner_highlight_active = not self.owner_highlight_active
		if self.owner_highlight_active: #show
			for player in self.players:
				red = player.color.r
				green = player.color.g
				blue = player.color.b
				for settlement in player.settlements:
					for tile in settlement.ground_map.itervalues():
						renderer.addColored(tile._instance, red, green, blue)
		else: # 'hide' functionality
			renderer.removeAllColored()

	def toggle_translucency(self):
		"""Make certain building types translucent"""
		worldutils.toggle_translucency(self)

	def toggle_health_for_all_health_instances(self):
		worldutils.toggle_health_for_all_health_instances(self)


def load_building(session, db, typeid, worldid):
	"""Loads a saved building. Don't load buildings yourself in the game code."""
	return Entities.buildings[typeid].load(session, db, worldid)


decorators.bind_all(World)
decorators.bind_all(load_building)
