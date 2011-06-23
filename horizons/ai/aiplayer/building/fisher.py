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

import math

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator.fisherevaluator import FisherEvaluator
from horizons.constants import BUILDINGS, PRODUCTION
from horizons.util.python import decorators

class AbstractFisher(AbstractBuilding):
	def get_production_level(self, building, resource_id):
		if building.get_history_length(resource_id) < PRODUCTION.COUNTER_LIMIT:
			return self.get_expected_production_level(resource_id)
		else:
			return building.get_absolute_production_level(resource_id)

	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		evaluators = self.get_evaluators(settlement_manager, resource_id)
		if not evaluators:
			return None

		evaluator = sorted(evaluators)[0]
		current_expected_production_level = evaluator.get_expected_production_level(resource_id)
		extra_buildings_needed = math.ceil(max(0.0, production_needed / current_expected_production_level))
		return extra_buildings_needed * self.get_expected_building_cost()

	@property
	def evaluator_class(self):
		return FisherEvaluator

	@classmethod
	def register_buildings(cls):
		cls.available_buildings[BUILDINGS.FISHERMAN_CLASS] = cls

AbstractFisher.register_buildings()

decorators.bind_all(AbstractFisher)
