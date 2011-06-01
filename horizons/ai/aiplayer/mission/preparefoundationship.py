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
from horizons.util import Point, Circle, Callback
from horizons.util.python import decorators
from horizons.constants import BUILDINGS

class PrepareFoundationShip(Mission):
	"""
	Given a ship and a settlement manager it moves the ship to the branch office and loads
	it with the resources required to start another settlement.
	"""

	def __init__(self, settlement_manager, ship, success_callback, failure_callback, **kwargs):
		super(PrepareFoundationShip, self).__init__(success_callback, failure_callback, \
			settlement_manager.land_manager.island.session, **kwargs)
		self.settlement_manager = settlement_manager
		self.ship = ship
		self.branch_office = self.settlement_manager.branch_office

	def start(self):
		self._move_to_bo_area()

	def _move_to_bo_area(self):
		(x, y) = self.branch_office.position.get_coordinates()[4]
		area = Circle(Point(x, y), BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE)
		try:
			self.ship.move(area, Callback(self._reached_bo_area), blocked_callback = Callback(self._move_to_bo_area))
		except MoveNotPossible:
			self.report_failure('Move not possible')

	def _reached_bo_area(self):
		self.log.info('Reached BO area')
		self.ship.owner.complete_inventory.load_foundation_resources(self.ship, \
			self.settlement_manager.land_manager.settlement)
		if self.settlement_manager.owner.have_starting_resources(self.ship, None):
			self.report_success('Transferred enough foundation resources to the ship')
		else:
			self.report_failure('Not enough foundation resources available')

decorators.bind_all(PrepareFoundationShip)
