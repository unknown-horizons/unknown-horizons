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

from horizons.ai.aiplayer.mission import ShipMission
from horizons.ai.aiplayer.builder import Builder
from horizons.constants import BUILDINGS
from horizons.util import Point, Circle, Callback, WorldObject
from horizons.util.python import decorators
from horizons.ext.enum import Enum

class FoundSettlement(ShipMission):
	"""
	Given a ship with the required resources and a bo_location the ship is taken near
	the location and a branch office is built.
	"""

	missionStates = Enum('created', 'moving')

	def __init__(self, success_callback, failure_callback, land_manager, ship, bo_location):
		super(FoundSettlement, self).__init__(success_callback, failure_callback, ship)
		self.land_manager = land_manager
		self.bo_location = bo_location
		self.branch_office = None
		self.state = self.missionStates.created

	def save(self, db):
		super(FoundSettlement, self).save(db)
		db("INSERT INTO ai_mission_found_settlement(rowid, land_manager, ship, bo_builder, state) VALUES(?, ?, ?, ?, ?)", \
			self.worldid, self.land_manager.worldid, self.ship.worldid, self.bo_location.worldid, self.state.index)
		assert isinstance(self.bo_location, Builder)
		self.bo_location.save(db)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT land_manager, ship, bo_builder, state FROM ai_mission_found_settlement WHERE rowid = ?", worldid)[0]
		self.land_manager = WorldObject.get_object_by_id(db_result[0])
		self.bo_location = Builder.load(db, db_result[2], self.land_manager)
		self.branch_office = None
		self.state = self.missionStates[db_result[3]]
		super(FoundSettlement, self).load(db, worldid, success_callback, failure_callback, WorldObject.get_object_by_id(db_result[1]))

		if self.state == self.missionStates.moving:
			self.ship.add_move_callback(Callback(self._reached_bo_area))
			self.ship.add_blocked_callback(Callback(self._move_to_bo_area))
		else:
			assert False, 'invalid state'

	def start(self):
		self.state = self.missionStates.moving
		self._move_to_bo_area()

	def _move_to_bo_area(self):
		if self.bo_location is None:
			self.report_failure('No possible branch office location')
			return

		self._move_to_branch_office_area(self.bo_location.position, Callback(self._reached_bo_area), \
			Callback(self._move_to_bo_area), 'Move not possible')

	def _reached_bo_area(self):
		self.log.info('%s reached BO area', self)

		self.branch_office = self.bo_location.execute()
		if not self.branch_office:
			self.report_failure('Unable to build the branch office')
			return

		island = self.bo_location.land_manager.island
		self.land_manager.settlement = island.get_settlement(self.bo_location.point)
		self.log.info('%s built the branch office', self)

		self._unload_all_resources(self.land_manager.settlement)
		self.report_success('Built the branch office, transferred resources')

	@classmethod
	def find_bo_location(cls, ship, land_manager):
		"""
		Finds a location for the branch office on the given island
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
						# the planned branch office should be reachable from the ship's water body
						ok = True
			if not ok:
				continue

			build_info = None
			point = Point(x, y)
			branch_office = Builder(BUILDINGS.BRANCH_OFFICE_CLASS, land_manager, point, ship = ship)
			if not branch_office:
				continue

			cost = 0
			for coords in land_manager.village:
				distance = point.distance_to_tuple(coords)
				if distance < personality.too_close_penalty_threshold:
					cost += personality.too_close_constant_penalty + personality.too_close_linear_penalty / (distance + 1.0)
				else:
					cost += distance

			for settlement_manager in land_manager.owner.settlement_managers:
				cost += branch_office.position.distance(settlement_manager.settlement.branch_office.position) * personality.linear_branch_office_penalty

			options.append((cost, branch_office))

		for _, build_info in sorted(options):
			(x, y) = build_info.position.get_coordinates()[4]
			if ship.check_move(Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)):
				return build_info
		return None

	@classmethod
	def create(cls, ship, land_manager, success_callback, failure_callback):
		bo_location = cls.find_bo_location(ship, land_manager)
		return FoundSettlement(success_callback, failure_callback, land_manager, ship, bo_location)

decorators.bind_all(FoundSettlement)
