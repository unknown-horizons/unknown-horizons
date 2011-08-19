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
from horizons.ai.aiplayer.buildingevaluator.signalfireevaluator import SignalFireEvaluator
from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class AbstractSignalFire(AbstractBuilding):
	def iter_potential_locations(self, settlement_manager):
		for (x, y) in settlement_manager.branch_office.position.get_radius_coordinates(self.radius):
			if (x, y) in settlement_manager.production_builder.plan:
				if (x, y) in settlement_manager.island.last_changed[self.size]:
					yield (x, y, 0)

	@property
	def evaluator_class(self):
		return SignalFireEvaluator

	@property
	def producer_building(self):
		""" signal fires don't produce anything """
		return False

	@classmethod
	def register_buildings(cls):
		cls.available_buildings[BUILDINGS.SIGNAL_FIRE_CLASS] = cls

AbstractSignalFire.register_buildings()

decorators.bind_all(AbstractSignalFire)
