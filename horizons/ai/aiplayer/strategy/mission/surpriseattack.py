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
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.shapes.circle import Circle
from horizons.util.shapes.point import Point
from horizons.util.worldobject import WorldObject

from horizons.world.units.movingobject import MoveNotPossible
from horizons.util.python import decorators


class SurpriseAttack(FleetMission):
	"""
	This is a basic attack mission.
	1. Send fleet to a Point (or Circle) A
	2. Break diplomacy with enemy player P if he is not hostile,
	3. Begin combat phase
	4. Return home (point B).
	"""

	missionStates = Enum.get_extended(FleetMission.missionStates, 'sailing_to_target', 'in_combat', 'breaking_diplomacy', 'going_back')

	def __init__(self, success_callback, failure_callback, ships, target_point, return_point, enemy_player):
		super(SurpriseAttack, self).__init__(success_callback, failure_callback, ships)
		self.__init(target_point, return_point, enemy_player)

	def __init(self, target_point, return_point, enemy_player):
		self.target_point = target_point
		self.return_point = return_point
		self.enemy_player = enemy_player

		self.combatIntermissions = {
			self.missionStates.sailing_to_target: (self.sail_to_target, self.flee_home),
			self.missionStates.in_combat: (self.go_back, self.flee_home),
			self.missionStates.going_back: (self.go_back, self.flee_home),
			self.missionStates.breaking_diplomacy: (self.break_diplomacy, self.flee_home),
			self.missionStates.fleeing_home: (self.flee_home, self.flee_home),
		}

		# Fleet callbacks corresponding to given state
		self._state_fleet_callbacks = {
			self.missionStates.sailing_to_target: Callback(self.break_diplomacy),
			self.missionStates.going_back: Callback(self.report_success, "Ships arrived at return point"),
			self.missionStates.fleeing_home: Callback(self.report_failure, "Combat was lost, ships fled home successfully"),
		}

	def save(self, db):
		super(SurpriseAttack, self).save(db)
		db("INSERT INTO ai_mission_surprise_attack (rowid, enemy_player_id, target_point_x, target_point_y, target_point_radius, "
			"return_point_x, return_point_y) VALUES(?, ?, ?, ?, ?, ?, ?)", self.worldid, self.enemy_player.worldid, self.target_point.center.x,
			self.target_point.center.y, self.target_point.radius, self.return_point.x, self.return_point.y)

	def _load(self, worldid, owner, db, success_callback, failure_callback):
		super(SurpriseAttack, self)._load(db, worldid, success_callback, failure_callback, owner)
		db_result = db("SELECT enemy_player_id, target_point_x, target_point_y, target_point_radius, return_point_x, return_point_y "
						"FROM ai_mission_surprise_attack WHERE rowid = ?", worldid)[0]
		enemy_player_id, target_point_x, target_point_y, target_point_radius, return_point_x, return_point_y = db_result

		target_point = Circle(Point(target_point_x, target_point_y), target_point_radius)
		return_point = Point(return_point_x, return_point_y)
		enemy_player = WorldObject.get_object_by_id(enemy_player_id)
		self.__init(target_point, return_point, enemy_player)

	def start(self):
		self.sail_to_target()

	def sail_to_target(self):
		self.log.debug("Player %s, Mission %s, 1/4 set off from point %s to point %s", self.owner.name, self.__class__.__name__, self.return_point, self.target_point)
		try:
			self.fleet.move(self.target_point, self._state_fleet_callbacks[self.missionStates.sailing_to_target])
			self.state = self.missionStates.sailing_to_target
		except MoveNotPossible:
			self.report_failure("Move was not possible when moving to target")

	def break_diplomacy(self):
		self.state = self.missionStates.breaking_diplomacy
		self.log.debug("Player %s, Mission %s, 2/4 breaking diplomacy with Player %s", self.owner.name, self.__class__.__name__, self.enemy_player.name)
		if not self.session.world.diplomacy.are_enemies(self.owner, self.enemy_player):
			AddEnemyPair(self.owner, self.enemy_player).execute(self.session)
		self.in_combat()

	def in_combat(self):
		self.combat_phase = True
		self.log.debug("Player %s, Mission %s, 3/4 in combat", self.owner.name, self.__class__.__name__)
		self.state = self.missionStates.in_combat

	def go_back(self):
		self.log.debug("Player %s, Mission %s, 4/4 going back after combat to point %s", self.owner.name, self.__class__.__name__, self.return_point)
		try:
			self.fleet.move(self.return_point, self._state_fleet_callbacks[self.missionStates.going_back])
			self.state = self.missionStates.going_back
		except MoveNotPossible:
			self.report_failure("Move was not possible when going back")

	def flee_home(self):
		if self.fleet.size() > 0:
			try:
				self.fleet.move(self.return_point, self._state_fleet_callbacks[self.missionStates.fleeing_home])
				self.state = self.missionStates.fleeing_home
			except MoveNotPossible:
				self.report_failure("Combat was lost, ships couldn't flee home")
		else:
			self.report_failure("Combat was lost, all ships were wiped out")

	@classmethod
	def create(cls, success_callback, failure_callback, fleet, target_point, return_point, enemy_player):
		return SurpriseAttack(success_callback, failure_callback, fleet, target_point, return_point, enemy_player)

decorators.bind_all(SurpriseAttack)
