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

from horizons.ai.aiplayer.goal.productionchaingoal import ProductionChainGoal
from horizons.constants import RES
from horizons.util.python import decorators

class FeederChainGoal(ProductionChainGoal):
	"""
	Objects of this class are used for production chains on feeder islands
	The update call reserved the production for the (non-existent) settlement so it can't be transferred.
	The late_update call declares that the settlement doesn't need it after all thus freeing it.
	TODO: make that a single explicit action: right now import quotas are deleted by the first step which can make it look like less resources can be imported.
	"""

	def __init__(self, settlement_manager, resource_id, name):
		super(FeederChainGoal, self).__init__(settlement_manager, resource_id, name)
		self._may_import = False
		self._feeder_personality = self.owner.personality_manager.get('FeederChainGoal')

	@property
	def priority(self):
		return super(FeederChainGoal, self).priority + self._feeder_personality.extra_priority

	def execute(self):
		self.chain.reserve(self._needed_amount, self._may_import)
		result = super(FeederChainGoal, self).execute()
		self.chain.reserve(0, False)
		return result

	def _update_needed_amount(self):
		self._needed_amount = self.settlement_manager.get_ideal_production_level(self.chain.resource_id)

	def update(self):
		super(FeederChainGoal, self).update()
		self.chain.reserve(0, False)

class FeederFoodGoal(FeederChainGoal):
	def __init__(self, settlement_manager):
		super(FeederFoodGoal, self).__init__(settlement_manager, RES.FOOD, 'food producer')

	def get_personality_name(self):
		return 'FoodGoal'

class FeederTextileGoal(FeederChainGoal):
	def __init__(self, settlement_manager):
		super(FeederTextileGoal, self).__init__(settlement_manager, RES.TEXTILE, 'textile producer')

	def get_personality_name(self):
		return 'TextileGoal'

class FeederLiquorGoal(FeederChainGoal):
	def __init__(self, settlement_manager):
		super(FeederLiquorGoal, self).__init__(settlement_manager, RES.LIQUOR, 'liquor producer')

	def get_personality_name(self):
		return 'LiquorGoal'

	@property
	def can_be_activated(self):
		return super(FeederLiquorGoal, self).can_be_activated and self.settlement_manager.get_resource_production(RES.BRICKS) > 0

class FeederTobaccoProductsGoal(FeederChainGoal):
	def __init__(self, settlement_manager):
		super(FeederTobaccoProductsGoal, self).__init__(settlement_manager, RES.TOBACCO_PRODUCTS, 'tobacco products producer')

	def get_personality_name(self):
		return 'FeederTobaccoProductsGoal'

	@property
	def can_be_activated(self):
		return super(FeederTobaccoProductsGoal, self).can_be_activated and self.settlement_manager.get_resource_production(RES.BRICKS) > 0

class FeederSaltGoal(FeederChainGoal):
	def __init__(self, settlement_manager):
		super(FeederSaltGoal, self).__init__(settlement_manager, RES.SALT, 'salt producer')

	def get_personality_name(self):
		return 'FeederSaltGoal'

decorators.bind_all(FeederChainGoal)
decorators.bind_all(FeederFoodGoal)
decorators.bind_all(FeederTextileGoal)
decorators.bind_all(FeederLiquorGoal)
decorators.bind_all(FeederTobaccoProductsGoal)
decorators.bind_all(FeederSaltGoal)
