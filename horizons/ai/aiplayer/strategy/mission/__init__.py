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

from horizons.ai.aiplayer.mission import Mission
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject


class FleetMission(Mission):

	missionStates = Enum('created', 'fleeing_home')

	# db_table name has to be overwritten by the concrete mission

	log = logging.getLogger("ai.aiplayer.fleetmission")

	def __init__(self, success_callback, failure_callback, ships):
		assert ships, "Attempt to create a fleet mission out of 0 ships"
		super(FleetMission, self).__init__(success_callback, failure_callback, ships[0].owner)
		self.__init()
		self._init_fleet(ships)

	def __init(self):
		self.unit_manager = self.owner.unit_manager
		self.session = self.owner.session
		self.strategy_manager = self.owner.strategy_manager
		self.combat_phase = False
		self.state = self.missionStates.created

		# combatIntermissions states which function should be called after combat phase was finished (winning or losing).
		# each combatIntermission entry should provide both, It is the CombatManager that decides which function to call
		# Dictionary of type: missionState => (won_function, lost_function)
		self.combatIntermissions = {}

		# _state_fleet_callbacks states which callback is supposed to be called by the fleet when it reaches the target point
		# based on given mission state. Used when changing mission (initiating new mission phase) states and loading game (restarting mission from given state)
		# Dictionary of type: missionState => Callback object
		self._state_fleet_callbacks = {}

	def _init_fleet(self, ships):
		self.fleet = self.unit_manager.create_fleet(ships=ships, destroy_callback=Callback(self.cancel, "All ships were destroyed"))
		for ship in self.fleet.get_ships():
			self.owner.ships[ship] = self.owner.shipStates.on_a_mission

	def save(self, db):
		super(FleetMission, self).save(db)
		db("INSERT INTO ai_fleet_mission (rowid, owner_id, fleet_id, state_id, combat_phase) VALUES(?, ?, ?, ?, ?)", self.worldid,
			self.owner.worldid, self.fleet.worldid, self.state.index, self.combat_phase)

	@classmethod
	def load(cls, worldid, owner, db, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(worldid, owner, db, success_callback, failure_callback)
		self._initialize_mission()
		return self

	def _load(self, db, worldid, success_callback, failure_callback, owner):
		super(FleetMission, self).load(db, worldid, success_callback, failure_callback, owner)
		self.__init()

		fleet_id, state_id, combat_phase = db("SELECT fleet_id, state_id, combat_phase FROM ai_fleet_mission WHERE rowid = ?", worldid)[0]

		self.fleet = WorldObject.get_object_by_id(fleet_id)
		self.state = self.missionStates[state_id]
		self.combat_phase = bool(combat_phase)

	def _initialize_mission(self):
		"""
		Initializes mission after loading is finished.
		"""

		# Add move callback for fleet, dependent on loaded fleet state
		if self.state in self._state_fleet_callbacks:
			self.fleet.callback = self._state_fleet_callbacks[self.state]

		# Add destroy callback, the same for every case of fleet being destroyed
		self.fleet.destroy_callback = Callback(self.cancel, "All ships were destroyed")

	def _dismiss_fleet(self):
		for ship in self.fleet.get_ships():
			self.owner.ships[ship] = self.owner.shipStates.idle
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

	def pause_mission(self):
		self.log.debug("Player %s, Mission %s, pausing mission at state %s", self.owner.name, self.__class__.__name__, self.state)
		self.combat_phase = True
		for ship in self.fleet.get_ships():
			ship.stop()

	# continue / abort methods are called by CombatManager after it handles combat.
	# CombatManager decides whether the battle was successful (and if the mission should be continued) or unsuccessful (mission should be aborted)
	def continue_mission(self):
		assert self.combat_phase, "request to continue mission without it being in combat_phase in the first place"
		assert self.state in self.combatIntermissions, "request to continue mission from not defined state: %s" % self.state
		self.log.debug("Player %s, Mission %s, continuing mission at state %s", self.owner.name, self.__class__.__name__, self.state)
		self.combat_phase = False
		self.combatIntermissions[self.state][0]()

	def abort_mission(self, msg):
		assert self.combat_phase, "request to abort mission without it being in combat_phase in the first place"
		assert self.state in self.combatIntermissions, "request to abort mission from not defined state: %s" % self.state
		self.log.debug("Player %s, Mission %s, aborting mission at state %s", self.owner.name, self.__class__.__name__, self.state)
		self.combat_phase = False
		self.combatIntermissions[self.state][1]()

	def cancel(self, msg):
		self.report_failure(msg)

	def __str__(self):
		return super(FleetMission, self).__str__() + \
		(' using %s' % (self.fleet if hasattr(self, 'fleet') else 'unknown fleet')) + \
		('(mission state:%s,' % (self.state if hasattr(self, 'state') else 'unknown state')) + \
		('combat_phase:%s)' % (self.combat_phase if hasattr(self, 'combat_phase') else 'N/A'))
