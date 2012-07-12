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
from horizons.ai.aiplayer.mission import Mission

class FleetMission(Mission):
	def __init__(self, success_callback, failure_callback, fleet):
		super(FleetMission, self).__init__(success_callback, failure_callback, fleet.owner)
		self.__init(fleet)

	def __init(self, fleet):
		self.fleet = fleet
		self.unit_manager = self.owner.unit_manager
		for ship in fleet.ships:
			ship.add_remove_listener(self.lost_ship)

	def load(self, db, worldid, success_callback, failure_callback, ship):
		super(FleetMission, self).load(db, worldid, success_callback, failure_callback, ship.owner)
		self.__init(ship)

	def _dismiss_fleet(self):
		for ship in self.fleet.ships:
			self.owner.ships[ship] = self.owner.shipStates.idle
			ship.remove_remove_listener(self.lost_ship)
		self.unit_manager.destroy_fleet(self.fleet)

	def report_success(self, msg):
		self._dismiss_fleet()
		super(FleetMission, self).report_success(msg)

	def report_failure(self, msg):
		self._dismiss_fleet()
		super(FleetMission, self).report_failure(msg)

	def lost_ship(self):
		if self.fleet.size() == 0:
			self.cancel()

	def cancel(self):
		super(FleetMission, self).cancel()

	def __str__(self):
		return super(FleetMission, self).__str__() + (' using %s' % (self.ship if hasattr(self, 'ship') else 'unknown ship'))
