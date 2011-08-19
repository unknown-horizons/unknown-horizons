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

class DomesticTrade(Mission):
	"""
	Given a ship and two settlement managers the ship is taken to the first one,
	loaded with resources, and then moved to the other one to unload the resources.
	"""

	missionStates = Enum('created', 'moving_to_source_bo', 'moving_to_destination_bo')

	def __init__(self, source_settlement_manager, destination_settlement_manager, ship, success_callback, failure_callback, **kwargs):
		super(DomesticTrade, self).__init__(success_callback, failure_callback, \
			source_settlement_manager.land_manager.island.session, **kwargs)
		self.source_settlement_manager = source_settlement_manager
		self.destination_settlement_manager = destination_settlement_manager
		self.ship = ship
		self.state = self.missionStates.created
		self.ship.add_remove_listener(self.cancel)

	def save(self, db):
		super(DomesticTrade, self).save(db)
		db("INSERT INTO ai_mission_domestic_trade(rowid, source_settlement_manager, destination_settlement_manager, ship, state) VALUES(?, ?, ?, ?, ?)", \
			self.worldid, self.source_settlement_manager.worldid, self.destination_settlement_manager.worldid, self.ship.worldid, self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT source_settlement_manager, destination_settlement_manager, ship, state FROM ai_mission_domestic_trade WHERE rowid = ?", worldid)[0]
		self.source_settlement_manager = WorldObject.get_object_by_id(db_result[0])
		self.destination_settlement_manager = WorldObject.get_object_by_id(db_result[1])
		self.ship = WorldObject.get_object_by_id(db_result[2])
		self.state = self.missionStates[db_result[3]]
		super(DomesticTrade, self).load(db, worldid, success_callback, failure_callback, self.source_settlement_manager.session)

		if self.state == self.missionStates.moving_to_source_bo:
			self.ship.add_move_callback(Callback(self._reached_source_bo_area))
			self.ship.add_blocked_callback(Callback(self._move_to_source_bo_area))
		elif self.state == self.missionStates.moving_to_destination_bo:
			self.ship.add_move_callback(Callback(self._reached_destination_bo_area))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_bo_area))

		self.ship.add_remove_listener(self.cancel)

	def report_success(self, msg):
		self.ship.remove_remove_listener(self.cancel)
		super(DomesticTrade, self).report_success(msg)

	def report_failure(self, msg):
		self.ship.remove_remove_listener(self.cancel)
		super(DomesticTrade, self).report_failure(msg)

	def start(self):
		self.state = self.missionStates.moving_to_source_bo
		self._move_to_source_bo_area()

	def _move_to_source_bo_area(self):
		(x, y) = self.source_settlement_manager.branch_office.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, Callback(self._reached_source_bo_area), blocked_callback = Callback(self._move_to_source_bo_area))
		except MoveNotPossible:
			self.report_failure('First move not possible')

	def _reached_source_bo_area(self):
		self.log.info('Reached the source branch office area')
		if self.source_settlement_manager.trade_manager.load_resources(self.destination_settlement_manager, self.ship):
			self.log.info('Loaded resources')
			self.state = self.missionStates.moving_to_destination_bo
			self._move_to_destination_bo_area()
		else:
			self.report_failure('No need for the ship at the source branch office')

	def _move_to_destination_bo_area(self):
		(x, y) = self.destination_settlement_manager.branch_office.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, Callback(self._reached_destination_bo_area), blocked_callback = Callback(self._move_to_destination_bo_area))
		except MoveNotPossible:
			self.report_failure('Second move not possible')

	def _reached_destination_bo_area(self):
		self.log.info('Reached destination branch office area')
		self.ship.owner.complete_inventory.unload_all(self.ship, self.destination_settlement_manager.settlement)
		self.report_success('Unloaded resources')

	def cancel(self):
		self.ship.stop()
		super(DomesticTrade, self).cancel()

decorators.bind_all(DomesticTrade)
