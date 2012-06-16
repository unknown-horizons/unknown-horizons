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
from horizons.ai.aiplayer.behavior import BehaviorManager
from horizons.ai.aiplayer.behavior.profile import BehaviorProfile
from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.ship import PirateShip


class CombatManager(WorldObject):
	"""
	CombatManager object is responsible for handling close combat in game.
	It scans the environment (lookout) and requests certain actions from behavior
	"""
	log = logging.getLogger("ai.aiplayer.combatmanager")

	def __init__(self, owner):
		super(CombatManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session

	def lookout(self):
		unit_manager = self.owner.unit_manager
		rules = self.owner.unit_manager.filtering_rules
		for ship_group in unit_manager.get_available_ship_groups(None):
			ships_around = unit_manager.find_ships_near_group(ship_group)

			# we want only PirateShips
			pirates = unit_manager.filter_ships(self.owner, ships_around, (rules.ship_type(PirateShip), ))

			environment = {'enemies': pirates, 'ship_group': ship_group, }
			if pirates:
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'pirates_in_sight', **environment)
			else:
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.idle,
					'no_one_in_sight', **environment)

	def tick(self):
		self.lookout()

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls, owner)
		#self._load(db, player)
		return self

	#TODO add save/load mechanisms

class PirateCombatManager(CombatManager):
	"""
	Pirate player requires slightly different handling of combat, thus it gets his own CombatManager.
	Pirate player is able to use standard BehaviorComponents in it's BehaviorManager.
	"""
	log = logging.getLogger("ai.aiplayer.piratecombatmanager")

	def __init__(self, owner):
		super(PirateCombatManager, self).__init__(owner)
		self.owner = owner
		self.session = owner.session

	def lookout(self):
		unit_manager = self.owner.unit_manager
		rules = self.owner.unit_manager.filtering_rules
		for ship, shipState in self.owner.ships.iteritems():
			enemies = unit_manager.find_ships_near_group([ship])
			fighting_ships = unit_manager.filter_ships(self.owner, enemies, (rules.ship_type(FightingShip), ))
			print fighting_ships
			environment = {'enemies': fighting_ships, 'ship_group': [ship], }
			if fighting_ships:
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'fighting_ships_in_sight', **environment)
			else:
				if self.owner.ships[ship] != self.owner.shipStates.moving_random:
					self.owner.behavior_manager.request_action(BehaviorProfile.action_types.idle,
						'no_one_in_sight', **environment)

