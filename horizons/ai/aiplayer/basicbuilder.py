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

import copy
from typing import Dict, Tuple

from horizons.command.building import Build
from horizons.constants import BUILDINGS
from horizons.entities import Entities
from horizons.util.shapes import Point, Rect
from horizons.world.building.production import Mine


class BasicBuilder:
	"""An object of this class represents a non-checked plan to build a building at a specific place."""

	rotations = [45, 135, 225, 315]
	# don't change the orientation of the following building types
	non_rotatable_buildings = [BUILDINGS.WAREHOUSE, BUILDINGS.FISHER, BUILDINGS.BOAT_BUILDER,
		BUILDINGS.MINE, BUILDINGS.SALT_PONDS]

	__slots__ = ('building_id', 'coords', 'orientation', 'position')

	def __init__(self, building_id, coords, orientation):
		self.building_id = building_id
		self.coords = coords
		self.orientation = orientation

		size = Entities.buildings[building_id].size
		if orientation % 2 != 0:
			size = (size[1], size[0])
		self.position = Rect.init_from_topleft_and_size_tuples(coords, size)

	def _get_rotation(self, session, build_position_rotation):
		"""Return the rotation of the new building (randomize it if allowed)."""
		if self.building_id in self.non_rotatable_buildings:
			return build_position_rotation
		if Entities.buildings[self.building_id].size[0] == Entities.buildings[self.building_id].size[1]:
			# any orientation could be chosen
			return self.rotations[session.random.randint(0, 3)]
		else:
			# there are two possible orientations
			assert 0 <= self.orientation <= 1
			return self.rotations[self.orientation + 2 * session.random.randint(0, 1)]

	def get_loading_area(self):
		"""Return the position of the loading area."""
		if self.building_id == BUILDINGS.MINE:
			return Mine.get_loading_area(self.building_id, self.rotations[self.orientation], self.position)
		else:
			return self.position

	def execute(self, land_manager, ship=None):
		"""Build the building."""
		building_class = Entities.buildings[self.building_id]
		building_level = building_class.get_initial_level(land_manager.owner)
		action_set_id = building_class.get_random_action_set(level=building_level)

		build_position = Entities.buildings[self.building_id].check_build(land_manager.session,
		    Point(*self.coords), rotation=self.rotations[self.orientation],
		    check_settlement=(ship is None), ship=ship, issuer=land_manager.owner)
		assert build_position.buildable

		cmd = Build(self.building_id, self.coords[0], self.coords[1], land_manager.island,
			self._get_rotation(land_manager.session, build_position.rotation),
			settlement=land_manager.settlement, ship=ship, tearset=build_position.tearset,
			action_set_id=action_set_id)
		result = cmd(land_manager.owner)
		assert result
		return result

	def have_resources(self, land_manager, ship=None, extra_resources=None):
		"""Return a boolean showing whether we have the resources to build the building right now."""
		# the copy has to be made because Build.check_resources modifies it
		extra_resources = copy.copy(extra_resources) if extra_resources is not None else {}
		inventories = [land_manager.settlement, ship]
		return Build.check_resources(extra_resources, Entities.buildings[self.building_id].costs, land_manager.owner, inventories)[0]

	def __str__(self):
		return 'BasicBuilder of building {0:d} at {1!s}, orientation {2:d}'. \
			format(self.building_id, self.coords, self.orientation)

	__cache = {} # type: Dict[Tuple[int, Tuple[int, int], int], BasicBuilder]

	@classmethod
	def clear_cache(cls):
		cls.__cache.clear()

	@classmethod
	def create(cls, building_id, coords, orientation):
		"""
		Create or get a cached version of the BasicBuilder.

		This is supposed to speed up the process in case identical BasicBuilder instances
		would be created. The constructor should be used directly otherwise.
		"""

		key = (building_id, coords, orientation)
		if key not in cls.__cache:
			cls.__cache[key] = BasicBuilder(building_id, coords, orientation)
		return cls.__cache[key]
