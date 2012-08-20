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
import collections

import logging
from horizons.ai.aiplayer.combat.unitmanager import UnitManager

from horizons.ai.aiplayer.strategy.mission.chaseshipsandattack import ChaseShipsAndAttack
from horizons.ai.aiplayer.strategy.mission.pirateroutine import PirateRoutine
from horizons.ai.aiplayer.strategy.mission.scouting import ScoutingMission
from horizons.ai.aiplayer.strategy.mission.surpriseattack import SurpriseAttack
from horizons.component.healthcomponent import HealthComponent
from horizons.component.namedcomponent import NamedComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import RES
from horizons.util.python import trim_value, map_balance
from horizons.util.worldobject import WorldObject
from horizons.world.player import Player


class StrategyManager(object):
	"""
	StrategyManager object is responsible for handling major decisions in game such as
	sending fleets to battle, keeping track of diplomacy between players, declare wars.
	"""
	log = logging.getLogger("ai.aiplayer.fleetmission")

	def __init__(self, owner):
		super(StrategyManager, self).__init__()
		self.__init(owner)

	def __init(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.unit_manager = owner.unit_manager
		self.missions = set()

		# Dictionary of Condition_hash => FleetMission. Condition_hash is a key since it's searched for more often. Values are
		# unique because of WorldObject's inheritance, but it makes removing items from it in O(n).
		self.conditions_being_resolved = {}

		self.missions_to_load = {
			ScoutingMission: "ai_scouting_mission",
			SurpriseAttack: "ai_mission_surprise_attack",
			ChaseShipsAndAttack: "ai_mission_chase_ships_and_attack",
		}

	@property
	def conditions(self):
		# conditions are held in behavior manager since they are a part of behavior profile (just like actions and strategies)
		return self.owner.behavior_manager.get_conditions()

	def calculate_player_wealth_balance(self, other_player):
		"""
		Calculates wealth balance between two players.
		Wealth balance of 1.2 means that self.owner is 1.2 times wealthier than other_player.
		@param other_player: other player matched against self.owner
		@type other_player: Player
		"""

		gold_weight = 0.25 # we don't value gold that much
		resources_weight = 0.75

		resource_values = []
		for player in [self.owner, other_player]:
			resources_value = 0.0
			for settlement in player.settlements:
				resources_value += sum((self.session.db.get_res_value(resource) * amount for resource, amount\
					in settlement.get_component(StorageComponent).inventory.itercontents() if self.session.db.get_res_value(resource)))
			resource_values.append(resources_value)
		ai_resources, enemy_resources = resource_values

		ai_gold = self.owner.get_component(StorageComponent).inventory[RES.GOLD]
		enemy_gold = other_player.get_component(StorageComponent).inventory[RES.GOLD]
		return (ai_resources * resources_weight + ai_gold * gold_weight) / (enemy_resources * resources_weight + enemy_gold * gold_weight)

	def calculate_player_power_balance(self, other_player):
		"""
		Calculates power balance between two players.
		Power balance of 1.2 means that self.owner is 1.2 times stronger than other_player

		@param other_player: other player who is matched against self.owner
		@type other_player: Player
		@return: power balance between self.owner and other_player
		@rtype: float
		"""

		min_balance = 10e-7
		max_balance = 1000.0

		ships = self.owner.ships.keys()
		ships = self.unit_manager.filter_ships(ships, (self.unit_manager.filtering_rules.fighting(),))
		enemy_ships = self.unit_manager.get_player_ships(other_player)
		enemy_ships = self.unit_manager.filter_ships(enemy_ships, (self.unit_manager.filtering_rules.fighting(),))

		# infinitely more powerful
		if len(ships) and not len(enemy_ships):
			return max_balance

		# infinitely less powerful
		elif not len(ships) and len(enemy_ships):
			return min_balance
		elif not len(ships) and not len(enemy_ships):
			return 1.0

		return UnitManager.calculate_power_balance(ships, enemy_ships)

	def calculate_player_terrain_balance(self, other_player):
		"""
		Calculates balance between sizes of terrain, i.e. size on map.
		Terrain balance of 1.2 means that self.owner has 1.2 times larger terrain than other_player
		"""

		min_balance = 10e-7
		max_balance = 1000.0

		terrains = []
		island_counts = []
		for player in [self.owner, other_player]:
			terrain_total = 0
			islands = set()
			for settlement in player.settlements:
				terrain_total += len(settlement.ground_map)
				islands.add(settlement.island)
			terrains.append(terrain_total)
			island_counts.append(len(islands))

		ai_terrain, enemy_terrain = terrains
		ai_islands, enemy_islands = island_counts

		# if not
		if ai_islands and not enemy_islands:
			return max_balance
		if not ai_islands and enemy_islands:
			return min_balance
		if not ai_islands and not enemy_islands:
			return 1.0

		island_count_balance = float(ai_islands) / float(enemy_islands)

		# it favors having 3 islands of total size X, than 2 of total size X (or bigger)
		return (float(ai_terrain) / float(enemy_terrain)) * island_count_balance

	def calculate_player_balance(self, player, trimming_factor=10.0, linear_boundary=10.0):
		"""
		Calculate power balance between self.owner and other player.

		trimming_factor: Since any balance returns values of (0, inf) we agree to assume if x < 0.1 -> x = 0.1 and if x > 10.0 -> x=10.0
		linear_boundary: boundary of [-10.0, 10.0] for new balance scale

		@param player: player to calculate balance against
		@type player: Player
		@param trimming_factor: trim actual balance values to range [1./trimming_factor, trimming_factor] e.g. [0.1, 10.0]
		@type trimming_factor: float
		@param linear_boundary: boundaries of new balance scale [-linear_boundary, linear_boundary], e.g. [-10.0, 10.0]
		@type linear_boundary: float
		@return: unified balance for various variables
		@rtype: collections.namedtuple
		"""
		wealth_balance = self.owner.strategy_manager.calculate_player_wealth_balance(player)
		power_balance = self.owner.strategy_manager.calculate_player_power_balance(player)
		terrain_balance = self.owner.strategy_manager.calculate_player_terrain_balance(player)
		balance = {
			'wealth':wealth_balance,
			'power':power_balance,
			'terrain':terrain_balance,
		}
		balance = dict(( (key, trim_value(value, 1./trimming_factor, trimming_factor)) for key, value in balance.iteritems()))
		balance = dict(( (key, map_balance(value, trimming_factor, linear_boundary)) for key, value in balance.iteritems()))

		return collections.namedtuple('Balance', 'wealth, power, terrain')(**balance)

	def save(self, db):
		for mission in list(self.missions):
			mission.save(db)

		for condition, mission in self.conditions_being_resolved.iteritems():
			db("INSERT INTO ai_condition_lock (owner_id, condition, mission_id) VALUES(?, ?, ?)", self.owner.worldid, condition, mission.worldid)

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls)
		super(StrategyManager, self).__init__()
		self.__init(owner)
		self._load(db)
		return self

	def _load(self, db):
		for class_name, db_table in self.missions_to_load.iteritems():
			db_result = db("SELECT m.rowid FROM %s m, ai_fleet_mission f WHERE f.owner_id = ? and m.rowid = f.rowid" % db_table, self.owner.worldid)
			for (mission_id,) in db_result:
				self.missions.add(class_name.load(mission_id, self.owner, db, self.report_success, self.report_failure))

		# load condition locks
		db_result = db("SELECT condition, mission_id FROM ai_condition_lock WHERE owner_id = ?", self.owner.worldid)
		for (condition, mission_id) in db_result:
			self.conditions_being_resolved[condition] = WorldObject.get_object_by_id(mission_id)

	def report_success(self, mission, msg):
		self.log.info("Player: %s|StrategyManager|Mission %s was a success: %s", self.owner.worldid, mission, msg)
		self.end_mission(mission)

	def report_failure(self, mission, msg):
		self.log.info("Player: %s|StrategyManager|Mission %s was a failure: %s", self.owner.worldid, mission, msg)
		self.end_mission(mission)

	def end_mission(self, mission):
		self.log.info("Player: %s|StrategyManager|Mission %s ended", self.owner.worldid, mission)
		if mission in self.missions:
			self.missions.remove(mission)

		# remove condition lock (if condition was lockable) after mission ends
		self.unlock_condition(mission)

	def start_mission(self, mission):
		self.log.info("Player: %s|StrategyManager|Mission %s started", self.owner.worldid, mission)
		self.missions.add(mission)
		mission.start()

	def lock_condition(self, condition, mission):
		self.conditions_being_resolved[condition] = mission

	def unlock_condition(self, mission):
		# values (FleetMission) are unique so it's possible to remove them this way:
		for condition, value in self.conditions_being_resolved.iteritems():
			if mission == value:
				del self.conditions_being_resolved[condition]
				return

	def get_missions(self, condition=None):
		"""
		Get missions filtered by certain condition (by default return all missions)
		"""
		if condition:
			return [mission for mission in self.missions if condition(mission)]
		else:
			return self.missions

	def request_to_pause_mission(self, mission, **environment):
		"""
		@return: returns True is mission is allowed to pause, False otherwise
		@rtype: bool
		"""
		# TODO: make that decision based on environment (**environment as argument)
		mission.pause_mission()
		return True

	def get_ships_for_mission(self):
		filters = self.unit_manager.filtering_rules
		rules = (filters.ship_state(self.owner.ships, (self.owner.shipStates.idle,)), filters.fighting(), filters.not_in_fleet())
		idle_ships = self.unit_manager.get_ships(rules)

		return idle_ships

	def handle_strategy(self):

		# Get all available ships that can take part in a mission
		idle_ships = self.get_ships_for_mission()

		# Get all other players
		other_players = [player for player in self.session.world.players if player != self.owner]

		# Check which conditions occur
		occuring_conditions = []

		environment = {'idle_ships': idle_ships}

		for player in other_players:
			# Prepare environment
			self.log.debug("Conditions occuring against player %s", player.name)
			environment['player'] = player

			for condition in self.conditions.keys():

				# Check whether given condition is already being resolved
				if condition.get_identifier(**environment) in self.conditions_being_resolved:
					self.log.debug("  %s: Locked", condition.__class__.__name__)
					continue

				condition_outcome = condition.check(**environment)
				self.log.debug("  %s: %s", condition.__class__.__name__, ("Yes" if condition_outcome else "No"))
				if condition_outcome:
					occuring_conditions.append((condition, condition_outcome))

			# Revert environment to previous state
			del environment['player']

		# Nothing to do when none of the conditions occur
		if occuring_conditions:
			# Choose the most important one

			selected_condition, selected_outcome = max(occuring_conditions,
				key=lambda (condition, outcome): self.conditions[condition] * outcome['certainty'])

			self.log.debug("Selected condition: %s", selected_condition.__class__.__name__)
			for key, value in selected_outcome.iteritems():
				# Insert condition-gathered info into environment
				environment[key] = value
				self.log.debug(" %s: %s", key, value)

			# Try to execute a mission that resolves given condition the best
			mission = self.owner.behavior_manager.request_strategy(**environment)
			if mission:
				self.start_mission(mission)
				if selected_condition.lockable:
					self.lock_condition(selected_condition.get_identifier(**environment), mission)

		self.log.debug("Missions:")
		for mission in list(self.missions):
			self.log.debug("%s", mission)

		self.log.debug("Fleets:")
		for fleet in list(self.unit_manager.fleets):
			self.log.debug("%s", fleet)

	def tick(self):
		self.handle_strategy()


class PirateStrategyManager(StrategyManager):

	def __init__(self, owner):
		super(PirateStrategyManager, self).__init__(owner)
		self.__init(owner)

	def get_ships_for_mission(self):
		filters = self.unit_manager.filtering_rules
		rules = (filters.ship_state(self.owner.ships, (self.owner.shipStates.idle,)), filters.pirate(), filters.not_in_fleet())
		idle_ships = self.unit_manager.get_ships(rules)

		return idle_ships

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls)
		super(PirateStrategyManager, self).__init__(owner)
		self.__init(owner)
		self._load(db)
		return self

	def __init(self, owner):
		self.missions_to_load = {
			PirateRoutine: "ai_mission_pirate_routine",
		}
