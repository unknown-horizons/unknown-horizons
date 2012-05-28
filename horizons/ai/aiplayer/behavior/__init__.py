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
from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack
from horizons.ext.enum import Enum

from horizons.util.worldobject import WorldObject


class BehaviorManager(WorldObject):
	"""
	BehaviorManager holds BehaviorComponents.
	Entities such as CombatManager or StrategyManager ask BehaviorManager to perform
	and action, or create a mission object. BehaviorManager does these based on
	behavior probability and likelihood of success.
	"""

	# Types of actions behavior can handle
	action_types = Enum('offensive', 'defensive')

	actions = {
		action_types.offensive: dict(),
		action_types.defensive: dict(),
	}

	log = logging.getLogger("ai.aiplayer.behaviormanager")

	def __init__(self, owner):
		super(BehaviorManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self._load_action_behaviors()

	def _load_action_behaviors(self):
		"""
		Load action behaviors from YAML.
		"""

		# TODO: This should be loaded from YAML
		self.actions[self.action_types.offensive][BehaviorActionPirateHater(self.owner)] = 0.1
		self.actions[self.action_types.offensive][BehaviorActionCoward(self.owner)] = 0.9

	def request_action(self, type, action_name, **environment):
		possible_behaviors = []
		for beh, prob in self.actions[type].iteritems():
			if hasattr(beh, action_name):
				possible_behaviors.append((beh,prob))

		# get the best action possible
		final_action = self.get_best_behavior(possible_behaviors, action_name, dict(environment))

		# call winning action
		getattr(final_action, action_name)(**environment)

	def get_best_behavior(self, behavior_iterable, action_name, environment_data):
		"""
		Get best behavior from behavior_iterable (linear time).
		"""
		total, rnd_val = 0, self.session.random.random()

		# instead of scaling every value to make 1.0, we scale rnd_val to sum of probabilities
		sum_probs = sum([item[1] for item in behavior_iterable])
		rnd_val*=sum_probs

		for beh, prob in behavior_iterable:
			if (total + prob) > rnd_val:
				return beh
			total+=prob
		# TODO: take action certainity into account as well


class BehaviorAction(object):
	"""
	This is an abstract BehaviorAction component.
	"""
	log = logging.getLogger('ai.aiplayer.behavior')
	def __init__(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session

class BehaviorActionPirateHater(BehaviorAction):

	def __init__(self, owner):
		super(BehaviorActionPirateHater, self).__init__(owner)

	def attack_pirate_group(self, **environment):
		"""
		Always attack pirates.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']

		for ship in ship_group:
			if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
				AddEnemyPair(self.owner, enemies[0].owner).execute(self.session)
			Attack(ship, enemies[0])
		BehaviorAction.log.info('I feel urgent need to wipe out them pirates.')

class BehaviorActionCoward(BehaviorAction):

	def __init__(self, owner):
		super(BehaviorActionCoward, self).__init__(owner)

	def attack_pirate_group(self, **environment):
		"""
		Dummy action, do nothing really.
		"""
		BehaviorAction.log.info('Pirates give me chills man.')
