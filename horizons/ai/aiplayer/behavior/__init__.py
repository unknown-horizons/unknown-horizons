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


class BehaviorManager(WorldObject):
	"""
	BehaviorManager holds BehaviorComponents.
	Entities such as CombatManager or StrategyManager ask BehaviorManager to perform
	and action, or create a mission object. BehaviorManager does these based on
	behavior probability and likelihood of success.
	"""

	# Types of actions behavior can handle

	log = logging.getLogger("ai.aiplayer.behaviormanager")

	def __init__(self, owner):

		super(BehaviorManager, self).__init__()

		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.actions = owner.get_random_actions()

	def request_action(self, type, action_name, **environment):
		possible_behaviors = []
		for beh, prob in self.actions[type].iteritems():
			if hasattr(beh, action_name):
				certainty = beh.certainty(action_name, **environment)
				# final probability is the one defined in profile multiplied by certainty
				self.log.info("%s Action:%s Probability:%s Certainty:%s" % (beh.__class__.__name__, action_name, prob, certainty))
				possible_behaviors.append((beh, prob * certainty))

		# get the best action possible
		final_action = self.get_best_behavior(possible_behaviors, action_name, **environment)

		# call winning action
		getattr(final_action, action_name)(**environment)

	def get_best_behavior(self, behavior_iterable, action_name, **environment):
		"""
		Get best behavior from behavior_iterable (linear time).
		"""
		total, rnd_val = 0, self.session.random.random()

		# instead of scaling every value to make 1.0, we scale rnd_val to sum of probabilities
		sum_probs = sum([item[1] for item in behavior_iterable])
		rnd_val *= sum_probs

		for beh, prob in behavior_iterable:
			if (total + prob) > rnd_val:
				return beh
			total += prob

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls, owner)
		#self._load(db, player)
		return self
