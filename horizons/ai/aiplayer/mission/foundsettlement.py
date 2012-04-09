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
from horizons.ai.aiplayer.builder import Builder
from horizons.constants import BUILDINGS
from horizons.util import Point, Circle, Callback, WorldObject
from horizons.util.python import decorators
from horizons.ext.enum import Enum

class FoundSettlement(ShipMission):
	"""
	Given a ship with the required resources and a warehouse_location the ship is taken near
	the location and a warehouse is built.
	"""

	missionStates = Enum('created', 'moving')

	def __init__(self, success_callback, failure_callback, land_manager, ship, warehouse_location):
		super(FoundSettlement, self).__init__(success_callback, failure_callback, ship)
		self.land_manager = land_manager
		self.warehouse_location = warehouse_location
		self.warehouse = None
		self.state = self.missionStates.created

	def save(self, db):
		super(FoundSettlement, self).save(db)
		db("INSERT INTO ai_mission_found_settlement(rowid, land_manager, ship, warehouse_builder, state) VALUES(?, ?, ?, ?, ?)", \
			self.worldid, self.land_manager.worldid, self.ship.worldid, self.warehouse_location.worldid, self.state.index)
		assert isinstance(self.warehouse_location, Builder)
		self.warehouse_location.save(db)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT land_manager, ship, warehouse_builder, state FROM ai_mission_found_settlement WHERE rowid = ?", worldid)[0]
		self.land_manager = WorldObject.get_object_by_id(db_result[0])
		self.warehouse_location = Builder.load(db, db_result[2], self.land_manager)
		self.warehouse = None
		self.state = self.missionStates[db_result[3]]
		super(FoundSettlement, self).load(db, worldid, success_callback, failure_callback, WorldObject.get_object_by_id(db_result[1]))

		if self.state == self.missionStates.moving:
			self.ship.add_move_callback(Callback(self._reached_destination_area))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_area))
		else:
			assert False, 'invalid state'

	def start(self):
		self.state = self.missionStates.moving
		self._move_to_destination_area()

	def _move_to_destination_area(self):
		if self.warehouse_location is None:
			self.report_failure('No possible warehouse location')
			return

		self._move_to_warehouse_area(self.warehouse_location.position, Callback(self._reached_destination_area), \
			Callback(self._move_to_destination_area), 'Move not possible')

	def _reached_destination_area(self):
		self.log.info('%s reached BO area', self)

		self.warehouse = self.warehouse_location.execute()
		if not self.warehouse:
			self.report_failure('Unable to build the warehouse')
			return

		island = self.warehouse_location.land_manager.island
		self.land_manager.settlement = island.get_settlement(self.warehouse_location.point)
		self.log.info('%s built the warehouse', self)

		self._unload_all_resources(self.land_manager.settlement)
		self.report_success('Built the warehouse, transferred resources')

	@classmethod
	def find_warehouse_location(cls, ship, land_manager):
		"""
		Finds a location for the warehouse on the given island
		@param LandManager: the LandManager of the island
		@return _BuildPosition: a possible build location
		"""
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		island = land_manager.island
		world = island.session.world
		personality = land_manager.owner.personality_manager.get('FoundSettlement')
		options = []

		for (x, y), tile in sorted(island.ground_map.iteritems()):
			ok = False
			for x_offset, y_offset in moves:
				for d in xrange(2, 6):
					coords = (x + d * x_offset, y + d * y_offset)
					if coords in world.water_body and world.water_body[coords] == world.water_body[ship.position.to_tuple()]:
						# the planned warehouse should be reachable from the ship's water body
						ok = True
			if not ok:
				continue

			build_info = None
			point = Point(x, y)
			warehouse = Builder(BUILDINGS.WAREHOUSE, land_manager, point, ship = ship)
			if not warehouse:
				continue

			cost = 0
			for coords in land_manager.village:
				distance = point.distance_to_tuple(coords)
				if distance < personality.too_close_penalty_threshold:
					cost += personality.too_close_constant_penalty + personality.too_close_linear_penalty / (distance + 1.0)
				else:
					cost += distance

			for settlement_manager in land_manager.owner.settlement_managers:
				cost += warehouse.position.distance(settlement_manager.settlement.warehouse.position) * personality.linear_warehouse_penalty

			options.append((cost, warehouse))

		for _, build_info in sorted(options):
			(x, y) = build_info.position.get_coordinates()[4]
			if ship.check_move(Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)):
				return build_info
		return None

	@classmethod
	def create(cls, ship, land_manager, success_callback, failure_callback):
		warehouse_location = cls.find_warehouse_location(ship, land_manager)
		return FoundSettlement(success_callback, failure_callback, land_manager, ship, warehouse_location)

decorators.bind_all(FoundSettlement)
