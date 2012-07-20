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
from weakref import WeakKeyDictionary
from horizons.ai.aiplayer.behavior import BehaviorManager
from horizons.ai.aiplayer.behavior.profile import BehaviorProfile
from horizons.ai.aiplayer.unitmanager import UnitManager
from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack
from horizons.component.namedcomponent import NamedComponent
from horizons.ext.enum import Enum
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.pirateship import PirateShip


class CombatManager(object):
	"""
	CombatManager object is responsible for handling close combat in game.
	It scans the environment (lookout) and requests certain actions from behavior
	"""
	log = logging.getLogger("ai.aiplayer.behavior.combatmanager")

	# states to keep track of combat movement of each ship.
	shipCombatStates = Enum('idle', 'attacking', 'fleeing')

	def __init__(self, owner):
		super(CombatManager, self).__init__()
		self.owner = owner
		self.unit_manager = owner.unit_manager
		self.world = owner.world
		self.session = owner.session
		self.ships = WeakKeyDictionary()

	def handle_mission_combat(self, mission):
		"""
		Routine for handling combat in mission that requests for it.
		"""
		filters = self.unit_manager.filtering_rules
		fleet = mission.fleet

		ship_group = fleet.get_ships()

		if not ship_group:
			mission.abort_mission()

		ships_around = self.unit_manager.find_ships_near_group(ship_group)
		ships_around = self.unit_manager.filter_ships(self.owner, ships_around, (filters.hostile()))
		pirate_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.pirate(), ))
		fighting_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.fighting(), ))
		working_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.working(), ))

		environment = {'ship_group': ship_group}

		# begin combat if it's still unresolved
		if fighting_ships:
			environment['enemies'] = fighting_ships
			environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
			self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, fighting_ships[0].owner.name, environment['power_balance']))
			self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
				'fighting_ships_in_sight', **environment)
		elif pirate_ships:
			environment['enemies'] = working_ships
			environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, pirate_ships)
			self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, pirate_ships[0].owner.name, environment['power_balance']))
			self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
				'pirates_in_sight', **environment)
		elif working_ships:
			environment['enemies'] = working_ships
			self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
				'working_ships_in_sight', **environment)
		else:
			mission.continue_mission()

	def handle_casual_combat(self):
		"""
		Handles combat for ships wandering around the map (not assigned to any fleet/mission).
		"""
		filters = self.unit_manager.filtering_rules

		rules = (filters.not_in_fleet(), filters.fighting() )
		for ship in self.unit_manager.get_ships(rules):
			# Turn into one-ship group, since reasoning is based around groups of ships
			ship_group = [ship, ]
			# TODO: create artificial groups by dividing ships that are near into groups based on their distance

			ships_around = self.unit_manager.find_ships_near_group(ship_group)
			pirate_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.pirate(), ))
			fighting_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.fighting(), ))
			working_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.working(), ))
			environment = {'ship_group': ship_group}
			if fighting_ships:
				environment['enemies'] = fighting_ships
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, fighting_ships[0].owner.name, environment['power_balance']))
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'fighting_ships_in_sight', **environment)
			elif pirate_ships:
				environment['enemies'] =  pirate_ships
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, pirate_ships)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s" % (self.owner.name, pirate_ships[0].owner.name, environment['power_balance']))
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'pirates_in_sight', **environment)
			elif working_ships:
				environment['enemies'] = working_ships
				self.owner.behavior_manager.request_action(BehaviorProfile.action_types.offensive,
					'working_ships_in_sight', **environment)
			else:
				# execute idle action only if whole fleet is idle
				if all([self.owner.ships[ship] == self.owner.shipStates.idle for ship in ship_group]):
					self.owner.behavior_manager.request_action(BehaviorProfile.action_types.idle,
						'no_one_in_sight', **environment)

	def lookout(self):
		"""
		Basically do 3 things:
		1. Handle combat for missions that explicitly request for it.
		2. Check whether any of current missions may want to be interrupted to resolve potential
			combat that was not planned (e.g. hostile ships nearby fleet on a mission)
		3. Handle combat for ships currently not used in any mission.
		"""
		filters = self.unit_manager.filtering_rules
		# handle fleets that explicitly request to be in combat
		for mission in self.owner.strategy_manager.get_missions(condition=lambda mission: mission.combat_phase):
			self.handle_mission_combat(mission)

		# handle fleets that may way to be in combat, but request for it first
		for mission in self.owner.strategy_manager.get_missions(condition=lambda mission: not mission.combat_phase):

			# test first whether requesting for combat is of any use (any ships nearby)
			ship_group = mission.fleet.get_ships()
			ships_around = self.unit_manager.find_ships_near_group(ship_group)
			ships_around = self.unit_manager.filter_ships(self.owner, ships_around, (filters.hostile()))
			pirate_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.pirate(), ))
			fighting_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.fighting(), ))
			working_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.working(), ))

			# TODO: for now only test for hostile fighting ships
			if fighting_ships:
				if self.owner.strategy_manager.request_to_pause_mission(mission):
					self.handle_mission_combat(mission)
			elif working_ships:
				if self.owner.strategy_manager.request_to_pause_mission(mission):
					self.handle_mission_combat(mission)
			elif pirate_ships:
				if self.owner.strategy_manager.request_to_pause_mission(mission):
					self.handle_mission_combat(mission)

		# handle idle ships that are wandering around the map
		self.handle_casual_combat()

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

	def lookout(self):
		filters = self.unit_manager.filtering_rules
		for ship, shipState in self.owner.ships.iteritems():
			ships_around = self.unit_manager.find_ships_near_group([ship])
			environment = {'ship_group': [ship], }

			if ships_around:
				fighting_ships = self.unit_manager.filter_ships(self.owner, ships_around, (filters.ship_type(FightingShip), filters.hostile()))

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
