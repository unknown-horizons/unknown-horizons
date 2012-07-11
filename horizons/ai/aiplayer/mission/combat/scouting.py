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

from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Point, Circle, WorldObject
from horizons.util.python import decorators
from horizons.constants import BUILDINGS
from horizons.component.storagecomponent import StorageComponent


class ScoutingMission(Mission):
	"""
	This is an example of a scouting mission.
	Send ship from point A to point B, and then to point A again.
	"""
	missionStates = Enum('created', 'sailing_to_target', 'going_back')
	target_point_range = 5
	starting_point_range = 5

	def __init__(self, success_callback, failure_callback, ship, target_point):
		super(ScoutingMission, self).__init__(success_callback, failure_callback, ship.owner)
		self.__init(ship, target_point)

	def __init(self, ship, target_point):
		self.ship = ship
		self.target_point = target_point
		self.ship.add_remove_listener(self.cancel)

	def save(self, db):
		super(ScoutingMission, self).save(db)
		db("INSERT INTO ai_mission_scouting(rowid, owner, ship, starting_point_x, starting_point_y, target_point_x, target_point_y, state) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", \
			self.worldid, self.owner.worldid, self.ship.worldid, self.starting_point.x, self.starting_point.y, self.target_point.x, self.target_point.y, self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT owner, ship, starting_point_x, starting_point_y, target_point_x, target_point_y, state FROM ai_mission_scouting WHERE rowid = ?", worldid)[0]
		owner = WorldObject.get_object_by_id(db_result[0])
		self.ship = WorldObject.get_object_by_id(db_result[1])
		self.starting_point = Point(db_result[2], db_result[3])
		self.target_point = Point(db_result[4], db_result[5])
		self.state = self.missionStates[db_result[6]]
		super(ScoutingMission, self).load(db, worldid, success_callback, failure_callback, owner)

		if self.state == self.missionStates.sailing_to_target:
			self.ship.add_move_callback(Callback(self.go_back))
		elif self.state == self.missionStates.going_back:
			self.ship.add_move_callback(Callback(self.report_success, "Scouting mission successful "))
		else:
			assert False, 'invalid state'

	def cancel(self):
		self.ship.stop()
		super(ScoutingMission, self).cancel()

	def start(self):
		self.state = self.missionStates.sailing_to_target
		self.set_off()

	def go_back(self):
		try:
			self.ship.move(Circle(self.starting_point, self.starting_point_range), Callback(self.report_success,"Scouting mission was a success"))
		except MoveNotPossible:
			self.report_failure("Couldn't move")

	def set_off(self):
		if not self.target_point:
			self.target_point = self.owner.session.world.get_random_possible_ship_position()

		self.starting_point = self.ship.position

		try:
			self.ship.move(Circle(self.target_point, self.target_point_range), Callback(self.go_back))
		except MoveNotPossible:
			self.report_failure("Couldn't move")

	@classmethod
	def create(cls, success_callback, failure_callback, ship, target_point=None):
		return ScoutingMission(success_callback, failure_callback, ship, target_point)

decorators.bind_all(ScoutingMission)