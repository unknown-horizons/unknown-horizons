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

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.buildingevaluator.ironmineevaluator import IronMineEvaluator
from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class AbstractIronMine(AbstractBuilding):
	def iter_potential_locations(self, settlement_manager):
		for building in settlement_manager.land_manager.settlement.get_buildings_by_id(BUILDINGS.MOUNTAIN_CLASS):
			(x, y) = building.position.origin.to_tuple()
			yield (x, y, 0)

	@property
	def evaluator_class(self):
		return IronMineEvaluator

	def get_collector_likelihood(self, building, resource_id):
		return 0 # it should always be picked up by the smeltery collector

	@classmethod
	def register_buildings(cls):
		cls.available_buildings[BUILDINGS.IRON_MINE_CLASS] = cls

AbstractIronMine.register_buildings()

decorators.bind_all(AbstractIronMine)
