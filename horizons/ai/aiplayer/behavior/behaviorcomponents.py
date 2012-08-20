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
from collections import defaultdict
from horizons.ai.aiplayer.behavior.movecallbacks import BehaviorMoveCallback
from horizons.ai.aiplayer.combat.combatmanager import CombatManager
from horizons.ai.aiplayer.strategy.mission.chaseshipsandattack import ChaseShipsAndAttack
from horizons.ai.aiplayer.strategy.mission.pirateroutine import PirateRoutine
from horizons.ai.aiplayer.strategy.mission.scouting import ScoutingMission
from horizons.ai.aiplayer.strategy.mission.surpriseattack import SurpriseAttack
from horizons.ai.aiplayer.combat.unitmanager import UnitManager
from horizons.command.diplomacy import AddEnemyPair

import logging
from horizons.component.namedcomponent import NamedComponent
from horizons.constants import BUILDINGS
from horizons.ext.enum import Enum
from horizons.util.python import trim_value, map_balance
from horizons.util.python.callback import Callback
from horizons.util.shapes.circle import Circle
from horizons.util.shapes.point import Point
from horizons.world.units.movingobject import MoveNotPossible


class BehaviorComponent(object):
	"""
	This is an abstract BehaviorComponent - a building block for AI Behavior.
	"""
	log = logging.getLogger('ai.aiplayer.behavior.behaviorcomponents')
	default_certainty = 1.0
	minimal_fleet_size = 1

	def __init__(self, owner):
		self.owner = owner
		self.combat_manager = owner.combat_manager
		self.unit_manager = owner.unit_manager
		self.world = owner.world
		self.session = owner.session

		# Witchery below is a way to have certainty() always return the same certainty if it's not defined per behavior.
		self._certainty = defaultdict(lambda: (lambda **env: self.default_certainty))

	def certainty(self, action_name, **environment):
		certainty = self._certainty[action_name](**environment)
		assert certainty is not None, "Certainty function returned None instead of a float. Certainty in %s for %s" % (self.__class__.__name__, action_name)
		return certainty

	# common certainties used by various behaviors
	def _certainty_has_boat_builder(self, **environment):
		if self.owner.count_buildings(BUILDINGS.BOAT_BUILDER):
			return self.default_certainty
		else:
			return 0.0

	def _certainty_has_fleet(self, **environment):
		idle_ships = environment['idle_ships']
		if idle_ships:
			return self.default_certainty
		else:
			return 0.0

# Components below are roughly divided into "Aggressive, Normal,Cautious" etc.
# (division below is not related to the way dictionaries in BehaviorManager are named (offensive, idle, defensive))


class BehaviorDoNothing(BehaviorComponent):
	"""
	Behavior that does nothing. Used mainly for idle actions (we don't want to scout too often).
	"""

	def __init__(self, owner):
		super(BehaviorDoNothing, self).__init__(owner)

	def no_one_in_sight(self, **environment):
		pass


class BehaviorPirateRoutine(BehaviorComponent):
	"""
	Idle behavior for Pirate player. It has to be specialized for Pirate since general AI does not have home_point.
	Responsible for pirate ships routine when no one is around. States change in a loop:
	idle -> moving_random -> going_home -> idle
	"""

	sail_home_chance = 0.3  # sail_home_chance to sail home, 1-sail_home_chance to sail randomly
	pirate_caught_ship_radius = 5
	pirate_home_radius = 2

	def __init__(self, owner):
		super(BehaviorPirateRoutine, self).__init__(owner)

	def no_one_in_sight(self, **environment):
		"""
		Idle action, sail randomly when no ship was spotted nearby.
		"""
		ship_group = environment['ship_group']
		for ship in ship_group:
			rand_val = self.session.random.random()
			if self.owner.ships[ship] == self.owner.shipStates.idle:
				if rand_val < self.sail_home_chance:
					self._sail_home(ship)
				else:
					self._sail_random(ship)

			self.log.debug('BehaviorPirateRoutine: Ship:%s no_one_in_sight' % ship.get_component(NamedComponent).name)

	def trading_ships_in_sight(self, **environment):
		ship_group = environment['ship_group']
		for ship in ship_group:
			self._chase_closest_ship(ship)
			self.log.debug('BehaviorPirateRoutine: Ship:%s trading_ships_in_sight' % ship.get_component(NamedComponent).name)

	def _arrived(self, ship):
		"""
		Callback function executed once ship arrives at the destination after certain action.
		Practically only changes ship state to idle.
		"""
		owner = ship.owner
		self.log.debug('Player %s: Ship %s: arrived at destination after "%s"' % (owner.name,
			ship.get_component(NamedComponent).name, owner.ships[ship]))
		owner.ships[ship] = owner.shipStates.idle

	def _chase_closest_ship(self, pirate_ship):
		owner = pirate_ship.owner
		ship = owner.get_nearest_player_ship(pirate_ship)
		if ship:
			owner.ships[pirate_ship] = owner.shipStates.chasing_ship

			# if ship was caught
			if ship.position.distance(pirate_ship.position) <= self.pirate_caught_ship_radius:
				self.log.debug('Pirate %s: Ship %s(%s) caught %s' % (owner.worldid,
					pirate_ship.get_component(NamedComponent).name, owner.ships[pirate_ship], ship))
				self._sail_home(pirate_ship)
			else:
				try:
					pirate_ship.move(Circle(ship.position, self.pirate_caught_ship_radius - 1), Callback(self._sail_home, pirate_ship))
					owner.ships[pirate_ship] = owner.shipStates.chasing_ship
					self.log.debug('Pirate %s: Ship %s(%s) chasing %s' % (owner.worldid,
						pirate_ship.get_component(NamedComponent).name, owner.ships[pirate_ship], ship.get_component(NamedComponent).name))
				except MoveNotPossible:
					self.log.debug('Pirate %s: Ship %s(%s) unable to chase the closest ship %s' % (owner.worldid,
						pirate_ship.get_component(NamedComponent).name, owner.ships[pirate_ship], ship.get_component(NamedComponent).name))
					owner.ships[pirate_ship] = owner.shipStates.idle

	def _sail_home(self, pirate_ship):
		owner = pirate_ship.owner
		try:
			pirate_ship.move(Circle(owner.home_point, self.pirate_home_radius), Callback(self._arrived, pirate_ship))
			owner.ships[pirate_ship] = owner.shipStates.going_home
			self.log.debug('Pirate %s: Ship %s(%s): sailing home at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name,
				owner.ships[pirate_ship], owner.home_point))
		except MoveNotPossible:
			owner.ships[pirate_ship] = owner.shipStates.idle
			self.log.debug('Pirate %s: Ship %s: unable to move home at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name, owner.home_point))

	def _sail_random(self, pirate_ship):

		owner = pirate_ship.owner
		session = owner.session
		point = session.world.get_random_possible_ship_position()
		try:
			pirate_ship.move(point, Callback(self._arrived, pirate_ship))
			owner.ships[pirate_ship] = owner.shipStates.moving_random
			self.log.debug('Pirate %s: Ship %s(%s): moving random at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name,
				owner.ships[pirate_ship], point))
		except MoveNotPossible:
			owner.ships[pirate_ship] = owner.shipStates.idle
			self.log.debug('Pirate %s: Ship %s: unable to move random at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name, point))

# Common certainty functions for offensive actions
def certainty_power_balance_exp(**environment):
	"""
	Return power_balance^2, altering the exponent will impact the weight certainty has.
	"""
	return BehaviorComponent.default_certainty * (environment['power_balance'] ** 2)


def certainty_power_balance_inverse(**environment):
	"""
	Return power_balance reciprocal,
	"""

	return BehaviorComponent.default_certainty * (1. / environment['power_balance'])


class BehaviorRegular(BehaviorComponent):
	"""
	A well-balanced way to respond to situations in game.
	"""
	power_balance_threshold = 1.0

	def __init__(self, owner):
		super(BehaviorRegular, self).__init__(owner)
		self._certainty['pirate_ships_in_sight'] = certainty_power_balance_exp
		self._certainty['fighting_ships_in_sight'] = certainty_power_balance_exp
		self._certainty['player_shares_island'] = self._certainty_player_shares_island
		self._certainty['hostile_player'] = self._certainty_hostile_player
		self._certainty['debug'] = self._certainty_ship_amount

	def pirate_ships_in_sight(self, **environment):
		"""
		Attacks pirates only if they are enemies already and the power balance is advantageous.
		"""
		pirates = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = environment['power_balance']

		# It's enough to check if first pirate is hostile, since there is only one pirate player.
		if self.session.world.diplomacy.are_enemies(self.owner, pirates[0].owner):
			# Let each ship attack it's closest enemy to maximize dps (in a way)
			ship_pairs = UnitManager.get_closest_ships_for_each(ship_group, pirates)
			for ship, pirate in ship_pairs:
				ship.attack(pirates[0])
			BehaviorComponent.log.info('%s: Attacked pirate ship', self.__class__.__name__)
		else:
			BehaviorComponent.log.info('%s: Pirate ship was not hostile', self.__class__.__name__)

	def fighting_ships_in_sight(self, **environment):
		"""
		Attacks frigates only if they are enemies already and the power balance is advantageous.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = environment['power_balance']

		if power_balance > self.power_balance_threshold:
			BehaviorComponent.log.info('%s: Enemy group is too strong', self.__class__.__name__)
			return

		if self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			ship_pairs = UnitManager.get_closest_ships_for_each(ship_group, enemies)
			for ship, enemy_ship in ship_pairs:
				ship.attack(enemy_ship)

			BehaviorComponent.log.info('%s: Attacked enemy ship', self.__class__.__name__)
		else:
			BehaviorComponent.log.info('%s: Enemy ship was not hostile', self.__class__.__name__)

	def working_ships_in_sight(self, **environment):
		"""
		Attacks working ships only if they are hostile.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']

		if self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			for ship in ship_group:
				ship.attack(enemies[0])
			BehaviorComponent.log.info('%s: Attacked enemy ship', self.__class__.__name__)
		else:
			BehaviorComponent.log.info('%s: Enemy worker was not hostile', self.__class__.__name__)

	def _certainty_player_shares_island(self, **environment):
		"""
		Dummy certainty that checks for a fleets size only.
		"""
		idle_ships = environment['idle_ships']

		if len(idle_ships) < self.minimal_fleet_size:
			return 0.0

		return self.default_certainty

	def _certainty_ship_amount(self, **environment):
		idle_ships = environment['idle_ships']

		if len(idle_ships) < self.minimal_fleet_size:
			return 0.0
		else:
			return self.default_certainty

	def _certainty_hostile_player(self, **environment):
		enemy_player = environment['player']
		idle_ships = environment['idle_ships']

		enemy_ships = self.unit_manager.get_player_ships(enemy_player)

		if not enemy_ships or len(idle_ships) < self.minimal_fleet_size:
			return 0.0

		return self.default_certainty

	def player_shares_island(self, **environment):
		"""
		Response to player that shares an island with AI player.
		Regular AI should simply attack given player.
		"""
		enemy_player = environment['player']
		idle_ships = environment['idle_ships']

		if not enemy_player.settlements:
			return None

		target_point = self.unit_manager.get_warehouse_area(enemy_player.settlements[0], 13)

		return_point = idle_ships[0].position.copy()
		mission = SurpriseAttack.create(self.owner.strategy_manager.report_success,
			self.owner.strategy_manager.report_failure, idle_ships, target_point, return_point, enemy_player)
		return mission

	def hostile_player(self, **environment):
		"""
		Arrage an attack for hostile ships.
		"""
		enemy_player = environment['player']
		idle_ships = environment['idle_ships']
		enemy_ships = self.unit_manager.get_player_ships(enemy_player)

		# TODO: pick target ship better
		target_ship = enemy_ships[0]
		mission = ChaseShipsAndAttack.create(self.owner.strategy_manager.report_success,
			self.owner.strategy_manager.report_failure, idle_ships, target_ship)

		return mission

	def neutral_player(self, **environment):
		"""
		Not concerned about neutral players.
		"""
		return None


class BehaviorAggressive(BehaviorComponent):

	power_balance_threshold = 0.8 # allow to attack targets that are slightly stronger

	def __init__(self, owner):
		super(BehaviorAggressive, self).__init__(owner)
		self._certainty['neutral_player'] = self._certainty_neutral_player
		self._certainty['fighting_ships_in_sight'] = self._certainty_fighting_ships_in_sight

	def _certainty_fighting_ships_in_sight(self, **environment):
		return self.default_certainty

	def fighting_ships_in_sight(self, **environment):
		"""
		Attacks frigates only if they are enemies already and the power balance is advantageous.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = environment['power_balance']

		if power_balance < self.power_balance_threshold:
			BehaviorComponent.log.info('%s: Enemy group is too strong', self.__class__.__name__)
			return

		# attack ship with the lowest HP
		target_ship = UnitManager.get_lowest_hp_ship(enemies)

		if self.session.world.diplomacy.are_enemies(self.owner, target_ship.owner):
			for ship in ship_group:
				ship.attack(target_ship)
			BehaviorComponent.log.info('%s: Attacked enemy ship', self.__class__.__name__)
		else:
			BehaviorComponent.log.info('%s: Enemy ship was not hostile', self.__class__.__name__)

	def _certainty_neutral_player(self, **environment):
		idle_ships = environment['idle_ships']

		if len(idle_ships) >= self.minimal_fleet_size:
			return self.default_certainty
		elif self.owner.count_buildings(BUILDINGS.BOAT_BUILDER):
			return self.default_certainty
		else:
			return 0.0

	def neutral_player(self, **environment):
		"""
		Start war with neutral player
		-make a SurpriseAttack if possible.
		-break diplomacy otherwise.
		"""
		idle_ships = environment['idle_ships']
		enemy_player = environment['player']

		# Nothing to do when AI or enemy don't have a settlement yet
		if not enemy_player.settlements or not self.owner.settlements:
			return None

		# Send a surprise attack if there are ships available, otherwise simply declare war
		if idle_ships:
			target_point = self.unit_manager.get_warehouse_area(enemy_player.settlements[0])
			return_point = self.unit_manager.get_warehouse_area(self.owner.settlements[0], 15)
			mission = SurpriseAttack.create(self.owner.strategy_manager.report_success,
				self.owner.strategy_manager.report_failure, idle_ships, target_point, return_point, enemy_player)
			return mission
		else:
			AddEnemyPair(self.owner, enemy_player).execute(self.session)


class BehaviorCautious(BehaviorComponent):

	def __init__(self, owner):
		super(BehaviorCautious, self).__init__(owner)

	def neutral_player(self, **environment):
		"""
		Not concerned about neutral players.
		"""
		return None


class BehaviorSmart(BehaviorComponent):

	def fighting_ships_in_sight(self, **environment):
		"""
		Attacks frigates, and keeps distance based on power balance.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = environment['power_balance']

		if power_balance >= 1.0:
			range_function = CombatManager.close_range
		else:
			range_function = CombatManager.fallback_range

		ship_pairs = UnitManager.get_closest_ships_for_each(ship_group, enemies)
		for ship, enemy_ship in ship_pairs:
			if self.session.world.diplomacy.are_enemies(ship.owner, enemy_ship.owner):
				BehaviorMoveCallback.maintain_distance_and_attack(ship, enemy_ship, range_function(ship))
				BehaviorComponent.log.info('%s: Attack: %s -> %s', self.__class__.__name__,
					ship.get_component(NamedComponent).name, enemy_ship.get_component(NamedComponent).name)
			else:
				BehaviorComponent.log.info('%s: Enemy ship %s was not hostile', self.__class__.__name__,
					ship.get_component(NamedComponent).name)

	def working_ships_in_sight(self, **environment):
		"""
		Attacks working ships only if they are hostile.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']

		if self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			# working ships won't respond with fire, each ship should attack the closest one, and chase them if necessary.
			ship_pairs = UnitManager.get_closest_ships_for_each(ship_group, enemies)
			for ship, enemy_ship in ship_pairs:
				range_function = CombatManager.close_range
				BehaviorMoveCallback.maintain_distance_and_attack(ship, enemy_ship, range_function(ship))
			BehaviorComponent.log.info('%s: Attacked enemy ship', self.__class__.__name__)
		else:
			BehaviorComponent.log.info('%s: Enemy worker was not hostile', self.__class__.__name__)


# Behaviors calculate single value against each of the players (you can think of it as of respect, or "relationship_score" values towards other player)
# Each AI values different traits in others. Based on that value AI can break diplomacy with an ally, declare a war, or
# act the other way around: form an alliance
class BehaviorDiplomatic(BehaviorComponent):
	"""
	Behaviors that handle diplomacy.
	"""

	# value to which each function is related, so even when relationship_score is at the peek somewhere (e.g. it's value is 1.0)
	# probability to actually choose given action is peek/upper_boundary (0.2 in case of upper_boundary = 5.0)
	upper_boundary = 5.0

	# possible actions behavior can take
	actions = Enum('wait', 'war', 'peace', 'neutral')

	def calculate_relationship_score(self, balance, weights):
		"""
		Calculate total relationship_score based on balances and their weights.
		Count only balances that have weight defined (this way "default" weight is 0)
		"""
		return sum((getattr(balance, key) * value for key, value in weights.iteritems()))

	def _move_f(self, f, v_x, v_y):
		"""
		Return function f moved by vector (v_x, v_y)
		"""
		return lambda x: f(x - v_x) + v_y

	def handle_diplomacy(self, parameters, **environment):
		"""
		Main function responsible for handling diplomacy.
		"""
		player = environment['player']
		balance =  self.owner.strategy_manager.calculate_player_balance(player)
		relationship_score = self.calculate_relationship_score(balance, self.weights)
		action = self._get_action(relationship_score, **parameters)
		self._perform_action(action, **environment)

	def _perform_action(self, action, **environment):
		"""
		Execute action from actions Enum.
		"""
		player = environment['player']

		# ideally this shouldn't automatically change diplomacy for both players (i.e. add_pair) but do it for one side only.

		if action == self.actions.war:
			self.session.world.diplomacy.add_enemy_pair(self.owner, player)
		elif action == self.actions.peace:
			self.session.world.diplomacy.add_ally_pair(self.owner, player)
		elif action == self.actions.neutral:
			self.session.world.diplomacy.add_neutral_pair(self.owner, player)

	def _get_quadratic_function(self, mid, root, peek=1.0):
		"""
		Functions for border distributions such as enemy or ally (left or right parabola).
		@param mid: value on axis X that is to be center of the parabola
		@type mid: float
		@param root: value on axis X which is a crossing point of axis OX and the function itself
		@type root: float
		@param peek: value on axis Y which is a peek of a function
		@type peek: float
		@return: quadratic function
		@rtype: lambda(x)
		"""

		# base function is upside-down parabola, stretched in X in order to have roots at exactly 'root' value.
		# (-1. / (abs(mid - root) ** 2)) part is for stretching the parabola in X axis and flipping it upside down, we have to use
		# abs(mid - root) because it's later moved by mid
		base = lambda x: (-1. / (abs(mid - root) ** 2)) * (x ** 2)

		# we move the function so it looks like "distribution", i.e. move it far left(or right), and assume the peek is 1.0
		moved = self._move_f(base, mid, peek)

		# in case of negative values of f(x) we want to have 0.0 instead
		final_function = lambda x: max(0.0, moved(x))

		return final_function

	def get_enemy_function(self, root, peek=1.0):
		return self._get_quadratic_function(-10.0, root, peek)

	def get_ally_function(self, root, peek=1.0):
		return self._get_quadratic_function(10.0, root, peek)

	def get_neutral_function(self, mid, root, peek=1.0):
		return self._get_quadratic_function(mid, root, peek)

	def _choose_random_from_tuple(self, tuple):
		"""
		Choose random action from tuple of (name, value)
		"""
		total_probability = sum((item[1] for item in tuple))
		random_value = self.session.random.random() * total_probability
		counter = 0.0
		for item in tuple:
			if item[1] + counter >= random_value:
				return item[0]
			else:
				counter+= item[1]

	def _get_action(self, relationship_score, **parameters):
		possible_actions = []
		if 'enemy' in parameters:
			enemy_params = parameters['enemy']
			possible_actions.append((self.actions.war, self.get_enemy_function(**enemy_params)(relationship_score), ))

		if 'ally' in parameters:
			ally_params = parameters['ally']
			possible_actions.append((self.actions.peace, self.get_ally_function(**ally_params)(relationship_score), ))

		if 'neutral' in parameters:
			neutral_params = parameters['neutral']
			possible_actions.append((self.actions.neutral, self.get_neutral_function(**neutral_params)(relationship_score), ))

		max_probability = max((item[1] for item in possible_actions))
		random_value = self.session.random.random() * self.upper_boundary
		if random_value < max_probability: #do something
			return self._choose_random_from_tuple(possible_actions)
		else:
			return self.actions.wait

	def hostile_player(self, **environment):
		"""
		Calculate balance, and change diplomacy towards a player to neutral or ally.
		This has a very small chance though, since BehaviorEvil enjoys to be in a war.
		"""

		# Parameters are crucial in determining how AI should behave:
		# 'ally' and 'enemy' parameters are tuples of 1 or 2 values that set width or width and height of the parabola.
		# By default parabola peek is fixed at 1.0, but could be changed (by providing second parameter)
		# to manipulate the chance with which given actions is called
		# 'neutral' parameter is a tuple up to three values, first one determining where the center of the parabola is

		self.handle_diplomacy(self.parameters_hostile, **environment)

	def neutral_player(self, **environment):
		self.handle_diplomacy(self.parameters_neutral, **environment)

	def allied_player(self, **environment):
		self.handle_diplomacy(self.parameters_allied, **environment)

class BehaviorEvil(BehaviorDiplomatic):
	"""
	Diplomatic behavior.
	Evil AI likes players that are:
		- stronger
		- bigger (in terms of terrain)
		- wealthier
	Neutral towards:
		- poorer
	Dislikes:
		- weaker
		- smaller
	"""

	# negative weights favors opposite balance, e.g. enemy is stronger => higher relationship_score
	weights = {
		'power': -0.6,
		'wealth': -0.3,
		'terrain': -0.1,
	}

	parameters_hostile = {
		'neutral': {'mid':0.0, 'root':2.0, 'peek':0.2}, # parabola with the center at 0.0, of root at 2.0 and -2.0. Peek at 0.5 (on Y axis)
		'ally': {'root':7.0, },
	}
	parameters_neutral = {
		'enemy': {'root':-1.0, },
		'ally': {'root':5.0, 'peek':0.7, },
	}
	parameters_allied = {
		'neutral': {'mid':-2.0, 'root':-0.5, 'peek':0.2, }, # parabola with the center at -2.0, of root at -0.5 (the other at -3.5). Peek at 0.2 (on Y axis)
		'enemy': {'root': -3.5, }, # smaller chance to go straight from allied to hostile
	}


	def __init__(self, owner):
		super(BehaviorEvil, self).__init__(owner)
		#self._certainty['hostile_player'] = self._certainty_has_fleet
		#self._certainty['neutral_player'] = self._certainty_has_boat_builder



class BehaviorGood(BehaviorDiplomatic):
	"""
	Diplomatic behavior.
	Good AI likes players that are:
		- weaker
		- smaller
	Neutral towards:
		- wealth
	Dislikes:
		-
	"""

	weights = {
		'power': 0.6,
		'terrain': 0.4,
		'wealth': 0.0,
	}

	parameters_hostile = {
		'neutral': {'mid': -2.0, 'root': -0.5, 'peek': 0.2, },
		'ally': {'root': 1.0, },
	}

	parameters_neutral = {
		'ally': {'root': 5.0, },
		'enemy': {'root': -3.0, },
	}

	parameters_allied = {
		'neutral': {'mid': -3.0, 'root': -1.5, 'peek': 0.2, },
		'enemy': {'root': -5.0, },
	}

class BehaviorNeutral(BehaviorDiplomatic):
	"""
	Diplomatic behavior.
	Neutral AI likes players that are:
		- wealthier
	Neutral towards:
		- strength
		- size (favor bigger though)
	Dislikes:
		-
	"""

	weights = {
		'wealth': -0.8,
		'power': -0.1,
		'terrain': -0.1,
	}

	parameters_hostile = {
		'neutral': {'mid': 0.0, 'root': 2.0, 'peek': 0.3, },
		'ally': {'root': 4.0, },
	}

	parameters_neutral = {
		'ally': {'root': 5.0, },
		'enemy': {'root': -5.0, },
	}

	parameters_allied = {
		'neutral':{'mid': -1.0, 'root': 0.0, 'peek': 0.3, },
		'enemy': {'root': -7.0, },
	}

class BehaviorDebug(BehaviorComponent):

	def __init__(self, owner):
		super(BehaviorDebug, self).__init__(owner)

	def debug(self, **environment):
		"""
		For debugging purposes.
		"""

		return None


class BehaviorRegularPirate(BehaviorComponent):

	power_balance_threshold = 1.0

	def __init__(self, owner):
		super(BehaviorRegularPirate, self).__init__(owner)
		self._certainty['fighting_ships_in_sight'] = certainty_power_balance_exp
		self._certainty['pirate_routine'] = self._certainty_pirate_routine

	def fighting_ships_in_sight(self, **environment):
		"""
		Attacks frigates only if they are enemies already and the power balance is advantageous.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = environment['power_balance']

		if power_balance < self.power_balance_threshold:
			BehaviorComponent.log.info('%s: Enemy ship was too strong, did not attack', self.__class__.__name__)
			return

		if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			BehaviorComponent.log.info('%s: Enemy ship was not hostile', self.__class__.__name__)
			return

		for ship in ship_group:
			ship.attack(enemies[0])
		BehaviorComponent.log.info('%s: Attacked enemy ship', self.__class__.__name__)

	def _certainty_pirate_routine(self, **environment):
		idle_ships = environment['idle_ships']
		if len(idle_ships) >= self.minimal_fleet_size:
			return self.default_certainty
		else:
			return 0.0

	def pirate_routine(self, **environment):
		"""
		Strategy that spawns pirate's idle-sailing routine.
		"""
		idle_ships = environment['idle_ships']

		# Use a one-ship group:
		idle_ships = idle_ships[:1]

		mission = PirateRoutine.create(self.owner.strategy_manager.report_success, self.owner.strategy_manager.report_failure, idle_ships)
		BehaviorComponent.log.info('BehaviorRegularPirate: pirate_routine request')
		return mission

class BehaviorAggressivePirate(BehaviorComponent):

	def __init__(self, owner):
		super(BehaviorAggressivePirate, self).__init__(owner)
		self._certainty['fighting_ships_in_sight'] = certainty_power_balance_exp

	def fighting_ships_in_sight(self, **environment):
		"""
		Attacks frigates only if they are enemies. Does not care about power balance.
		"""

		enemies = environment['enemies']
		ship_group = environment['ship_group']

		if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			BehaviorComponent.log.info('%s: Enemy ship was not hostile', self.__class__.__name__)
			return

		target_ship = UnitManager.get_lowest_hp_ship(enemies)
		for ship in ship_group:
			ship.attack(target_ship)
		BehaviorComponent.log.info('%s: Attacked enemy ship', self.__class__.__name__)

class BehaviorBreakDiplomacy(BehaviorComponent):
	"""
	Temporary action for breaking diplomacy with other players.
	"""

	def __init__(self, owner):
		super(BehaviorBreakDiplomacy, self).__init__(owner)

	def fighting_ships_in_sight(self, **environment):
		enemies = environment['enemies']
		ship_group = environment['ship_group']

		if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			AddEnemyPair(self.owner, enemies[0].owner).execute(self.session)
		BehaviorComponent.log.info('Player:%s broke diplomacy with %s' % (self.owner.name, enemies[0].owner.name))


class BehaviorCoward(BehaviorComponent):

	def __init__(self, owner):
		super(BehaviorCoward, self).__init__(owner)
		# Certainty here is a hyperbolic function from power_balance
		# (higher power_balance -> lesser chance of doing nothing)
		self._certainty['pirate_ships_in_sight'] = certainty_power_balance_inverse

	def pirate_ships_in_sight(self, **environment):
		"""
		Dummy action, do nothing really.
		"""
		BehaviorComponent.log.info('Pirates give me chills man.')


def certainty_are_enemies(**environment):
	"""
	returns 0.0 if two players are enemies already, default certainty otherwise.
	"""
	enemies = environment['enemies']
	ship_group = environment['ship_group']

	player = ship_group[0].owner
	enemy_player = enemies[0].owner

	return 0.0 if player.session.world.diplomacy.are_enemies(player, enemy_player) else BehaviorComponent.default_certainty


class BehaviorPirateHater(BehaviorComponent):

	def __init__(self, owner):
		super(BehaviorPirateHater, self).__init__(owner)
		self._certainty['pirate_ships_in_sight'] = certainty_are_enemies

	def pirate_ships_in_sight(self, **environment):
		"""
		Breaks diplomacy and attacks pirates.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = environment['power_balance']

		if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
				AddEnemyPair(self.owner, enemies[0].owner).execute(self.session)
		BehaviorComponent.log.info('I feel urgent need to wipe out them pirates.')
