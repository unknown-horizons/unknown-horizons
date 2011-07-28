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

from horizons.ai.aiplayer.goal.productionchaingoal import ProductionChainGoal
from horizons.ai.aiplayer.constants import BUILD_RESULT

from horizons.constants import BUILDINGS, RES
from horizons.util.python import decorators

class FeederChainGoal(ProductionChainGoal):
	"""
	Objects of this class are used for production chains on feeder islands
	The update call reserved the production for the (non-existent) settlement so it can't be transferred.
	The late_update call declares that the settlement doesn't need it after all thus freeing it.
	TODO: make that a single explicit action: right now import quotas are deleted by the first step which can make it look like less resources can be imported.
	"""

	def __init__(self, settlement_manager, chain, name):
		super(FeederChainGoal, self).__init__(settlement_manager, chain, name)
		self.__init()

	def __init(self):
		self._may_import = False

	def _update_needed_amount(self):
		self._needed_amount = self.settlement_manager.get_total_missing_production(self.chain.resource_id)

	def late_update(self):
		self.chain.reserve(0, False) # remove the reserved production quota so it can be exported

class FeederTextileGoal(FeederChainGoal):
	@property
	def can_be_activated(self):
		return self.owner.settler_level > 0

class FeederLiquorGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.owner.settler_level > 1 and self.settlement_manager.get_resource_production(RES.BRICKS_ID) > 0

decorators.bind_all(FeederChainGoal)
decorators.bind_all(FeederTextileGoal)
decorators.bind_all(FeederLiquorGoal)
