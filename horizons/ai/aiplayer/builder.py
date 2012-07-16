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

import copy
import logging

from horizons.entities import Entities
from horizons.constants import BUILDINGS
from horizons.command.building import Build
from horizons.util.python import decorators
from horizons.util import Point, WorldObject
from horizons.world.building.production import Mine

class Builder(WorldObject):
	"""An object of this class represents a plan to build a building at a specific place."""

	log = logging.getLogger("ai.aiplayer.builder")

	rotations = [45, 135, 225, 315]
	# don't change the orientation of the following building types
	non_rotatable_buildings = [BUILDINGS.WAREHOUSE, BUILDINGS.FISHER, BUILDINGS.BOAT_BUILDER,
		BUILDINGS.IRON_MINE, BUILDINGS.SALT_PONDS]

	def __init__(self, building_id, land_manager, point, orientation=0, ship=None, worldid=None):
		"""
		@param building_id: the id of the building class
		@param land_manager: LandManager instance
		@param point: the origin coordinates
		@param orientation: 0..3 for the rotations [45, 135, 225, 315]
		@param ship: ship instance if building from ship
		@param worldid: the worldid of a loaded object
		"""

		super(Builder, self).__init__(worldid)
		self.building_id = building_id
		self.land_manager = land_manager
		self.session = land_manager.session
		self.point = point
		self.orientation = orientation
		self.ship = ship

		check_settlement = ship is None
		self.build_position = Entities.buildings[building_id].check_build(self.session, point,
			rotation = self.rotations[orientation], check_settlement = check_settlement, ship = ship,
			issuer = self.land_manager.owner)
		self.position = self.build_position.position

	def save(self, db):
		super(Builder, self).save(db)
		db("INSERT INTO ai_builder(rowid, building_type, x, y, orientation, ship) VALUES(?, ?, ?, ?, ?, ?)",
			self.worldid, self.building_id, self.point.x, self.point.y, self.orientation,
			None if self.ship is None else self.ship.worldid)

	@classmethod
	def load(cls, db, worldid, land_manager):
		db_result = db("SELECT building_type, x, y, orientation, ship FROM ai_builder WHERE rowid = ?", worldid)[0]
		ship = WorldObject.get_object_by_id(db_result[4]) if db_result[4] else None
		return cls.create(db_result[0], land_manager, Point(db_result[1], db_result[2]), db_result[3], ship, worldid=worldid)

	def __nonzero__(self):
		"""Return a boolean showing whether it is possible to build the building at this place."""
		return self.build_position.buildable

	def __str__(self):
		return 'Builder(%d) of building %d at %s, orientation %d' % (self.worldid, self.building_id, self.point.to_tuple(), self.orientation)

	def _get_rotation(self):
		"""Return the rotation of the new building (randomise it if allowed)."""
		if self.building_id in self.non_rotatable_buildings:
			return self.build_position.rotation
		if Entities.buildings[self.building_id].size[0] == Entities.buildings[self.building_id].size[1]:
			# any orientation could be chosen
			return self.rotations[self.session.random.randint(0, 3)]
		else:
			# there are two possible orientations
			assert 0 <= self.orientation <= 1
			return self.rotations[self.orientation + 2 * self.session.random.randint(0, 1)]

	def get_loading_area(self):
		"""Return the position of the loading area."""
		if self.building_id == BUILDINGS.IRON_MINE:
			return Mine.get_loading_area(self.building_id, self.rotations[self.orientation], self.position)
		else:
			return self.position

	def execute(self):
		"""Build the building."""
		cmd = Build(self.building_id, self.point.x, self.point.y, self.land_manager.island,
			self._get_rotation(), settlement = self.land_manager.settlement,
			ship = self.ship, tearset = self.build_position.tearset)
		result = cmd(self.land_manager.owner)
		#self.log.debug('%s.execute(): %s', self.__class__.__name__, result)
		return result

	def have_resources(self, extra_resources=None):
		"""Return a boolean showing whether we have the resources to build the building right now."""
		# the copy has to be made because Build.check_resources modifies it
		extra_resources = copy.copy(extra_resources) if extra_resources is not None else {}
		inventories = [self.land_manager.settlement, self.ship]
		(enough_res, _) = Build.check_resources(extra_resources,
			Entities.buildings[self.building_id].costs, self.land_manager.owner, inventories)
		return enough_res

	cache = {}

	@classmethod
	def create(cls, building_id, land_manager, point, orientation=0, ship=None, worldid=None):
		"""
		Return a Builder object. Use the __nonzero__ function to know whether it is usable.

		@param building_id: the id of the building class
		@param land_manager: LandManager instance
		@param point: the origin coordinates
		@param orientation: 0..3 for the rotations [45, 135, 225, 315]
		@param ship: ship instance if building from ship
		@param worldid: the worldid of a loaded object
		"""

		coords = point.to_tuple()
		key = (building_id, coords, orientation, land_manager.owner.worldid)
		size = Entities.buildings[building_id].size
		if orientation == 1 or orientation == 3:
			size = (size[1], size[0])

		last_changed = land_manager.island.last_changed[size][coords]
		if key in cls.cache and last_changed != cls.cache[key][0]:
			del cls.cache[key]
		if key not in cls.cache:
			cls.cache[key] = (last_changed, Builder(building_id, land_manager, point, orientation, ship, worldid=worldid))
		return cls.cache[key][1]

decorators.bind_all(Builder)
