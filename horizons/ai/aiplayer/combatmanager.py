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
from horizons.ai.aiplayer.unitmanager import UnitManager
from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack
from horizons.component.namedcomponent import NamedComponent
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.pirateship import PirateShip


class CombatManager(object):
	"""
	CombatManager object is responsible for handling close combat in game.
	It scans the environment (lookout) and requests certain actions from behavior
	"""
	log = logging.getLogger("ai.aiplayer.behavior.combatmanager")

	def __init__(self, owner):
		super(CombatManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session

	def lookout(self):
		unit_manager = self.owner.unit_manager
		rules = self.owner.unit_manager.filtering_rules
		for ship_group in unit_manager.get_available_ship_groups(None):
			for ship in ship_group:
				self.log.debug("Ship:%s state:%s"%(ship.get_component(NamedComponent).name, self.owner.ships[ship]))
			ships_around = unit_manager.find_ships_near_group(ship_group)

			# we want only PirateShips
			pirates = unit_manager.filter_ships(self.owner, ships_around, (rules.ship_type(PirateShip), ))
			fighting_ships = unit_manager.filter_ships(self.owner, ships_around, (rules.ship_type(FightingShip), ))
			environment = {'ship_group': ship_group}
			if fighting_ships:
				environment['enemies'] = fighting_ships
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, fighting_ships[0].owner.name, environment['power_balance']))
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'fighting_ships_in_sight', **environment)
			elif pirates:
				environment = {'enemies': pirates, 'ship_group': ship_group, }
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, pirates)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, pirates[0].owner.name, environment['power_balance']))
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'pirates_in_sight', **environment)
			else:
				# execute idle action only if whole fleet is idle
				if all([self.owner.ships[ship] == self.owner.shipStates.idle for ship in ship_group]):
					self.owner.behavior_manager.request_action(BehaviorProfile.action_types.idle,
						'no_one_in_sight', **environment)

	def tick(self):
		self.lookout()


class PirateCombatManager(CombatManager):
	"""
	Pirate player requires slightly different handling of combat, thus it gets his own CombatManager.
	Pirate player is able to use standard BehaviorComponents in it's BehaviorManager.
	"""
	log = logging.getLogger("ai.aiplayer.piratecombatmanager")

	def __init__(self, owner):
		super(PirateCombatManager, self).__init__(owner)
		# todo: remove 2 lines below
		self.owner = owner
		self.session = owner.session

	def lookout(self):
		unit_manager = self.owner.unit_manager
		rules = self.owner.unit_manager.filtering_rules
		for ship, shipState in self.owner.ships.iteritems():
			ships_around = unit_manager.find_ships_near_group([ship])
			environment = {'ship_group': [ship], }

			if ships_around:
				fighting_ships = unit_manager.filter_ships(self.owner, ships_around, (rules.ship_type(FightingShip), rules.hostile()))

				if fighting_ships:
					environment['enemies'] = fighting_ships
					environment['power_balance'] = UnitManager.calculate_power_balance([ship], fighting_ships)
					self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, fighting_ships[0].owner.name, environment['power_balance']))
					self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
						'fighting_ships_in_sight', **environment)
				elif shipState in [self.owner.shipStates.moving_random, self.owner.shipStates.chasing_ship, self.owner.shipStates.idle]:
					environment['enemies'] = ships_around
					self.owner.behavior_manager.request_action(BehaviorProfile.action_types.idle,
						'trading_ships_in_sight', **environment)
			else:
				if self.owner.ships[ship] != self.owner.shipStates.moving_random:
					self.owner.behavior_manager.request_action(BehaviorProfile.action_types.idle,
						'no_one_in_sight', **environment)
