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

import logging
from horizons.ai.aiplayer.behavior.profile import BehaviorManager


class Condition(object):
	"""
	Condition's goal is to aid StrategyManager in figuring out what kind of strategy/mission
	is applicable to given state of world, e.g. instead of having a really long method that decides what kind of reasoning
	should be done at given point, we have a collection of Conditions (with priorities) that are easier to handle.
	"""

	log = logging.getLogger("ai.aiplayer.combat.condition")
	default_certainty = 1.0

	def __init__(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.unit_manager = owner.unit_manager

		# States whether given condition can be locked
		self.lockable = True

	def check(self, **environment):
		"""
		Based on information contained in **environment, determine wheter given condition occurs.
		@return: If the condition occurs: dictionary, else: None
		"""
		raise NotImplementedError("This is an abstract class")

	def get_identifier(self, **environment):
		"""
		Based on information contained in **environment return an Unique identifier for given condition.
		User for checking whether given condition is already being resolved by a mission in progress.
		@return: unique identifier
		@rtype: str
		"""
		return self.__class__.__name__


class ConditionSharingSettlement(Condition):
	"""
	States whether given player shares a settlement with AI.
	Raises "attack_enemy_player" strategy
	"""
	def __init__(self, owner):
		super(ConditionSharingSettlement, self).__init__(owner)

	def check(self, **environment):
		other_player = environment['player']

		my_islands = set(self.unit_manager.get_player_islands(self.owner))
		enemy_islands = set(self.unit_manager.get_player_islands(other_player))

		# checks whether player share the same island
		if my_islands & enemy_islands:
			return {'player': other_player, 'certainty': self.default_certainty, 'strategy_name': 'player_shares_island', 'type': BehaviorManager.strategy_types.offensive}
		else:
			return None

	def get_identifier(self, **environment):
		return super(ConditionSharingSettlement, self).get_identifier(**environment) + str(environment['player'].worldid)


class ConditionHostile(Condition):
	"""
	States whether there is a hostile player that can be attacked (i.e. has ships that can be destroyed)
	"""
	def __init__(self, owner):
		super(ConditionHostile, self).__init__(owner)

	def check(self, **environment):
		player = environment['player']

		if not self.session.world.diplomacy.are_enemies(self.owner, player):
			return None

		hostile_ships = self.unit_manager.get_player_ships(player)
		if hostile_ships:
			return {'player': player, 'certainty': self.default_certainty, 'strategy_name': 'hostile_player', 'type': BehaviorManager.strategy_types.offensive}
		else:
			return None

	def get_identifier(self, **environment):
		return super(ConditionHostile, self).get_identifier(**environment) + str(environment['player'].worldid)


class ConditionNeutral(Condition):
	"""
	States whether given player is neutral.
	What it aims to do is not only find if given player is neutral, but also sort them,
	i.e. penalize if given neutral is ally with our enemies etc.
	This way in case of any diplomatic actions it's possible to have a "safe" ally
	"""

	def check(self, **environment):
		player = environment['player']
		if self.session.world.diplomacy.are_neutral(self.owner, player):
			return {'player': player, 'certainty': self.default_certainty, 'strategy_name': 'neutral_player', 'type': BehaviorManager.strategy_types.diplomatic}
		else:
			return None

	def get_identifier(self, **environment):
		return super(ConditionNeutral, self).get_identifier(**environment) + str(environment['player'].worldid)


class ConditionAllied(Condition):
	"""
	States whether given player is ally.
	"""

	def check(self, **environment):
		player = environment['player']
		if self.session.world.diplomacy.are_allies(self.owner, player):
			return {'player': player, 'certainty': self.default_certainty, 'strategy_name': 'allied_player', 'type': BehaviorManager.strategy_types.diplomatic}
		else:
			return None


	def get_identifier(self, **environment):
		return super(ConditionAllied, self).get_identifier(**environment) + str(environment['player'].worldid)


class ConditionDebug(Condition):
	"""
	For testing purposes, always happens
	"""

	def check(self, **environment):
		player = environment['player']
		return {'player': player, 'certainty': self.default_certainty, 'strategy_name': 'debug', 'type': BehaviorManager.strategy_types.diplomatic}
		#return {'player': player, 'certainty': self.default_certainty, 'strategy_name': 'player_shares_island', 'type': BehaviorManager.strategy_types.offensive}

	def get_identifier(self, **environment):
		return super(ConditionDebug, self).get_identifier(**environment) + str(environment['player'].worldid)


class ConditionPirateRoutinePossible(Condition):
	"""
	Currently always occurs, when pirate has more conditions/strategies to work on, this may change.
	"""
	def __init__(self, owner):
		super(ConditionPirateRoutinePossible, self).__init__(owner)
		self.lockable = False

	def check(self, **environment):
		return {'certainty': self.default_certainty, 'strategy_name': 'pirate_routine', 'type': BehaviorManager.strategy_types.idle}

	def get_identifier(self, **environment):
		return super(ConditionPirateRoutinePossible, self).get_identifier(**environment)
