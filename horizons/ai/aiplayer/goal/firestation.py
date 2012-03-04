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

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.constants import BUILDINGS, RES
from horizons.util.python import decorators

class FireStationGoal(SettlementGoal):
	def get_personality_name(self):
		return 'FireStationGoal'

	@property
	def can_be_activated(self):
		return super(FireStationGoal, self).can_be_activated and self.settlement_manager.get_resource_production(RES.BRICKS_ID) > 0

	@property
	def active(self):
		return super(FireStationGoal, self).active and self._is_active

	def update(self):
		super(FireStationGoal, self).update()
		if self.can_be_activated:
			self._is_active = any(AbstractBuilding.buildings[BUILDINGS.FIRE_STATION_CLASS].iter_potential_locations(self.settlement_manager))
		else:
			self._is_active = False

	def execute(self):
		result = AbstractBuilding.buildings[BUILDINGS.FIRE_STATION_CLASS].build(self.settlement_manager, None)[0]
		self._log_generic_build_result(result, 'fire station')
		return self._translate_build_result(result)

decorators.bind_all(FireStationGoal)
