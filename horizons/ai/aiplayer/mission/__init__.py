# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS
from horizons.util.shapes import Circle
from horizons.util.worldobject import WorldObject
from horizons.world.units.unitexeptions import MoveNotPossible


class Mission(WorldObject):
	"""
	This class describes a general mission that an AI seeks to fulfil.
	"""

	log = logging.getLogger("ai.aiplayer.mission")

	def __init__(self, success_callback, failure_callback, owner):
		super().__init__()
		self.__init(success_callback, failure_callback, owner)

	def __init(self, success_callback, failure_callback, owner):
		self.success_callback = success_callback
		self.failure_callback = failure_callback
		self.owner = owner

	def report_success(self, msg):
		self.log.info('%s mission success: %s', self, msg)
		self.success_callback(self, msg)

	def report_failure(self, msg):
		self.log.debug('%s mission failure: %s', self, msg)
		self.failure_callback(self, msg)

	def save(self, db):
		pass

	def load(self, db, worldid, success_callback, failure_callback, owner):
		super().load(db, worldid)
		self.__init(success_callback, failure_callback, owner)

	def cancel(self):
		self.report_failure('Mission cancelled')

	def __str__(self):
		return '{} {}({:d})'.format(
			self.owner if hasattr(self, 'owner') else 'unknown player',
			self.__class__.__name__, self.worldid)

	def end(self):
		pass


class ShipMission(Mission):
	def __init__(self, success_callback, failure_callback, ship):
		super().__init__(success_callback, failure_callback, ship.owner)
		self.__init(ship)

	def __init(self, ship):
		self.ship = ship
		self.ship.add_remove_listener(self.cancel)

	def load(self, db, worldid, success_callback, failure_callback, ship):
		super().load(db, worldid, success_callback, failure_callback, ship.owner)
		self.__init(ship)

	def report_success(self, msg):
		self.ship.remove_remove_listener(self.cancel)
		super().report_success(msg)

	def report_failure(self, msg):
		self.ship.remove_remove_listener(self.cancel)
		super().report_failure(msg)

	def cancel(self):
		self.ship.stop()
		super().cancel()

	@classmethod
	def move_resource(cls, ship, settlement, resource_id, amount):
		"""Move up to amount tons of resource_id from the ship to the settlement."""
		if amount > 0:
			missing = ship.get_component(StorageComponent).inventory.alter(resource_id, -amount)
			overflow = settlement.get_component(StorageComponent).inventory.alter(resource_id, amount - missing)
			ship.get_component(StorageComponent).inventory.alter(resource_id, overflow)
		elif amount < 0:
			missing = settlement.get_component(StorageComponent).inventory.alter(resource_id, amount)
			overflow = ship.get_component(StorageComponent).inventory.alter(resource_id, missing - amount)
			settlement.get_component(StorageComponent).inventory.alter(resource_id, overflow)

	def _unload_all_resources(self, settlement):
		# copy the inventory because otherwise we would be modifying it while iterating
		for res, amount in [item for item in self.ship.get_component(StorageComponent).inventory.itercontents()]:
			self.move_resource(self.ship, settlement, res, amount)

	def _move_to_warehouse_area(self, position, success_callback, blocked_callback, failure_msg):
		area = Circle(position.center, BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, success_callback, blocked_callback=blocked_callback)
		except MoveNotPossible:
			self.report_failure(failure_msg)

	def __str__(self):
		return super().__str__() + (' using {}'.format(
			self.ship if hasattr(self, 'ship') else 'unknown ship'))
