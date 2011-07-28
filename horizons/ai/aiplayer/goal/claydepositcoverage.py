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

from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class ClayDepositCoverageGoal(SettlementGoal):
	@property
	def priority(self):
		return 450

	@property
	def active(self):
		return self.owner.settler_level > 0 and not self.settlement_manager.have_deposit(BUILDINGS.CLAY_DEPOSIT_CLASS) and \
			self.settlement_manager.reachable_deposit(BUILDINGS.CLAY_DEPOSIT_CLASS)

	def execute(self):
		result = self.settlement_manager.production_builder.improve_deposit_coverage(BUILDINGS.CLAY_DEPOSIT_CLASS)
		self.settlement_manager.log_generic_build_result(result,  'clay deposit coverage storage')
		return self._translate_build_result(result)

decorators.bind_all(ClayDepositCoverageGoal)
