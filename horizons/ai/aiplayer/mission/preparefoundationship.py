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
from horizons.constants import RES
from horizons.component.storagecomponent import StorageComponent

class PrepareFoundationShip(ShipMission):
	"""
	Given a ship and a settlement manager it moves the ship to the warehouse and loads
	it with the resources required to start another settlement.
	"""

	missionStates = Enum('created', 'moving')

	def __init__(self, settlement_manager, ship, feeder_island, success_callback, failure_callback):
		super(PrepareFoundationShip, self).__init__(success_callback, failure_callback, ship)
		self.settlement_manager = settlement_manager
		self.feeder_island = feeder_island
		self.warehouse = self.settlement_manager.settlement.warehouse
		self.state = self.missionStates.created

	def save(self, db):
		super(PrepareFoundationShip, self).save(db)
		db("INSERT INTO ai_mission_prepare_foundation_ship(rowid, settlement_manager, ship, feeder_island, state) VALUES(?, ?, ?, ?, ?)", \
			self.worldid, self.settlement_manager.worldid, self.ship.worldid, self.feeder_island, self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT settlement_manager, ship, feeder_island, state FROM ai_mission_prepare_foundation_ship WHERE rowid = ?", worldid)[0]
		self.settlement_manager = WorldObject.get_object_by_id(db_result[0])
		self.warehouse = self.settlement_manager.settlement.warehouse
		self.feeder_island = db_result[2]
		self.state = self.missionStates[db_result[3]]
		super(PrepareFoundationShip, self).load(db, worldid, success_callback, failure_callback, \
			WorldObject.get_object_by_id(db_result[1]))

		if self.state == self.missionStates.moving:
			self.ship.add_move_callback(Callback(self._reached_destination_area))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_area))
		else:
			assert False, 'invalid state'

	def start(self):
		self.state = self.missionStates.moving
		self._move_to_destination_area()

	def _move_to_destination_area(self):
		self._move_to_warehouse_area(self.warehouse.position, Callback(self._reached_destination_area), \
			Callback(self._move_to_destination_area), 'Move not possible')

	def _load_foundation_resources(self):
		personality = self.owner.personality_manager.get('SettlementFounder')
		if self.feeder_island:
			max_amounts = {RES.BOARDS: personality.max_new_feeder_island_boards, RES.TOOLS: personality.max_new_feeder_island_tools}
		else:
			max_amounts = {RES.BOARDS: personality.max_new_island_boards, RES.FOOD: personality.max_new_island_food, RES.TOOLS: personality.max_new_island_tools}

		for resource_id, max_amount in max_amounts.iteritems():
			self.move_resource(self.ship, self.settlement_manager.settlement, resource_id, self.ship.get_component(StorageComponent).inventory[resource_id] - max_amount)

	def _reached_destination_area(self):
		self.log.info('%s reached BO area', self)
		self._load_foundation_resources()

		success = False
		if self.feeder_island:
			success = self.settlement_manager.owner.settlement_founder.have_feeder_island_starting_resources(self.ship, None)
			if success:
				self.report_success('Transferred enough feeder island foundation resources to the ship')
		else:
			success = self.settlement_manager.owner.settlement_founder.have_starting_resources(self.ship, None)
			if success:
				self.report_success('Transferred enough foundation resources to the ship')
		if not success:
			self.report_failure('Not enough foundation resources available')

	def cancel(self):
		self.ship.stop()
		super(PrepareFoundationShip, self).cancel()

decorators.bind_all(PrepareFoundationShip)
