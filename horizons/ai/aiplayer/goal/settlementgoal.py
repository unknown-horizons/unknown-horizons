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
from horizons.ai.aiplayer.goal import Goal
from horizons.component.namedcomponent import NamedComponent
from horizons.constants import BUILDINGS


class SettlementGoal(Goal):
	"""
	An object of this class describes a goal that a settlement of an AI player attempts to fulfil.
	"""

	def __init__(self, settlement_manager):
		super().__init__(settlement_manager.owner)
		self.settlement_manager = settlement_manager
		self.land_manager = settlement_manager.land_manager
		self.production_builder = settlement_manager.production_builder
		self.village_builder = settlement_manager.village_builder
		self.settlement = settlement_manager.settlement
		self.island = settlement_manager.island
		self.session = settlement_manager.session

	@property
	def can_be_activated(self):
		return super().can_be_activated and self.personality.residences_required <= self.settlement.count_buildings(BUILDINGS.RESIDENTIAL)

	def __str__(self):
		return super().__str__() + ', ' + self.settlement_manager.settlement.get_component(NamedComponent).name

	def _log_generic_build_result(self, result, name):
		if result == BUILD_RESULT.OK:
			self.log.info('%s built a %s', self, name)
		elif result == BUILD_RESULT.NEED_RESOURCES:
			self.log.info('%s not enough materials to build a %s', self, name)
		elif result == BUILD_RESULT.SKIP:
			self.log.info('%s skipped building a %s', self, name)
		else:
			self.log.info('%s failed to build a %s (%d)', self, name, result)
