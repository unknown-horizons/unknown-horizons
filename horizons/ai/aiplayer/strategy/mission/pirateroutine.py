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
from horizons.util.shapes.point import Point
from horizons.util.worldobject import WorldObject

from horizons.world.units.movingobject import MoveNotPossible
from horizons.util.python import decorators


class PirateRoutine(FleetMission):
	"""
	Never ending mission of:
	1. Start moving to random places.
	2. Chase nearby ships along the way.
	3. Go back home
	"""

	missionStates = Enum.get_extended(FleetMission.missionStates, 'sailing_to_target', 'chasing_ship', 'going_home')

	# range at which the ship is considered "caught"
	caught_range = 5

	def __init__(self, success_callback, failure_callback, ships):
		super(PirateRoutine, self).__init__(success_callback, failure_callback, ships)
		self.__init()

	def __init(self):
		self.target_point = self.owner.session.world.get_random_possible_ship_position()

		self.combatIntermissions = {
			self.missionStates.sailing_to_target: (self.sail_to_target, self.flee_home),
			self.missionStates.chasing_ship: (self.chase_ship, self.flee_home),
			self.missionStates.going_home: (self.go_home, self.flee_home),
			self.missionStates.fleeing_home: (self.flee_home, self.flee_home),
		}

		self._state_fleet_callbacks = {
			self.missionStates.sailing_to_target: Callback(self.go_home),
			self.missionStates.chasing_ship: Callback(self.chase_ship),
			self.missionStates.going_home: Callback(self.report_success, "Pirate routine ended successfully"),
			self.missionStates.fleeing_home: Callback(self.report_failure, "Mission was a failure, ships fled home successfully"),
		}

	def save(self, db):
		super(PirateRoutine, self).save(db)
		db("INSERT INTO ai_mission_pirate_routine (rowid, target_point_x, target_point_y) VALUES(?, ?, ?)", self.worldid,
			self.target_point.x, self.target_point.y)

	def _load(self, worldid, owner, db, success_callback, failure_callback):
		super(PirateRoutine, self)._load(db, worldid, success_callback, failure_callback, owner)
		db_result = db("SELECT target_point_x, target_point_y FROM ai_mission_pirate_routine WHERE rowid = ?", worldid)[0]

		self.target_point = Point(*db_result)

		self.__init()

	def start(self):
		self.sail_to_target()

	def sail_to_target(self):
		self.log.debug("Pirate %s, Mission %s, 1/2 set off to random point at %s", self.owner.name, self.__class__.__name__, self.target_point)
		try:
			self.fleet.move(self.target_point, self._state_fleet_callbacks[self.missionStates.sailing_to_target])
			self.state = self.missionStates.sailing_to_target
		except MoveNotPossible:
			self.report_failure("Move was not possible when moving to target")

	def go_home(self):
		self.log.debug("Pirate %s, Mission %s, 2/2 going home at point %s", self.owner.name, self.__class__.__name__, self.owner.home_point)
		try:
			self.fleet.move(self.owner.home_point, self._state_fleet_callbacks[self.missionStates.going_home])
			self.state = self.missionStates.going_home
		except MoveNotPossible:
			self.report_failure("Pirate: %s, Mission: %s, Pirate ship couldn't go home." % (self.owner.name, self.__class__.__name__))

	def chase_ship(self):
		pass

	def flee_home(self):
		# check if fleet still exists
		if self.fleet.size() > 0:
			try:
				self.fleet.move(self.owner.home_point, self._state_fleet_callbacks[self.missionStates.fleeing_home])
				self.state = self.missionStates.fleeing_home
			except MoveNotPossible:
				self.report_failure("Pirate: %s, Mission: %s, Pirate ship couldn't flee home after combat" % (self.owner.name, self.__class__.__name__))
		else:
			self.report_failure("Combat was lost, all ships were wiped out")

	@classmethod
	def create(cls, success_callback, failure_callback, ships):
		return PirateRoutine(success_callback, failure_callback, ships)

decorators.bind_all(PirateRoutine)
