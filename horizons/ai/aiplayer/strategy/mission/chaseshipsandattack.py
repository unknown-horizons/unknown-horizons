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

from horizons.ai.aiplayer.strategy.mission import FleetMission
from horizons.command.diplomacy import AddEnemyPair
from horizons.component.namedcomponent import NamedComponent
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.shapes.circle import Circle
from horizons.util.worldobject import WorldObject

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
	target_range = 5

	def __init__(self, success_callback, failure_callback, ships, target_ship):
		super(ChaseShipsAndAttack, self).__init__(success_callback, failure_callback, ships)
		self.__init(target_ship)

	def __init(self, target_ship):
		self.target_ship = target_ship

		self.combatIntermissions = {
			self.missionStates.sailing_to_target: (self.sail_to_target, self.flee_home),
			self.missionStates.in_combat: (self.check_ship_alive, self.flee_home),
			self.missionStates.fleeing_home: (self.flee_home, self.flee_home),
		}

		self._state_fleet_callbacks = {
			self.missionStates.sailing_to_target: Callback(self.was_reached),
			self.missionStates.fleeing_home: Callback(self.report_failure, "Combat was lost, ships fled home successfully"),
		}

	def save(self, db):
		super(ChaseShipsAndAttack, self).save(db)
		db("INSERT INTO ai_mission_chase_ships_and_attack (rowid, target_ship_id) VALUES(?, ?)", self.worldid, self.target_ship.worldid)

	def _load(self, worldid, owner, db, success_callback, failure_callback):
		super(ChaseShipsAndAttack, self)._load(db, worldid, success_callback, failure_callback, owner)
		(target_ship_id,) = db("SELECT target_ship_id FROM ai_mission_chase_ships_and_attack WHERE rowid = ?", worldid)[0]

		target_ship = WorldObject.get_object_by_id(target_ship_id)
		self.__init(target_ship)

	def start(self):
		self.sail_to_target()

	def sail_to_target(self):
		self.log.debug("Player %s, Mission %s, 1/2 set off to ship %s at %s", self.owner.name, self.__class__.__name__,
			self.target_ship.get_component(NamedComponent).name, self.target_ship.position)
		try:
			self.fleet.move(Circle(self.target_ship.position, self.target_range), self._state_fleet_callbacks[self.missionStates.sailing_to_target])
			self.state = self.missionStates.sailing_to_target
		except MoveNotPossible:
			self.report_failure("Move was not possible when moving to target")

	def was_reached(self):
		if self.target_ship.in_ship_map:
			if any((ship.position.distance(self.target_ship.position) <= self.target_range + 1 for ship in self.fleet.get_ships())):
				# target ship reached: execute combat
				self.state = self.missionStates.in_combat
				self.in_combat()
			else:
				# target ship was not reached: sail again
				self.state = self.missionStates.sailing_to_target
				self.sail_to_target()
		else:
			# ship was destroyed
			self.report_success("Ship was destroyed")

	def check_ship_alive(self):
		if self.target_ship.in_ship_map:
			self.was_reached()
		else:
			self.report_success("Target ship was eliminated")

	def in_combat(self):
		if not self.session.world.diplomacy.are_enemies(self.owner, self.target_ship.owner):
			self.report_failure("Target ship was not hostile. Aborting mission.")
			return
		self.combat_phase = True
		self.log.debug("Player %s, Mission %s, 2/2 in combat", self.owner.name, self.__class__.__name__)
		self.state = self.missionStates.in_combat

	def flee_home(self):
		# check if fleet still exists
		if self.fleet.size() > 0:
			try:
				home_settlement = self.owner.settlements[0]
				return_point = self.unit_manager.get_warehouse_area(home_settlement, 10)
				self.fleet.move(return_point, self._state_fleet_callbacks[self.missionStates.fleeing_home])
				self.state = self.missionStates.fleeing_home
			except MoveNotPossible:
				self.report_failure("Combat was lost, ships couldn't flee home")
		else:
			self.report_failure("Combat was lost, all ships were wiped out")

	@classmethod
	def create(cls, success_callback, failure_callback, fleet, target_ship):
		return ChaseShipsAndAttack(success_callback, failure_callback, fleet, target_ship)

decorators.bind_all(ChaseShipsAndAttack)
