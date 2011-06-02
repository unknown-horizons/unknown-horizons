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

from horizons.entities import Entities
from horizons.constants import BUILDINGS
from horizons.command.building import Build
from horizons.util.python import decorators
from horizons.util import Point, WorldObject

class Builder(WorldObject):
	"""
	This is a convenience class to make it easier for the AI to build buildings.
	"""

	rotations = [45, 135, 225, 315]

	def __init__(self, building_id, land_manager, point, orientation=0, ship=None, worldid=None):
		"""
		Check if a building is buildable here.
		All tiles, that the building occupies are checked.
		@param building_id: int, the id of the building class
		@param land_manager: LandManager
		@param point: Point instance, bottom left corner coordinates
		@param orientation: 0..3 for the rotations [45, 135, 225, 315]
		@param ship: ship instance if building from ship
		@return instance of BuilderCommand
		"""
		super(Builder, self).__init__(worldid)
		self.building_id = building_id
		self.land_manager = land_manager
		self.point = point
		self.orientation = orientation
		self.ship = ship

		check_settlement = ship is None
		self.build_position = Entities.buildings[building_id].check_build(self.land_manager.session, \
			point, rotation = self.rotations[orientation], check_settlement = check_settlement, ship = None, \
			issuer = self.land_manager.owner)
		self.position = self.build_position.position

	def save(self, db):
		super(Builder, self).save(db)
		db("INSERT INTO ai_builder(rowid, building_type, x, y, orientation, ship) VALUES(?, ?, ?, ?, ?, ?)", \
			self.worldid, self.building_id, self.point.x, self.point.y, self.orientation, \
			None if self.ship is None else self.ship.worldid)

	@classmethod
	def load(cls, db, worldid, land_manager):
		db_result = db("SELECT building_type, x, y, orientation, ship FROM ai_builder WHERE rowid = ?", worldid)[0]
		ship = WorldObject.get_object_by_id(db_result[4]) if db_result[4] else None
		return cls.create(db_result[0], land_manager, Point(db_result[1], db_result[2]), db_result[3], ship, worldid=worldid)

	def __nonzero__(self):
		"""Returns buildable value. This enables code such as "if cls.check_build()"""
		return self.build_position.buildable

	def execute(self):
		"""Actually builds the building."""
		cmd = Build(self.building_id, self.point.x, self.point.y, self.land_manager.island, \
			self.build_position.rotation, settlement = self.land_manager.settlement, \
			ship = self.ship, tearset = self.build_position.tearset)
		return cmd(self.land_manager.owner)

	def have_resources(self):
		neededResources = {}
		inventories = [self.land_manager.settlement, self.ship]
		(enough_res, missing_res) = Build.check_resources(neededResources, \
			Entities.buildings[self.building_id].costs, self.land_manager.owner, inventories)
		return enough_res

	cache = {}
	cache_tick_id = -1

	@classmethod
	def create(cls, building_id, land_manager, point, orientation=0, ship=None, worldid=None):
		if land_manager.session.timer.tick_next_id != cls.cache_tick_id:
			cls.cache_tick_id = land_manager.session.timer.tick_next_id
			cls.cache = {}
		key = (building_id, point.to_tuple(), orientation)
		if key not in cls.cache:
			cls.cache[key] = Builder(building_id, land_manager, point, orientation, ship, worldid=worldid)
		return cls.cache[key]

decorators.bind_all(Builder)
