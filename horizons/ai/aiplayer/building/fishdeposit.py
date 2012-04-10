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
from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class AbstractFishDeposit(AbstractBuilding):
	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		""" You don't actually build fish deposits """
		return 0

	@property
	def directly_buildable(self):
		""" You don't actually build fish deposits """
		return False

	@property
	def ignore_production(self):
		return True

	@classmethod
	def register_buildings(cls):
		cls._available_buildings[BUILDINGS.FISH_DEPOSIT] = cls

AbstractFishDeposit.register_buildings()

decorators.bind_all(AbstractFishDeposit)
