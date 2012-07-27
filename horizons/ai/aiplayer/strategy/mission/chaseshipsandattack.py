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

from horizons.ai.aiplayer.mission.combat import FleetMission
from horizons.command.diplomacy import AddEnemyPair
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback

from horizons.world.units.movingobject import MoveNotPossible
from horizons.util.python import decorators


class ChaseShipsAndAttack(FleetMission):
	"""
	This is one of the basic attack missions.
	1. Sail to given ship on the map until the fleet is in close range
	2. Begin combat phase
	3. go to 1 if ship is still alive

	This mission may work the best for 2 ships fleet
	"""

	missionStates = Enum.get_extended(FleetMission.missionStates, 'sailing_to_target', 'in_combat')

	def __init__(self, success_callback, failure_callback, ships, target_point, return_point, enemy_player):
		super(ChaseShipsAndAttack, self).__init__(success_callback, failure_callback, ships)
		self.__init(target_point, return_point, enemy_player)

	def __init(self, target_point, return_point, enemy_player):
		self.target_point = target_point
		self.return_point = return_point
		self.enemy_player = enemy_player

		self.combatIntermissions = {
			self.missionStates.sailing_to_target: (self.set_off, self.flee_home),
			self.missionStates.in_combat: (self.go_back, self.flee_home),
			self.missionStates.going_back: (self.go_back, self.flee_home),
			self.missionStates.breaking_diplomacy: (self.break_diplomacy, self.flee_home),
		}

	def start(self):
		self.set_off()

	def set_off(self):
		self.log.debug("Player %s, Mission %s, 1/4 set off from point %s to point %s" % (self.owner.name, self.__class__.__name__, self.return_point, self.target_point))
		try:
			self.fleet.move(self.target_point, Callback(self.break_diplomacy))
			self.state = self.missionStates.sailing_to_target
		except MoveNotPossible:
			self.report_failure("Move was not possible when moving to target")

	def break_diplomacy(self):
		self.state = self.missionStates.breaking_diplomacy
		self.log.debug("Player %s, Mission %s, 2/4 breaking diplomacy with Player %s" % (self.owner.name, self.__class__.__name__, self.enemy_player.name))
		if not self.session.world.diplomacy.are_enemies(self.owner, self.enemy_player):
			AddEnemyPair(self.owner, self.enemy_player).execute(self.session)
		self.in_combat()

	def in_combat(self):
		self.combat_phase = True
		self.log.debug("Player %s, Mission %s, 3/4 in combat" % (self.owner.name, self.__class__.__name__))
		self.state = self.missionStates.in_combat
		# TODO: turn combat_phase into a Property and check whether current state is a key self.combatIntermission

	def go_back(self):
		self.log.debug("Player %s, Mission %s, 4/4 going back after combat to point %s" % (self.owner.name, self.__class__.__name__, self.return_point))
		try:
			self.fleet.move(self.return_point, Callback(self.report_success, "Ships arrived at return point"))
			self.state = self.missionStates.going_back
		except MoveNotPossible:
			self.report_failure("Move was not possible when going back")

	def flee_home(self):
		# check if fleet still exists
		if self.fleet.size() > 0:
			try:
				self.fleet.move(self.return_point, Callback(self.report_failure, "Combat was lost, ships fled home successfully"))
				self.state = self.missionStates.going_back
			except MoveNotPossible:
				self.report_failure("Combat was lost, ships couldn't flee home")
		else:
			self.report_failure("Combat was lost, all ships were wiped out")

	@classmethod
	def create(cls, success_callback, failure_callback, fleet, target_point, return_point, enemy_player):
		return ChaseShipsAndAttack(success_callback, failure_callback, fleet, target_point, return_point, enemy_player)

decorators.bind_all(ChaseShipsAndAttackAttack)