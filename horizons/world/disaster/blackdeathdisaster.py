# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

from horizons.world.disaster.buildinginfluencingdisaster import BuildingInfluencingDisaster
from horizons.constants import GAME_SPEED, BUILDINGS, RES, TIER
from horizons.world.status import BlackDeathStatusIcon

class BlackDeathDisaster(BuildingInfluencingDisaster):
	"""Simulates the Black Death.

	"""

	TYPE = "Happy dying."
	NOTIFICATION_TYPE = 'BUILDING_INFECTED_BY_BLACK_DEATH'

	SEED_CHANCE = 0.01

	EXPANSION_RADIUS = 7

	TIME_BEFORE_HAVOC = GAME_SPEED.TICKS_PER_SECOND * 4
	EXPANSION_TIME = TIME_BEFORE_HAVOC // 2 # try twice before dying

	DISASTER_RES = RES.BLACKDEATH

	BUILDING_TYPE = BUILDINGS.RESIDENTIAL

	MIN_BREAKOUT_TIER = TIER.SETTLERS

	MIN_INHABITANTS_FOR_BREAKOUT = 5

	STATUS_ICON = BlackDeathStatusIcon

	def wreak_havoc(self, building):
		"""Some inhabitants have to die."""
		super(BlackDeathDisaster, self)
		if building.inhabitants > 1:
			inhabitants_that_will_die = self.session.random.randint(1, building.inhabitants)
			building.inhabitants -= inhabitants_that_will_die
		#	building.
			self.log.debug("%s inhabitants dying", inhabitants_that_will_die)
