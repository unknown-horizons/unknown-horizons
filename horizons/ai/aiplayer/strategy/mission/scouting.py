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
		self.__init(target_point, ships)

	def __init(self, target_point, ships):
		self.target_point = target_point
		self.starting_point = ships[0].position.copy()

	def start(self):
		self.set_off()

	def go_back(self):
		try:
			self.fleet.move(self.starting_point, Callback(self.report_success, "Ships arrived at target"))
			self.state = self.missionStates.going_back
		except MoveNotPossible:
			self.report_failure("Move was not possible when going back")

	def set_off(self):
		if not self.target_point:
			self.target_point = self.owner.session.world.get_random_possible_ship_position()
		try:
			self.fleet.move(self.target_point, Callback(self.go_back))
			self.state = self.missionStates.sailing_to_target
		except MoveNotPossible:
			self.report_failure("Move was not possible when moving to target")

	@classmethod
	def create(cls, success_callback, failure_callback, ships, target_point=None):
		return ScoutingMission(success_callback, failure_callback, ships, target_point)

decorators.bind_all(ScoutingMission)
