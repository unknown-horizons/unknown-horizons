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

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.mission import ShipMission
from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.shapes import Circle, Point
from horizons.util.worldobject import WorldObject


class FoundSettlement(ShipMission):
	"""
	Given a ship with the required resources and the coordinates of the future warehouse
	the ship is taken near the end location and a warehouse is built.
	"""

	missionStates = Enum('created', 'moving')

	def __init__(self, success_callback, failure_callback, land_manager, ship, coords):
		super().__init__(success_callback, failure_callback, ship)
		self.land_manager = land_manager
		self.coords = coords
		self.warehouse = None
		self.state = self.missionStates.created

	def save(self, db):
		super().save(db)
		db("INSERT INTO ai_mission_found_settlement(rowid, land_manager, ship, x, y, state) VALUES(?, ?, ?, ?, ?, ?)",
			self.worldid, self.land_manager.worldid, self.ship.worldid, self.coords[0], self.coords[1], self.state.index)

	@classmethod
	def load(cls, db, worldid, success_callback, failure_callback):
		self = cls.__new__(cls)
		self._load(db, worldid, success_callback, failure_callback)
		return self

	def _load(self, db, worldid, success_callback, failure_callback):
		db_result = db("SELECT land_manager, ship, x, y, state FROM ai_mission_found_settlement WHERE rowid = ?", worldid)[0]
		self.land_manager = WorldObject.get_object_by_id(db_result[0])
		self.coords = (int(db_result[2]), int(db_result[3]))
		self.warehouse = None
		self.state = self.missionStates[db_result[4]]
		super().load(db, worldid, success_callback, failure_callback, WorldObject.get_object_by_id(db_result[1]))

		if self.state == self.missionStates.moving:
			self.ship.add_move_callback(Callback(self._reached_destination_area))
			self.ship.add_blocked_callback(Callback(self._move_to_destination_area))
		else:
			assert False, 'invalid state'

	def start(self):
		self.state = self.missionStates.moving
		self._move_to_destination_area()

	def _move_to_destination_area(self):
		if self.coords is None:
			self.report_failure('No possible warehouse location')
			return

		self._move_to_warehouse_area(
			Point(*self.coords), Callback(self._reached_destination_area),
			Callback(self._move_to_destination_area), 'Move not possible')

	def _reached_destination_area(self):
		self.log.info('%s reached BO area', self)

		builder = BasicBuilder(BUILDINGS.WAREHOUSE, self.coords, 0)
		if not builder.have_resources(self.land_manager, ship=self.ship):
			self.report_failure('Not enough resources for a warehouse at {}'.format(str(self.coords)))
			return

		self.warehouse = builder.execute(self.land_manager, ship=self.ship)
		assert self.warehouse

		self.land_manager.settlement = self.warehouse.settlement
		self.log.info('%s built the warehouse', self)

		self._unload_all_resources(self.land_manager.settlement)
		self.report_success('Built the warehouse, transferred resources')

	@classmethod
	def find_warehouse_location(cls, ship, land_manager):
		"""Return the coordinates of a location for the warehouse on the given island."""
		warehouse_class = Entities.buildings[BUILDINGS.WAREHOUSE]
		pos_offsets = []
		for dx in range(warehouse_class.width):
			for dy in range(warehouse_class.height):
				pos_offsets.append((dx, dy))

		island = land_manager.island
		personality = land_manager.owner.personality_manager.get('FoundSettlement')

		available_spots_list = list(sorted(island.terrain_cache.cache[warehouse_class.terrain_type][warehouse_class.size].intersection(island.available_land_cache.cache[warehouse_class.size])))
		available_spots_list = [x for x in available_spots_list
								if warehouse_class.check_build(land_manager.session, Point(*x), check_settlement=False)]
		if not available_spots_list:
			return None

		options = []
		limited_spots = island.session.random.sample(available_spots_list, min(len(available_spots_list), personality.max_options))
		for (x, y) in limited_spots:
			cost = 0
			for (x2, y2) in land_manager.village:
				dx = x2 - x
				dy = y2 - y
				distance = (dx * dx + dy * dy) ** 0.5
				if distance < personality.too_close_penalty_threshold:
					cost += personality.too_close_constant_penalty + personality.too_close_linear_penalty / (distance + 1.0)
				else:
					cost += distance

			for settlement_manager in land_manager.owner.settlement_managers:
				cost += settlement_manager.settlement.warehouse.position.distance((x, y)) * personality.linear_warehouse_penalty
			options.append((cost, x, y))

		for _, x, y in sorted(options):
			if ship.check_move(Circle(Point(x + warehouse_class.width // 2, y + warehouse_class.height // 2), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)):
				return (x, y)
		return None

	@classmethod
	def create(cls, ship, land_manager, success_callback, failure_callback):
		coords = cls.find_warehouse_location(ship, land_manager)
		return FoundSettlement(success_callback, failure_callback, land_manager, ship, coords)
