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
from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip


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
		for ship_group in self.owner.unit_manager.get_available_ship_groups(None):
			other_ships = self.owner.unit_manager.find_ships_near_group(ship_group)
			enemies = self.owner.unit_manager.filter_enemy_ships(other_ships)
			environment = {'enemies': enemies, 'ship_group': ship_group, }
			if enemies:
				# TODO: assume it's only pirates in range, it should take enemy types into account as well
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
					'pirates_in_sight', **environment)
			else:
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.idle,
					'no_one_in_sight', **environment)


	def calculate_power_balance(self, ai_ships, enemy_ships):
		pass

	def tick(self):
		self.lookout()

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls, owner)
		#self._load(db, player)
		return self

	#TODO add save/load mechanisms
