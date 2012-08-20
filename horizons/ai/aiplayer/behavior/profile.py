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

import random
from horizons.ai.aiplayer.behavior import BehaviorManager

from horizons.ai.aiplayer.behavior.behaviorcomponents import BehaviorPirateHater, BehaviorCoward,\
	BehaviorRegular, BehaviorPirateRoutine, BehaviorBreakDiplomacy,\
	BehaviorDoNothing, BehaviorRegularPirate, BehaviorAggressive, BehaviorAggressivePirate, BehaviorDebug, BehaviorSmart, BehaviorEvil, BehaviorNeutral, BehaviorGood, BehaviorCautious
from horizons.ai.aiplayer.strategy.condition import ConditionNeutral, ConditionSharingSettlement, ConditionHostile, ConditionDebug, ConditionPirateRoutinePossible, ConditionAllied


class BehaviorProfile(object):
	def __init__(self):
		"""
		Init actions and strategies with required types.
		e.g. self.strategies is a dict of Enum => dict(), each of such items is later filled by concrete BehaviorProfile.
		"""
		super(BehaviorProfile, self).__init__()
		self.actions = dict(((action_type, dict()) for action_type in BehaviorManager.action_types))
		self.strategies = dict(((strategy_type, dict()) for strategy_type in BehaviorManager.strategy_types))
		self.conditions = {}


class BehaviorProfileDebug(BehaviorProfile):

	def __init__(self, player):
		super(BehaviorProfileDebug, self).__init__()

		self.conditions = {
			ConditionHostile(player): 1.1,
			#ConditionSharingSettlement(player): 1.0,
			ConditionNeutral(player): 0.4,
			ConditionAllied(player): 0.3,
			#ConditionDebug(player): 1.0,
		}

		self.actions[BehaviorManager.action_types.offensive][BehaviorSmart(player)] = 1.0

		self.strategies[BehaviorManager.strategy_types.offensive][BehaviorRegular(player)] = 1.0
		#self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorAggressive(player)] = 0.02
		#self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorDebug(player)] = 1.0
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorEvil(player)] = 1.0


class BehaviorProfileAggressive(BehaviorProfile):

	def __init__(self, player):
		super(BehaviorProfileAggressive, self).__init__()

		self.conditions = {
			ConditionHostile(player): 1.1,
			ConditionSharingSettlement(player): 1.0,
			ConditionNeutral(player): 0.3,
			ConditionAllied(player): 0.3,
		}

		self.actions[BehaviorManager.action_types.offensive][BehaviorRegular(player)] = 0.35
		self.actions[BehaviorManager.action_types.offensive][BehaviorAggressive(player)] = 0.65
		self.actions[BehaviorManager.action_types.idle][BehaviorDoNothing(player)] = 1.0

		self.strategies[BehaviorManager.strategy_types.offensive][BehaviorRegular(player)] = 1.0

		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorAggressive(player)] = 0.05
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorEvil(player)] = 0.75
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorNeutral(player)] = 0.2


class BehaviorProfileBalanced(BehaviorProfile):

	def __init__(self, player):
		super(BehaviorProfileBalanced, self).__init__()

		self.conditions = {
			ConditionHostile(player): 1.1,
			ConditionSharingSettlement(player): 1.0,
			ConditionNeutral(player): 0.3,
			ConditionAllied(player): 0.29,
		}

		self.actions[BehaviorManager.action_types.offensive][BehaviorRegular(player)] = 0.8
		self.actions[BehaviorManager.action_types.offensive][BehaviorAggressive(player)] = 0.2
		self.actions[BehaviorManager.action_types.idle][BehaviorDoNothing(player)] = 1.0

		self.strategies[BehaviorManager.strategy_types.offensive][BehaviorRegular(player)] = 1.0

		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorEvil(player)] = 0.05
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorNeutral(player)] = 0.9
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorGood(player)] = 0.05

class BehaviorProfileCautious(BehaviorProfile):

	def __init__(self, player):
		super(BehaviorProfileCautious, self).__init__()

		self.conditions = {
			ConditionHostile(player): 0.9,
			#ConditionSharingSettlement(player): 1.0,  # does not respond to enemy sharing a settlement
			ConditionNeutral(player): 0.3,
			ConditionAllied(player): 0.29,
		}

		self.actions[BehaviorManager.action_types.offensive][BehaviorRegular(player)] = 0.8
		self.actions[BehaviorManager.action_types.idle][BehaviorDoNothing(player)] = 1.0

		self.strategies[BehaviorManager.strategy_types.offensive][BehaviorRegular(player)] = 1.0
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorGood(player)] = 0.7
		self.strategies[BehaviorManager.strategy_types.diplomatic][BehaviorNeutral(player)] = 0.3


class BehaviorProfilePirateRegular(BehaviorProfile):

	def __init__(self, player):
		super(BehaviorProfilePirateRegular, self).__init__()

		self.conditions = {
			ConditionPirateRoutinePossible(player): 1.0,
		}

		self.actions[BehaviorManager.action_types.offensive][BehaviorRegularPirate(player)] = 0.75
		self.actions[BehaviorManager.action_types.offensive][BehaviorAggressivePirate(player)] = 0.25
		self.actions[BehaviorManager.action_types.idle][BehaviorDoNothing(player)] = 0.5

		self.strategies[BehaviorManager.strategy_types.idle][BehaviorRegularPirate(player)] = 1.0


class BehaviorProfileManager(object):
	"""
	BehaviorProfileManager is an object that defines the dictionary with BehaviorComponents for AIPlayer.
	If it proves to be useful it will handle loading AI profiles from YAML.
	"""

	log = logging.getLogger("ai.aiplayer.behavior.profilemanager")

	@classmethod
	def get_random_player_profile(cls, player, token):
		return cls._get_random_profile(player, token, get_available_player_profiles())

	@classmethod
	def get_random_pirate_profile(cls, player, token):
		return cls._get_random_profile(player, token, get_available_pirate_profiles())

	@classmethod
	def _get_random_profile(cls, player, token, profiles):
		random_generator = random.Random()
		random_generator.seed(token)

		total, random_value = 0.0, random_generator.random()

		probabilities_sum = sum([item[1] for item in profiles])

		assert probabilities_sum > 1e-7, "sum of BehaviorProfile probabilities is too low: %s" % probabilities_sum

		random_value *= probabilities_sum

		chosen_profile = None
		for profile, probability in profiles:
			if (total + probability) >= random_value:
				chosen_profile = profile
				break
			total += probability

		cls.log.debug("BehaviorProfileManager: Player %s was given %s", player.name, chosen_profile.__name__)
		return chosen_profile(player)

# Each AI player is assigned a Profile with certain probability.
# actions, strategies and conditions are encapsulated inside a profile itself.
def get_available_player_profiles():
	return (
		(BehaviorProfileCautious, 0.3),
		(BehaviorProfileAggressive, 0.1),
		(BehaviorProfileBalanced, 0.6),
		#(BehaviorProfileDebug, 1.0),
	)

def get_available_pirate_profiles():
	return (
		(BehaviorProfilePirateRegular, 1.0),
	)
