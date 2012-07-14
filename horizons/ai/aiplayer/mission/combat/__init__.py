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
from horizons.ai.aiplayer.mission import Mission
from horizons.ext.enum import Enum

class FleetMission(Mission):

	missionStates = Enum('created')


	def __init__(self, success_callback, failure_callback, ships):
		super(FleetMission, self).__init__(success_callback, failure_callback, ships[0].owner)
		self.__init(ships)
		self.state = self.missionStates.created

		# flag stating whether mission is currently waiting for CombatManager to finish combat (CombatManager either cancels the mission or continues it).
		self.combat_phase = False

		# flag stating whether CombatManager can initiate combat when enemy approaches in the horizon.
		self.can_interfere = False

	def __init(self, ships):
		self.unit_manager = self.owner.unit_manager
		self.session = self.owner.session
		self.fleet = self.unit_manager.create_fleet(ships)
		self.strategy_manager = self.owner.strategy_manager
		for ship in self.fleet.get_ships():
			self.owner.ships[ship] = self.owner.shipStates.on_a_mission
			ship.add_remove_listener(self.lost_ship)

		# combatIntermissions is dictionary of type 'missionState -> (won_function, lost_function)' stating which function should be called after combat was finished in state X.
		self.combatIntermissions = {}

	def _dismiss_fleet(self):
		for ship in self.fleet.get_ships():
			self.owner.ships[ship] = self.owner.shipStates.idle
			ship.remove_remove_listener(self.lost_ship)
			ship.stop()
		self.unit_manager.destroy_fleet(self.fleet)

	def report_success(self, msg):
		self._dismiss_fleet()
		self.success_callback(self, msg)

	def report_failure(self, msg):
		self._dismiss_fleet()
		self.failure_callback(self, msg)

	def lost_ship(self):
		if self.fleet.size() == 0:
			self.cancel('Lost all of the ships')

	# continue / abort methods are called by CombatManager after it handles combat.
	# CombatManager decides whether the battle was successful (and the mission should be continued) or unsuccessful (mission should be aborted)
	def continue_mission(self):
		assert self.combat_phase, "request to continue mission without it being in combat_phase in the first place"
		assert self.state in self.combatIntermissions, "request to continue mission from not defined state: %s" % self.state
		self.combatIntermissions[self.state][0]()

	def abort_mission(self, msg):
		assert self.combat_phase, "request to abort mission without it being in combat_phase in the first place"
		assert self.state in self.combatIntermissions, "request to abort mission from not defined state: %s" % self.state
		self.combatIntermissions[self.state][1]()

	def cancel(self, msg):
		self.report_failure(msg)

	def __str__(self):
		return super(FleetMission, self).__str__() + (' using %s' % (self.fleet if hasattr(self, 'fleet') else 'unknown fleet'))
