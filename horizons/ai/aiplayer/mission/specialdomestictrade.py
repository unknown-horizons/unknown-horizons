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
from horizons.component.storagecomponent import StorageComponent
from horizons.component.namedcomponent import NamedComponent

class SpecialDomesticTrade(ShipMission):
	"""
	Given a ship and two settlement managers the ship will go to the source destination,
	load the most useful resources for the destination settlement, and then unload at the
	destination settlement.
	"""

	missionStates = Enum('created', 'moving_to_source_settlement', 'moving_to_destination_settlement')

	def __init__(self, source_settlement_manager, destination_settlement_manager, ship, success_callback, failure_callback):
		super(SpecialDomesticTrade, self).__init__(success_callback, failure_callback, ship)
		self.source_settlement_manager = source_settlement_manager
		self.destination_settlement_manager = destination_settlement_manager
		self.state = self.missionStates.created

	def save(self, db):
		super(SpecialDomesticTrade, self).save(db)
		db("INSERT INTO ai_mission_special_domestic_trade(rowid, source_settlement_manager, destination_settlement_manager, ship, state) VALUES(?, ?, ?, ?, ?)",
			self.worldid, self.source_settlement_manager.worldid, self.destination_settlement_manager.worldid, self.ship.worldid, self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT source_settlement_manager, destination_settlement_manager, ship, state FROM ai_mission_special_domestic_trade WHERE rowid = ?", worldid)[0]
		self.source_settlement_manager = WorldObject.get_object_by_id(db_result[0])
		self.destination_settlement_manager = WorldObject.get_object_by_id(db_result[1])
		self.state = self.missionStates[db_result[3]]
		super(SpecialDomesticTrade, self).load(db, worldid, success_callback, failure_callback, WorldObject.get_object_by_id(db_result[2]))

		if self.state is self.missionStates.moving_to_source_settlement:
			self.ship.add_move_callback(Callback(self._reached_source_settlement))
			self.ship.add_blocked_callback(Callback(self._move_to_source_settlement))
		elif self.state is self.missionStates.moving_to_destination_settlement:
			self.ship.add_move_callback(Callback(self._reached_destination_settlement))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_settlement))
		else:
			assert False, 'invalid state'

	def start(self):
		self.state = self.missionStates.moving_to_source_settlement
		self._move_to_source_settlement()
		self.log.info('%s started a special domestic trade mission from %s to %s using %s', self,
			self.source_settlement_manager.settlement.get_component(NamedComponent).name, self.destination_settlement_manager.settlement.get_component(NamedComponent).name, self.ship)

	def _move_to_source_settlement(self):
		self._move_to_warehouse_area(self.source_settlement_manager.settlement.warehouse.position, Callback(self._reached_source_settlement),
			Callback(self._move_to_source_settlement), 'Unable to move to the source settlement (%s)' % self.source_settlement_manager.settlement.get_component(NamedComponent).name)

	def _load_resources(self):
		source_resource_manager = self.source_settlement_manager.resource_manager
		source_inventory = self.source_settlement_manager.settlement.get_component(StorageComponent).inventory
		destination_resource_manager = self.destination_settlement_manager.resource_manager
		destination_inventory = self.destination_settlement_manager.settlement.get_component(StorageComponent).inventory

		options = []
		for resource_id, limit in destination_resource_manager.resource_requirements.iteritems():
			if destination_inventory[resource_id] >= limit:
				continue # the destination settlement doesn't need the resource
			if source_inventory[resource_id] <= source_resource_manager.resource_requirements[resource_id]:
				continue # the source settlement doesn't have a surplus of the resource

			price = self.owner.session.db.get_res_value(resource_id)
			tradable_amount = min(self.ship.get_component(StorageComponent).inventory.get_limit(resource_id), limit - destination_inventory[resource_id],
				source_inventory[resource_id] - source_resource_manager.resource_requirements[resource_id])
			options.append((tradable_amount * price, tradable_amount, resource_id))

		if not options:
			return False # no resources to transport

		options.sort(reverse = True)
		for _, amount, resource_id in options:
			self.move_resource(self.source_settlement_manager.settlement, self.ship, resource_id, amount)
		return True

	def _reached_source_settlement(self):
		self.log.info('%s reached the first warehouse area (%s)', self, self.source_settlement_manager.settlement.get_component(NamedComponent).name)
		if self._load_resources():
			self.state = self.missionStates.moving_to_destination_settlement
			self._move_to_destination_settlement()
		else:
			self.report_failure('No resources to transport')

	def _move_to_destination_settlement(self):
		self._move_to_warehouse_area(self.destination_settlement_manager.settlement.warehouse.position, Callback(self._reached_destination_settlement),
			Callback(self._move_to_destination_settlement), 'Unable to move to the destination settlement (%s)' % self.destination_settlement_manager.settlement.get_component(NamedComponent).name)

	def _reached_destination_settlement(self):
		self._unload_all_resources(self.destination_settlement_manager.settlement)
		self.log.info('%s reached the destination warehouse area (%s)', self, self.destination_settlement_manager.settlement.get_component(NamedComponent).name)
		self.report_success('Unloaded resources')

decorators.bind_all(SpecialDomesticTrade)
