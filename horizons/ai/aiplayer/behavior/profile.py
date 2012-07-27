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

from horizons.ai.aiplayer.behavior.behavioractions import BehaviorActionPirateHater, BehaviorActionCoward,\
	BehaviorActionKeepFleetTogether, BehaviorActionRegular, BehaviorActionPirateRoutine, BehaviorActionBreakDiplomacy,\
BehaviorActionScoutRandomlyNearby, BehaviorActionDoNothing, BehaviorActionRegularPirate
from horizons.ext.enum import Enum
from horizons.util.worldobject import WorldObject


class BehaviorProfile(WorldObject):
	"""
	BehaviorProfile is an object that defines the dictionary with BehaviorComponents for AIPlayer.
	If it proves to be useful it will handle loading AI profiles from YAML.
	"""
	action_types = Enum('offensive', 'defensive', 'idle')
	strategy_types = Enum('offensive', 'idle', 'diplomatic')

	log = logging.getLogger("ai.aiplayer.behaviorprofile")

	@classmethod
	def get_random_player_actions(cls, player):
		actions = {
			cls.action_types.offensive: dict(),
			cls.action_types.defensive: dict(),
			cls.action_types.idle: dict(),
			}
		#actions[cls.action_types.offensive][BehaviorActionPirateHater(player)] = 0.1
		#actions[cls.action_types.offensive][BehaviorActionCoward(player)] = 0.1
		actions[cls.action_types.offensive][BehaviorActionRegular(player)] = 2.0
		#actions[cls.action_types.offensive][BehaviorActionBreakDiplomacy(player)] = 0.1

		#actions[cls.action_types.idle][BehaviorActionKeepFleetTogether(player)] = 0.1
		#actions[cls.action_types.idle][BehaviorActionScoutRandomlyNearby(player)] = 0.2
		actions[cls.action_types.idle][BehaviorActionDoNothing(player)] = 1.0

		return actions

	@classmethod
	def get_random_player_strategies(cls, player):
		strategies = {
			cls.strategy_types.offensive: dict(),
			cls.strategy_types.diplomatic: dict(),
		}
		strategies[cls.strategy_types.offensive][BehaviorActionRegular(player)] = 1.0

		return strategies

	@classmethod
	def get_random_pirate_strategies(cls, player):
		return {}

	@classmethod
	def get_random_pirate_actions(cls, player):
		actions = {
			cls.action_types.offensive: dict(),
			cls.action_types.defensive: dict(),
			cls.action_types.idle: dict(),
		}
		actions[cls.action_types.offensive][BehaviorActionRegularPirate(player)] = 1.0
		actions[cls.action_types.idle][BehaviorActionPirateRoutine(player)] = 1.0
		actions[cls.action_types.idle][BehaviorActionDoNothing(player)] = 0.5

		return actions
