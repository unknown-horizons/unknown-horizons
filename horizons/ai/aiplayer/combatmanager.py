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
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip


class CombatManager(WorldObject):
	"""
	CombatManager objects is responsible for handling close combat in game.
	"""
	log = logging.getLogger("ai.aiplayer.combatmanager")

	def __init__(self, owner):
		super(CombatManager,self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.enemies_in_range = []

	def lookout(self):
		unit_manager = self.owner.unit_manager
		for ship_group in unit_manager.ship_groups:
			enemies = unit_manager.find_ships_near_group(ship_group)
			if enemies:
				self.enemies_in_range.append((ship_group, enemies))

	def attack(self):
		for ship_group, enemies in self.enemies_in_range:
			if not self.session.world.diplomacy.are_enemies(self.owner, enemies[0]):
				AddEnemyPair(self.owner, enemies[0].owner).execute(self.session)
			for ship in ship_group:
				Attack(ship, enemies[0])

	def tick(self):
		self.lookout()
		self.attack()

	#TODO add save/load mechanisms

