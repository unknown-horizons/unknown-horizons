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
	BehaviorKeepFleetTogether, BehaviorRegular, BehaviorPirateRoutine, BehaviorBreakDiplomacy,\
	BehaviorDoNothing, BehaviorRegularPirate, BehaviorAggressive
from horizons.ai.aiplayer.strategy.condition import ConditionNeutral, ConditionSharingSettlement, ConditionHostile, ConditionDebug
from horizons.ext.enum import Enum
from horizons.util.worldobject import WorldObject


class BehaviorProfile(WorldObject):
	"""
	BehaviorProfile is an object that defines the dictionary with BehaviorComponents for AIPlayer.
	If it proves to be useful it will handle loading AI profiles from YAML.
	"""

	log = logging.getLogger("ai.aiplayer.behavior.profile")

	@classmethod
	def get_random_player_actions(cls, player, token):

		random_generator = random.Random()
		random_generator.seed(token)
		# TODO: use new random generator to select a player actions randomly (controlled randomness, since seed is set)

		actions = {
			BehaviorManager.action_types.offensive: dict(),
			BehaviorManager.action_types.defensive: dict(),
			BehaviorManager.action_types.idle: dict(),
			}
		#actions[BehaviorManager.action_types.offensive][BehaviorPirateHater(player)] = 0.1
		#actions[BehaviorManager.action_types.offensive][BehaviorCoward(player)] = 0.1
		actions[BehaviorManager.action_types.offensive][BehaviorRegular(player)] = 2.0
		#actions[BehaviorManager.action_types.offensive][BehaviorBreakDiplomacy(player)] = 0.1

		#actions[BehaviorManager.action_types.idle][BehaviorKeepFleetTogether(player)] = 0.1

		#TODO: remove this behavior
		#actions[BehaviorManager.action_types.idle][BehaviorScoutRandomlyNearby(player)] = 0.1
		actions[BehaviorManager.action_types.idle][BehaviorDoNothing(player)] = 1.0

		return actions

	@classmethod
	def get_random_pirate_actions(cls, player, token):
		actions = {
			BehaviorManager.action_types.offensive: dict(),
			BehaviorManager.action_types.defensive: dict(),
			BehaviorManager.action_types.idle: dict(),
		}
		actions[BehaviorManager.action_types.offensive][BehaviorRegularPirate(player)] = 1.0
		actions[BehaviorManager.action_types.idle][BehaviorPirateRoutine(player)] = 1.0
		actions[BehaviorManager.action_types.idle][BehaviorDoNothing(player)] = 0.5

		return actions

	@classmethod
	def get_random_player_strategies(cls, player, token):
		strategies = {
			BehaviorManager.strategy_types.offensive: dict(),
			BehaviorManager.strategy_types.diplomatic: dict(),
		}
		strategies[BehaviorManager.strategy_types.offensive][BehaviorRegular(player)] = 1.0

		strategies[BehaviorManager.strategy_types.diplomatic][BehaviorAggressive(player)] = 0.01
		strategies[BehaviorManager.strategy_types.diplomatic][BehaviorRegular(player)] = 0.99

		return strategies

	@classmethod
	def get_random_player_conditions(cls, player, token):
		conditions = {
			#ConditionDebug(player):10.0,
			ConditionHostile(player): 1.1,
			ConditionSharingSettlement(player): 1.0,
			ConditionNeutral(player): 0.3,
		}
		return conditions

	@classmethod
	def get_random_pirate_conditions(cls, player, token):
		return {}

	@classmethod
	def get_random_pirate_strategies(cls, player, token):
		return {}

