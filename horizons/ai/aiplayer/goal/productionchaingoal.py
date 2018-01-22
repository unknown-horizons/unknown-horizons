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

from horizons.ai.aiplayer.constants import BUILD_RESULT
from horizons.ai.aiplayer.goal.settlementgoal import SettlementGoal
from horizons.constants import RES


class ProductionChainGoal(SettlementGoal):
	def __init__(self, settlement_manager, resource_id, name):
		super().__init__(settlement_manager)
		self.chain = settlement_manager.production_chain[resource_id]
		self.name = name
		self._may_import = True

	@property
	def active(self):
		return super().active and self._is_active

	def execute(self):
		result = self.chain.build(self._needed_amount)
		if result != BUILD_RESULT.ALL_BUILT and result != BUILD_RESULT.SKIP:
			self._log_generic_build_result(result, self.name)
		return self._translate_build_result(result)

	def _update_needed_amount(self):
		self._needed_amount = self.settlement_manager.get_resource_production_requirement(self.chain.resource_id) * \
			self.settlement_manager.personality.production_level_multiplier

	def update(self):
		super().update()
		if self.can_be_activated:
			self._update_needed_amount()
			self._current_amount = self.chain.reserve(self._needed_amount, self._may_import)
			self._is_active = self.chain.need_to_build_more_buildings(self._needed_amount)
		else:
			self._is_active = False


class FaithGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.FAITH, 'pavilion')

	def get_personality_name(self):
		return 'FaithGoal'


class TextileGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.TEXTILE, 'textile producer')

	def get_personality_name(self):
		return 'TextileGoal'


class BricksGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.BRICKS, 'bricks producer')

	def get_personality_name(self):
		return 'BricksGoal'


class EducationGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.EDUCATION, 'school')

	def get_personality_name(self):
		return 'EducationGoal'

	@property
	def can_be_activated(self):
		return super().can_be_activated and self.settlement_manager.get_resource_production(RES.BRICKS) > 0


class GetTogetherGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.GET_TOGETHER, 'get-together producer')

	def get_personality_name(self):
		return 'GetTogetherGoal'

	@property
	def can_be_activated(self):
		return super().can_be_activated and self.settlement_manager.get_resource_production(RES.BRICKS) > 0


class ToolsGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.TOOLS, 'tools producer')

	def get_personality_name(self):
		return 'ToolsGoal'

	@property
	def can_be_activated(self):
		return super().can_be_activated \
		   and self.production_builder.have_deposit(RES.RAW_IRON) \
		   and self.settlement_manager.get_resource_production(RES.BRICKS) > 0


class BoardsGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.BOARDS, 'boards producer')

	def get_personality_name(self):
		return 'BoardsGoal'


class FoodGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.FOOD, 'food producer')

	def get_personality_name(self):
		return 'FoodGoal'


class CommunityGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.COMMUNITY, 'main square')

	def get_personality_name(self):
		return 'CommunityGoal'


class TobaccoProductsGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.TOBACCO_PRODUCTS, 'tobacco products producer')

	def get_personality_name(self):
		return 'TobaccoProductsGoal'


class MedicalHerbsProductsGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.MEDICAL_HERBS, 'medical herbs products producer')

	def get_personality_name(self):
		return 'MedicalHerbsProductsGoal'


class SaltGoal(ProductionChainGoal):
	def __init__(self, settlement_manager):
		super().__init__(settlement_manager, RES.SALT, 'salt producer')

	def get_personality_name(self):
		return 'SaltGoal'
