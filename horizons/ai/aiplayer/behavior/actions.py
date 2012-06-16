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
from horizons.ai.aiplayer.unitmanager import UnitManager

from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack

import logging

class BehaviorAction(object):
	"""
	This is an abstract BehaviorAction component.
	"""
	log = logging.getLogger('ai.aiplayer.behavioraction')

	def __init__(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session


# Action components below are divided into Idle, Offensive and Defensive actions.
# This is just an arbitrary way to do this. Another good division may consist of "Aggressive, Normal,Cautious"
# (division below is not related to the way dictionaries in BehaviorManager are named (offensive, idle, defensive))

# Defensive Actions
#	Actions used in response to being attacked.
#	Possible usage may be: sailing back to main settlement, fleeing battle, sending reinforcements

# Idle Actions
#	Actions used in situations when there are no ships nearby.
#	Possible usage may be: scouting, sailing randomly, sailing back to main settlement
class BehaviorActionBored(BehaviorAction):
	def __init__(self, owner):
		super(BehaviorActionBored, self).__init__(owner)

	def no_one_in_sight(self, **enviornment):
		"""
		Idle action, sail randomly when no ship was spotted nearby.
		"""
		ship_group = enviornment['ship_group']
		for ship in ship_group:
			self.owner.send_ship_random(ship)
		BehaviorAction.log.info('no_one_in_sight action')


class BehaviorActionKeepFleetTogether(BehaviorAction):
	def __init__(self, owner):
		super(BehaviorActionKeepFleetTogether, self).__init__(owner)

	def no_one_in_sight(self, **enviornment):
		"""
		When no enemies are in sight, and the groups is dispersed, bring the whole fleet together.
		"""
		pass # TODO: implement


# Offensive Actions
#	Actions used when there is a possibility to engage in combat with other players.
#	It is also reasonable to flee from enemies if they are much stronger.
class BehaviorActionRegular(BehaviorAction):
	"""
	A well-balanced way to respond to situations in game.
	"""
	power_balance_threshold = 1.1 # TODO: Figure out a good place for these (if not just Personalities module).YAML.

	def __init__(self, owner):
		super(BehaviorActionRegular, self).__init__(owner)

	def pirates_in_sight(self, **environment):
		"""
		Attacks pirates only if they are enemies already and the power balance is advantageous.
		"""
		pirates = environment['enemies']
		ship_group = environment['ship_group']
		power_balance = UnitManager.calculate_power_balance(ship_group, pirates)

		# It's enough to check if first pirate is hostile, since there is only one pirate player.
		if self.session.world.diplomacy.are_enemies(self.owner, pirates[0].owner) and \
		   power_balance > self.power_balance_threshold:

			# Let each ship attack it's closest enemy to maximize dps (in a way)
			ship_pairs = UnitManager.get_closest_ships_for_each(ship_group, pirates)
			for ship, pirate in ship_pairs:
				Attack(ship, pirate).execute(self.session)
			BehaviorAction.log.info('Attacking pirate player.')
		else:
			BehaviorAction.log.info('Not attacking pirate player.')

	def fighting_ships_in_sight(self, **environment):
		"""
		Attacks frigates only if they are enemies already and the power balance is advantageous.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']

		if self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
			for ship in ship_group:
				Attack(ship, enemies[0]).execute(self.session)
			BehaviorAction.log.info('ActionRegular: Attacked enemy ship')
		else:
			BehaviorAction.log.info('ActionRegular: Enemy ship was not hostile')


class BehaviorActionCoward(BehaviorAction):
	def __init__(self, owner):
		super(BehaviorActionCoward, self).__init__(owner)

	def pirates_in_sight(self, **environment):
		"""
		Dummy action, do nothing really.
		"""
		BehaviorAction.log.info('Pirates give me chills man.')


class BehaviorActionPirateHater(BehaviorAction):
	def __init__(self, owner):
		super(BehaviorActionPirateHater, self).__init__(owner)

	def pirates_in_sight(self, **environment):
		"""
		Always attack pirates and start wars with them.
		"""
		enemies = environment['enemies']
		ship_group = environment['ship_group']

		for ship in ship_group:
			if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0].owner):
				AddEnemyPair(self.owner, enemies[0].owner).execute(self.session)
			Attack(ship, enemies[0]).execute(self.session)
		BehaviorAction.log.info('I feel urgent need to wipe out them pirates.')
