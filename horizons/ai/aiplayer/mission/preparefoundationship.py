# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Point, Circle, Callback, WorldObject
from horizons.util.python import decorators
from horizons.constants import BUILDINGS
from horizons.ext.enum import Enum

class PrepareFoundationShip(Mission):
	"""
	Given a ship and a settlement manager it moves the ship to the branch office and loads
	it with the resources required to start another settlement.
	"""

	missionStates = Enum('created', 'moving')

	def __init__(self, settlement_manager, ship, success_callback, failure_callback, **kwargs):
		super(PrepareFoundationShip, self).__init__(success_callback, failure_callback, \
			settlement_manager.land_manager.island.session, **kwargs)
		self.settlement_manager = settlement_manager
		self.ship = ship
		self.branch_office = self.settlement_manager.branch_office
		self.state = self.missionStates.created

	def save(self, db):
		super(PrepareFoundationShip, self).save(db)
		db("INSERT INTO ai_mission_prepare_foundation_ship(rowid, settlement_manager, ship, state) VALUES(?, ?, ?, ?)", \
			self.worldid, self.settlement_manager.worldid, self.ship.worldid, self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT settlement_manager, ship, state FROM ai_mission_prepare_foundation_ship WHERE rowid = ?", worldid)[0]
		self.settlement_manager = WorldObject.get_object_by_id(db_result[0])
		self.ship = WorldObject.get_object_by_id(db_result[1])
		self.branch_office = self.settlement_manager.branch_office
		self.state = self.missionStates[db_result[2]]
		super(PrepareFoundationShip, self).load(db, worldid, success_callback, failure_callback, \
			self.settlement_manager.land_manager.island.session)

		if self.state == self.missionStates.moving:
			self.ship.add_move_callback(Callback(self._reached_bo_area))
			self.ship.add_blocked_callback(Callback(self._move_to_bo_area))

	def start(self):
		self.state = self.missionStates.moving
		self._move_to_bo_area()

	def _move_to_bo_area(self):
		(x, y) = self.branch_office.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, Callback(self._reached_bo_area), blocked_callback = Callback(self._move_to_bo_area))
		except MoveNotPossible:
			self.report_failure('Move not possible')

	def _reached_bo_area(self):
		self.log.info('Reached BO area')
		self.ship.owner.complete_inventory.load_foundation_resources(self.ship, \
			self.settlement_manager.land_manager.settlement)
		if self.settlement_manager.owner.have_starting_resources(self.ship, None):
			self.report_success('Transferred enough foundation resources to the ship')
		else:
			self.report_failure('Not enough foundation resources available')

decorators.bind_all(PrepareFoundationShip)
