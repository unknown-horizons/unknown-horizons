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
from horizons.constants import GROUND, BUILDINGS
from horizons.util import Point, Circle, Callback
from horizons.world.building.buildable import Buildable
from horizons.entities import Entities
from horizons.command.building import Build

class FoundSettlement(Mission):
	"""
	Given a ship with the required resources and a bo_location the ship is taken near
	the location and a branch office is built.
	"""

	def __init__(self, success_callback, failure_callback, session, ship, bo_location, **kwargs):
		super(FoundSettlement, self).__init__(success_callback, failure_callback, session, **kwargs)
		self.ship = ship
		self.bo_location = bo_location

	def start(self):
		try:
			self._move_to_bo_area()
		except MoveNotPossible:
			self.report_failure('Move not possible')

	def _move_to_bo_area(self):
		(x, y) = self.bo_location.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		self.ship.move(area, Callback(self._reached_bo_area))

	def _reached_bo_area(self):
		self.log.info('Reached BO area')
		t = self.bo_location
		x = t.position.origin.x
		y = t.position.origin.y
		island = self.session.world.get_island(Point(x, y))
		cmd = Build(BUILDINGS.BRANCH_OFFICE_CLASS, x, y, island, t.rotation, ship = self.ship, tearset = t.tearset)
		cmd.execute(self.session)
		self.report_success('Built the branch office')

	@classmethod
	def find_bo_location(cls, island, close_to):
		"""
		Finds a location for the branch office on the given island
		@param island: the island
		@param Point: the point for which it has to be optimized
		@return _BuildPosition: a possible build location
		"""
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		rotations = [45, 135, 225, 315]

		best = None
		best_dist = 1000000000

		for (x, y), tile in island.ground_map.iteritems():
			dist = close_to.distance_to_tuple((x, y))
			if best_dist <= dist:
				continue

			ok = False
			for x_offset, y_offset in moves:
				for d in xrange(2, 5):
					x2 = x + d * x_offset
					y2 = y + d * y_offset
					if (x2, y2) not in island.ground_map:
						ok = True
						break

			if ok:
				point = Point(x, y)
				for rotation in rotations:
					build_location = Entities.buildings[BUILDINGS.BRANCH_OFFICE_CLASS].check_build(island.session, \
						point, rotation=rotation, check_settlement=False, ship=None)
					if build_location.buildable:
						best = build_location
						best_dist = dist

		return best

	@classmethod
	def create(cls, ship, island, success_callback, failure_callback):
		bo_location = cls.find_bo_location(island, ship.position)
		return FoundSettlement(success_callback, failure_callback, island.session, ship, bo_location)
