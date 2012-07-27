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
from horizons.ai.aiplayer.behavior.profile import BehaviorProfile


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

	def check(self, **environment):
		"""
		Based on information contained in **environment, determine wheter given condition occurs.
		@return: If the condition occurs: dictionary, else: None
		"""
		raise NotImplementedError("This is an abstract class")

class ConditionSharingSettlement(Condition):
	"""
	States whether any player shares a settlement with AI.
	Raises "attack_enemy_player" strategy
	"""
	def __init__(self, owner):
		super(ConditionSharingSettlement, self).__init__(owner)

	def check(self, **environment):
		other_players = environment['players']
		my_islands = set(self.unit_manager.get_player_islands(self.owner))

		players_sharing = []
		for player in other_players:
			enemy_islands = set(self.unit_manager.get_player_islands(player))

			# checks whether player share the same island
			if my_islands & enemy_islands:
				# TODO: maybe base certainty on power balance ?
				players_sharing.append(player)

		if players_sharing:
			return {'players': players_sharing, 'certainty': self.default_certainty, 'strategy_name': 'players_share_island', 'type': BehaviorProfile.strategy_types.offensive}
		else:
			return None

class ConditionHostile(Condition):
	"""
	States whether there is a hostile player that can be attacked.
	"""
	def __init__(self, owner):
		super(ConditionHostile, self).__init__(owner)

	def check(self, **environment):
		other_players = environment['players']

		hostile_players = [player for player in other_players if self.session.world.diplomacy.are_enemies(self.owner, player)]

		if hostile_players:
			return {'players': hostile_players, 'certainty': self.default_certainty, 'strategy_name': 'hostile_players', 'type': BehaviorProfile.strategy_types.offensive}
		else:
			return None

class ConditionNeutral(Condition):
	"""
	States whether there is a neutral player on the map.
	"""

	def check(self, **environment):
		other_players = environment['players']

		neutral_players = [player for player in other_players if self.session.world.diplomacy.are_neutral(self.owner, player)]

		if neutral_players:
			return {'players': neutral_players, 'certainty': self.default_certainty, 'strategy_name': 'neutral_players', 'type': BehaviorProfile.strategy_types.diplomatic}
		else:
			return None

class ConditionDebug(Condition):
	"""
	For testing purposes, always happens
	"""

	def check(self, **environment):
		players = environment['players']
		return {'players': players, 'certainty': self.default_certainty, 'strategy_name': 'neutral_players', 'type': BehaviorProfile.strategy_types.diplomatic}

def get_all_conditions(player):
		conditions = {
			#ConditionDebug(player):10.0,
			ConditionHostile(player): 1.1,
			ConditionSharingSettlement(player): 1.0,
			ConditionNeutral(player): 0.9,
			}
		return conditions

