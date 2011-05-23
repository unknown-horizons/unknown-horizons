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
from horizons.constants import GROUND
from horizons.util import Callback
from horizons.util import Point, Circle

class FoundSettlement(Mission):
	"""
	Given a ship with the required resources and a bo_location the ship is taken near
	the location and a branch office is built.
	"""

	def __init__(self, ship, bo_location, success_callback, failure_callback, **kwargs):
		super(FoundSettlement, self).__init__(success_callback, failure_callback, **kwargs)
		self.ship = ship
		self.bo_location = bo_location

	def start(self):
		try:
			self._move_to_bo_area()
		except MoveNotPossible:
			self.report_failure('Move not possible')

	def _move_to_bo_area(self):
		area = Circle(self.bo_location, 5)
		self.ship.move(area, Callback(self._reached_bo_area))

	def _reached_bo_area(self):
		self.report_success('Reached BO area')

	@classmethod
	def create(cls, ship, island, success_callback, failure_callback):
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]

		# select a location for the branch office
		bo_location = None
		for (x, y), tile in island.ground_map.iteritems():
			if tile.id == GROUND.DEFAULT_LAND:
				for x_offset, y_offset in moves:
					x4 = x + 4 * x_offset
					y4 = y + 4 * y_offset
					if (x4, y4) not in island.ground_map:
						bo_location = Point(x, y)
						break
				if bo_location is not None:
					break

		return FoundSettlement(ship, bo_location, success_callback, failure_callback)
