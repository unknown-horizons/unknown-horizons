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

class SpecialDomesticTrade(Mission):
	"""
	Given a ship and two settlement managers the ship will go to the source destination,
	load the most useful resources for the destination settlement, and then unload at the
	destination settlement.
	"""

	missionStates = Enum('created', 'moving_to_source_settlement', 'moving_to_destination_settlement')

	def __init__(self, source_settlement_manager, destination_settlement_manager, ship, success_callback, failure_callback, **kwargs):
		super(SpecialDomesticTrade, self).__init__(success_callback, failure_callback, source_settlement_manager.session, **kwargs)
		self.source_settlement_manager = source_settlement_manager
		self.destination_settlement_manager = destination_settlement_manager
		self.ship = ship
		self.state = self.missionStates.created
		self.ship.add_remove_listener(self.cancel)

	def save(self, db):
		super(SpecialDomesticTrade, self).save(db)
		db("INSERT INTO ai_mission_special_domestic_trade(rowid, source_settlement_manager, destination_settlement_manager, ship, state) VALUES(?, ?, ?, ?, ?)", \
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
		self.ship = WorldObject.get_object_by_id(db_result[2])
		self.state = self.missionStates[db_result[3]]
		super(SpecialDomesticTrade, self).load(db, worldid, success_callback, failure_callback, self.source_settlement_manager.session)

		if self.state is self.missionStates.moving_to_source_settlement:
			self.ship.add_move_callback(Callback(self._reached_source_settlement))
			self.ship.add_blocked_callback(Callback(self._move_to_source_settlement))
		elif self.state is self.missionStates.moving_to_destination_settlement:
			self.ship.add_move_callback(Callback(self._reached_destination_settlement))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_settlement))

		self.ship.add_remove_listener(self.cancel)

	def report_success(self, msg):
		self.ship.remove_remove_listener(self.cancel)
		super(SpecialDomesticTrade, self).report_success(msg)

	def report_failure(self, msg):
		self.ship.remove_remove_listener(self.cancel)
		super(SpecialDomesticTrade, self).report_failure(msg)

	def start(self):
		self.state = self.missionStates.moving_to_source_settlement
		self._move_to_source_settlement()
		self.log.info('Started a special domestic trade mission from %s to %s using %s', \
			self.source_settlement_manager.settlement.name, self.destination_settlement_manager.settlement.name, self.ship)

	def _move_to_source_settlement(self):
		(x, y) = self.source_settlement_manager.branch_office.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, Callback(self._reached_source_settlement), blocked_callback = Callback(self._move_to_source_settlement))
		except MoveNotPossible:
			self.report_failure('Unable to move to the source settlement (%s)' % self.source_settlement_manager.settlement.name)

	def _load_resources(self):
		source_resource_manager = self.source_settlement_manager.resource_manager
		source_inventory = self.source_settlement_manager.settlement.inventory
		destination_resource_manager = self.destination_settlement_manager.resource_manager
		destination_inventory = self.destination_settlement_manager.settlement.inventory

		options = []
		for resource_id, limit in destination_resource_manager.resource_requirements.iteritems():
			if destination_inventory[resource_id] >= limit:
				continue # the destination settlement doesn't need the resource
			if source_inventory[resource_id] <= source_resource_manager.resource_requirements[resource_id]:
				continue # the source settlement doesn't have a surplus of the resource

			price = self.session.db.get_res_value(resource_id)
			tradable_amount = min(self.ship.inventory.get_limit(resource_id), limit - destination_inventory[resource_id], \
				source_inventory[resource_id] - source_resource_manager.resource_requirements[resource_id])
			options.append((tradable_amount * price, tradable_amount, resource_id))

		if not options:
			return False # no resources to transport

		options.sort(reverse = True)
		for _, amount, resource_id in options:
			self.source_settlement_manager.owner.complete_inventory.move(self.source_settlement_manager.settlement, self.ship, resource_id, amount)
		return True

	def _reached_source_settlement(self):
		self.log.info('Reached the first branch office area (%s)', self.source_settlement_manager.settlement.name)
		if self._load_resources():
			self.state = self.missionStates.moving_to_destination_settlement
			self._move_to_destination_settlement()
		else:
			self.log.info('No resources to transport')
			self.report_failure('No resources to transport')

	def _move_to_destination_settlement(self):
		(x, y) = self.destination_settlement_manager.settlement.branch_office.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, Callback(self._reached_destination_settlement), blocked_callback = Callback(self._move_to_destination_settlement))
		except MoveNotPossible:
			self.report_failure('Unable to move to the destination settlement (%s)' % self.settlement.name)

	def _reached_destination_settlement(self):
		self.destination_settlement_manager.owner.complete_inventory.unload_all(self.ship, self.destination_settlement_manager.settlement)
		self.log.info('Reached the destination branch office area (%s)', self.destination_settlement_manager.settlement.name)

	def cancel(self):
		self.ship.stop()
		super(SpecialDomesticTrade, self).cancel()

decorators.bind_all(SpecialDomesticTrade)
