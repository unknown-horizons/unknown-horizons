# ###################################################
# Copyright (C) 2013-2017 The Unknown Horizons Team
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

from horizons.constants import BUILDINGS, RES, TIER
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.world.disaster.buildinginfluencingdisaster import BuildingInfluencingDisaster
from horizons.world.status import BlackDeathStatusIcon


class BlackDeathDisaster(BuildingInfluencingDisaster):
	"""Simulates the Black Death.

	"""

	TYPE = "Happy dying."
	NOTIFICATION_TYPE = 'BUILDING_INFECTED_BY_BLACK_DEATH'

	SEED_CHANCE = 0.015

	EXPANSION_RADIUS = 4

	DISASTER_RES = RES.BLACKDEATH

	BUILDING_TYPE = BUILDINGS.RESIDENTIAL

	MIN_BREAKOUT_TIER = TIER.SETTLERS

	MIN_INHABITANTS_FOR_BREAKOUT = 5

	STATUS_ICON = BlackDeathStatusIcon

	RESCUE_BUILDING_TYPE = BUILDINGS.DOCTOR

	def __init__(self, settlement, manager):
		super().__init__(settlement, manager)
		self.healed_buildings = []

	def infect(self, building, load=None):
		"""@load: (db, disaster_worldid), set on restoring infected state of savegame"""
		if building not in self.healed_buildings:
			super().infect(building, load=load)

	def wreak_havoc(self, building):
		"""Some inhabitants have to die."""
		super()
		if building.inhabitants > 1:
			inhabitants_that_will_die = self._manager.session.random.randint(1, building.inhabitants)
			building.inhabitants -= inhabitants_that_will_die
			self.log.debug("%s inhabitants dying", inhabitants_that_will_die)
			Scheduler().add_new_object(Callback(self.wreak_havoc, building), self, run_in=self.TIME_BEFORE_HAVOC)
		else:
			self.recover(building)

	def recover(self, building):
		self.healed_buildings.append(building)
		super().recover(building)
