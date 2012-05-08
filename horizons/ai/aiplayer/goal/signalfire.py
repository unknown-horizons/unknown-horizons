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
from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class SignalFireGoal(SettlementGoal):
	def get_personality_name(self):
		return 'SignalFireGoal'

	@property
	def active(self):
		return super(SignalFireGoal, self).active and not self.settlement.count_buildings(BUILDINGS.SIGNAL_FIRE)

	def execute(self):
		result = AbstractBuilding.buildings[BUILDINGS.SIGNAL_FIRE].build(self.settlement_manager, None)[0]
		self._log_generic_build_result(result, 'signal fire')
		return self._translate_build_result(result)

decorators.bind_all(SignalFireGoal)
