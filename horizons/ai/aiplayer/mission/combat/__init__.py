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
	def __init__(self, success_callback, failure_callback, ships):
		super(FleetMission, self).__init__(success_callback, failure_callback, ships[0].owner)
		self.__init(ships)

	def __init(self, ships):
		self.unit_manager = self.owner.unit_manager
		self.fleet = self.unit_manager.create_fleet(ships)
		self.strategy_manager = self.owner.strategy_manager
		for ship in self.fleet.get_ships():
			self.owner.ships[ship] = self.owner.shipStates.on_a_mission
			ship.add_remove_listener(self.lost_ship)

	def load(self, db, worldid, success_callback, failure_callback, fleet):
		super(FleetMission, self).load(db, worldid, success_callback, failure_callback, fleet.owner)
		self.__init(fleet)

	def report_success(self):
		self.success_callback(self)

	def report_failure(self):
		self.failure_callback(self)

	def _dismiss_fleet(self):
		for ship in self.fleet.get_ships():
			self.owner.ships[ship] = self.owner.shipStates.idle
			ship.remove_remove_listener(self.lost_ship)
			ship.stop()
		self.unit_manager.destroy_fleet(self.fleet)

	def report_success(self, msg):
		self._dismiss_fleet()
		self.success_callback(self, msg)

	def report_failure(self, msg):
		self._dismiss_fleet()
		self.failure_callback(self, msg)

	def lost_ship(self):
		if self.fleet.size() == 0:
			self.cancel()

	def cancel(self):
		super(FleetMission, self).cancel()

	def __str__(self):
		return super(FleetMission, self).__str__() + (' using %s' % (self.fleet if hasattr(self, 'fleet') else 'unknown fleet'))
