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
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.shapes.point import Point
from horizons.util.worldobject import WorldObject

from horizons.world.units.movingobject import MoveNotPossible
from horizons.util.python import decorators


class ScoutingMission(FleetMission):
	"""
	This is an example of a scouting mission.
	Send ship from point A to point B, and then to point A again.
	1. Send fleet to a point on the map
	2. Fleet returns to starting position of ships[0] (first ship)
	"""
	missionStates = Enum.get_extended(FleetMission.missionStates, 'sailing_to_target', 'going_back')

	def __init__(self, success_callback, failure_callback, ships, target_point):
		super(ScoutingMission, self).__init__(success_callback, failure_callback, ships)
		self.__init(target_point, ships[0].position.copy())

	def __init(self, target_point, starting_point):
		self.target_point = target_point
		self.starting_point = starting_point

		self.combatIntermissions = {
			self.missionStates.sailing_to_target: (self.sail_to_target, self.flee_home),
			self.missionStates.going_back: (self.go_back, self.flee_home),
			self.missionStates.fleeing_home: (self.flee_home, self.flee_home),
		}

		self._state_fleet_callbacks = {
			self.missionStates.sailing_to_target: Callback(self.go_back),
			self.missionStates.going_back: Callback(self.report_success, "Ships arrived at the target"),
			self.missionStates.fleeing_home: Callback(self.report_failure, "Combat was lost, ships fled home successfully"),
		}

	def start(self):
		self.sail_to_target()

	def save(self, db):
		super(ScoutingMission, self).save(db)
		db("INSERT INTO ai_scouting_mission (rowid, starting_point_x, starting_point_y, target_point_x, target_point_y) VALUES(?, ?, ?, ?, ?)",
			self.worldid, self.starting_point.x, self.starting_point.y, self.target_point.x, self.target_point.y)

	def _load(self, worldid, owner, db, success_callback, failure_callback):
		super(ScoutingMission, self)._load(db, worldid, success_callback, failure_callback, owner)
		db_result = db("SELECT target_point_x, target_point_y, starting_point_x, starting_point_y FROM ai_scouting_mission WHERE rowid = ?", worldid)[0]
		self.__init(Point(*db_result[:2]), Point(*db_result[2:]))

	def go_back(self):
		"""
		Going back home after successfully reaching the target point.
		"""
		try:
			self.fleet.move(self.starting_point, self._state_fleet_callbacks[self.missionStates.going_back])
			self.state = self.missionStates.going_back
		except MoveNotPossible:
			self.report_failure("Move was not possible when going back")

	def flee_home(self):
		"""
		Fleeing home after severe casualties.
		"""
		if self.fleet.size() > 0:
			try:
				self.fleet.move(self.starting_point, self._state_fleet_callbacks[self.missionStates.fleeing_home])
				self.state = self.missionStates.fleeing_home
			except MoveNotPossible:
				self.report_failure("Combat was lost, ships couldn't flee home")
		else:
			self.report_failure("Combat was lost, all ships were wiped out")

	def sail_to_target(self):
		if not self.target_point:
			self.target_point = self.owner.session.world.get_random_possible_ship_position()
		try:
			self.fleet.move(self.target_point, self._state_fleet_callbacks[self.missionStates.sailing_to_target])
			self.state = self.missionStates.sailing_to_target
		except MoveNotPossible:
			self.report_failure("Move was not possible when moving to target")

	@classmethod
	def create(cls, success_callback, failure_callback, ships, target_point=None):
		return ScoutingMission(success_callback, failure_callback, ships, target_point)

decorators.bind_all(ScoutingMission)
