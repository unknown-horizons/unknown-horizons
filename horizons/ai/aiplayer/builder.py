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

class Builder(object):
	"""
	This is a convenience class to make it easier for the AI to build buildings.
	"""

	rotations = [45, 135, 225, 315]

	def __init__(self, building_id, land_manager, point, orientation=0, ship=None):
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
		self.building_id = building_id
		self.land_manager = land_manager
		self.point = point
		self.orientation = orientation
		self.ship = ship

		check_settlement = ship is None
		self.build_position = Entities.buildings[building_id].check_build(self.land_manager.session, \
			point, rotation = self.rotations[orientation], check_settlement = check_settlement, ship = None)
		self.position = self.build_position.position

	def __nonzero__(self):
		"""Returns buildable value. This enables code such as "if cls.check_build()"""
		return self.build_position.buildable

	def execute(self):
		"""Actually builds the building."""
		cmd = Build(self.building_id, self.point.x, self.point.y, self.land_manager.island, \
			[45, 135, 225, 315][self.orientation], settlement = self.land_manager.settlement, \
			ship = self.ship, tearset = self.build_position.tearset)
		return cmd.execute(self.land_manager.session)
