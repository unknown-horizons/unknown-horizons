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

from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class TradingShipGoal(SettlementGoal):
	def get_personality_name(self):
		return 'TradingShipGoal'

	@property
	def active(self):
		return super(TradingShipGoal, self).active \
			and self.owner.count_buildings(BUILDINGS.BOAT_BUILDER) \
			and self.owner.need_more_ships \
			and not self.owner.unit_builder.num_ships_being_built

	def execute(self):
		self.settlement_manager.log.info('%s start building a ship', self)
		self.owner.unit_builder.build_ship()

decorators.bind_all(TradingShipGoal)
