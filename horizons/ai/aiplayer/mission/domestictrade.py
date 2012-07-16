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

from horizons.ai.aiplayer.mission import ShipMission
from horizons.util import Callback, WorldObject
from horizons.util.python import decorators
from horizons.ext.enum import Enum

class DomesticTrade(ShipMission):
	"""
	Given a ship and two settlement managers the ship is taken to the first one,
	loaded with resources, and then moved to the other one to unload the resources.
	"""

	missionStates = Enum('created', 'moving_to_source_warehouse', 'moving_to_destination_warehouse')

	def __init__(self, source_settlement_manager, destination_settlement_manager, ship, success_callback, failure_callback):
		super(DomesticTrade, self).__init__(success_callback, failure_callback, ship)
		self.source_settlement_manager = source_settlement_manager
		self.destination_settlement_manager = destination_settlement_manager
		self.state = self.missionStates.created

	def save(self, db):
		super(DomesticTrade, self).save(db)
		db("INSERT INTO ai_mission_domestic_trade(rowid, source_settlement_manager, destination_settlement_manager, ship, state) VALUES(?, ?, ?, ?, ?)",
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
		self.state = self.missionStates[db_result[3]]
		super(DomesticTrade, self).load(db, worldid, success_callback, failure_callback, WorldObject.get_object_by_id(db_result[2]))

		if self.state == self.missionStates.moving_to_source_warehouse:
			self.ship.add_move_callback(Callback(self._reached_source_warehouse_area))
			self.ship.add_blocked_callback(Callback(self._move_to_source_warehouse_area))
		elif self.state == self.missionStates.moving_to_destination_warehouse:
			self.ship.add_move_callback(Callback(self._reached_destination_warehouse_area))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_warehouse_area))
		else:
			assert False, 'invalid state'

	def start(self):
		self.state = self.missionStates.moving_to_source_warehouse
		self._move_to_source_warehouse_area()

	def _move_to_source_warehouse_area(self):
		self._move_to_warehouse_area(self.source_settlement_manager.settlement.warehouse.position, Callback(self._reached_source_warehouse_area),
			Callback(self._move_to_source_warehouse_area), 'First move not possible')

	def _reached_source_warehouse_area(self):
		self.log.info('%s reached the source warehouse area', self)
		if self.source_settlement_manager.trade_manager.load_resources(self):
			self.log.info('%s loaded resources', self)
			self.state = self.missionStates.moving_to_destination_warehouse
			self._move_to_destination_warehouse_area()
		else:
			self.report_failure('No need for the ship at the source warehouse')

	def _move_to_destination_warehouse_area(self):
		self._move_to_warehouse_area(self.destination_settlement_manager.settlement.warehouse.position, Callback(self._reached_destination_warehouse_area),
			Callback(self._move_to_destination_warehouse_area), 'Second move not possible')

	def _reached_destination_warehouse_area(self):
		self.log.info('%s reached destination warehouse area', self)
		self._unload_all_resources(self.destination_settlement_manager.settlement)
		self.report_success('Unloaded resources')

decorators.bind_all(DomesticTrade)
