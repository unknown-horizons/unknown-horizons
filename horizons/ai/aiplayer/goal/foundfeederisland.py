# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.ai.aiplayer.constants import GOAL_RESULT
from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal


class FoundFeederIslandGoal(SettlementGoal):
	def get_personality_name(self):
		return 'FoundFeederIslandGoal'

	def _need_feeder_island(self):
		return self.production_builder.count_available_squares(3, self.personality.feeder_island_requirement_cutoff)[1] < self.personality.feeder_island_requirement_cutoff

	def _have_feeder_island(self):
		for settlement_manager in self.owner.settlement_managers:
			if settlement_manager.feeder_island:
				available_squares = settlement_manager.production_builder.count_available_squares(3, self.personality.usable_feeder_island_cutoff)[1]
				if available_squares >= self.personality.usable_feeder_island_cutoff:
					return True
		return False

	@property
	def active(self):
		return super().active and self._need_feeder_island() and not self._have_feeder_island() and \
			self.owner.settlement_founder.can_found_feeder_island()

	def execute(self):
		self.settlement_manager.log.info('%s waiting for a feeder islands to be founded', self)
		self.owner.settlement_founder.found_feeder_island()
		return GOAL_RESULT.BLOCK_SETTLEMENT_RESOURCE_USAGE
