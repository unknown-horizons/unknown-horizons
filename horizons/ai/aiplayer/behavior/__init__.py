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

from horizons.util.worldobject import WorldObject


class BehaviorManager(object):
	"""
	BehaviorManager holds BehaviorComponents.
	Entities such as CombatManager or StrategyManager ask BehaviorManager to perform
	and action, or create a mission object. BehaviorManager does these based on
	behavior probability and likelihood of success.
	"""

	log = logging.getLogger("ai.aiplayer.behavior.behaviormanager")

	def __init__(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.actions = owner.get_random_actions()

	def request_action(self, type, action_name, **environment):
		possible_behaviors = []
		for behavior, probability in self.actions[type].iteritems():
			if hasattr(behavior, action_name):
				certainty = behavior.certainty(action_name, **environment)
				# final probability is the one defined in profile multiplied by it's certainty
				self.log.info("Player:%s Behavior:%s Action:%s (p: %s ,c: %s ,f: %s)" % (self.owner.name,
					behavior.__class__.__name__, action_name, probability, certainty, probability * certainty))
				possible_behaviors.append((behavior, probability * certainty))

		# get the best action possible
		final_action = self.get_best_behavior(possible_behaviors, action_name, **environment)

		# call winning action if any is possible
		if hasattr(final_action, action_name):
			getattr(final_action, action_name)(**environment)

	def request_strategy(self, type, strategy_name, **environment):
		pass
	def get_best_behavior(self, behavior_iterable, action_name, **environment):
		"""
		Get best behavior from behavior_iterable (linear time).
		"""
		total, random_value = 0.0, self.session.random.random()

		# instead of scaling every value to make 1.0, we scale random_value to sum of probabilities
		sum_probs = sum([item[1] for item in behavior_iterable])
		random_value *= sum_probs

		for behavior, probability in behavior_iterable:
			if (total + probability) > random_value:
				return behavior
			total += probability
