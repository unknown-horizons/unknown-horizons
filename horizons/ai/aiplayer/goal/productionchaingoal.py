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
from horizons.ai.aiplayer.constants import BUILD_RESULT

from horizons.constants import BUILDINGS, RES
from horizons.util.python import decorators

class ProductionChainGoal(SettlementGoal):
	def __init__(self, settlement_manager, chain, name):
		super(ProductionChainGoal, self).__init__(settlement_manager)
		self.__init(chain, name)

	def __init(self, chain, name):
		self.chain = chain
		self.name = name
		self._may_import = True

	@property
	def active(self):
		return self._is_active

	@property
	def priority(self):
		priorities = {
			RES.BOARDS_ID: 950,
			RES.COMMUNITY_ID: 900,
			RES.FOOD_ID: 800,
			RES.FAITH_ID: 700,
			RES.TEXTILE_ID: 500,
			RES.BRICKS_ID: 350,
			RES.EDUCATION_ID: 300,
			RES.LIQUOR_ID: 250,
			RES.GET_TOGETHER_ID: 250,
			RES.TOOLS_ID: 150
		}
		return priorities[self.chain.resource_id] + self.settlement_manager.feeder_island

	def execute(self):
		result = self.chain.build(self._needed_amount)
		if result != BUILD_RESULT.ALL_BUILT and result != BUILD_RESULT.SKIP:
			self.settlement_manager.log_generic_build_result(result, self.name)
		return self._translate_build_result(result)

	def _update_needed_amount(self):
		self._needed_amount = self.settlement_manager.get_resident_resource_usage(self.chain.resource_id) * \
			self.settlement_manager.personality.production_level_multiplier

	def update(self):
		super(ProductionChainGoal, self).update()
		if self.can_be_activated:
			self._update_needed_amount()
			self._current_amount = self.chain.reserve(self._needed_amount, self._may_import)
			self._is_active = self.chain.need_to_build_more_buildings(self._needed_amount)
		else:
			self._is_active = False

class FaithGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.settlement_manager.tents >= 10

class TextileGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.settlement_manager.tents >= 16 and self.owner.settler_level > 0

class BricksGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.owner.settler_level > 0

class EducationGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.settlement_manager.get_resource_production(RES.BRICKS_ID) > 0

class GetTogetherGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.owner.settler_level > 1 and self.settlement_manager.get_resource_production(RES.BRICKS_ID) > 0

class ToolsGoal(ProductionChainGoal):
	@property
	def can_be_activated(self):
		return self.owner.settler_level > 1 and self.settlement_manager.have_deposit(BUILDINGS.MOUNTAIN_CLASS) and \
			self.settlement_manager.get_resource_production(RES.BRICKS_ID) > 0

decorators.bind_all(ProductionChainGoal)
decorators.bind_all(FaithGoal)
decorators.bind_all(TextileGoal)
decorators.bind_all(BricksGoal)
decorators.bind_all(EducationGoal)
decorators.bind_all(GetTogetherGoal)
decorators.bind_all(ToolsGoal)
