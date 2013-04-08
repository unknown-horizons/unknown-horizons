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
from horizons.world.status import FireStatusIcon
from horizons.constants import GAME_SPEED, BUILDINGS, RES, TIER

class FireDisaster(BuildingInfluencingDisaster):
	"""Simulates a fire.

	"""

	TYPE = "The Flames Of The End"
	NOTIFICATION_TYPE = 'BUILDING_ON_FIRE'

	SEED_CHANCE = 0.005

	EXPANSION_RADIUS = 3

	TIME_BEFORE_HAVOC = GAME_SPEED.TICKS_PER_SECOND * 30
	EXPANSION_TIME = (TIME_BEFORE_HAVOC // 2) - 1 # try twice before dying

	DISASTER_RES = RES.FIRE

	BUILDING_TYPE = BUILDINGS.RESIDENTIAL

	MIN_BREAKOUT_TIER = TIER.PIONEERS

	MIN_INHABITANTS_FOR_BREAKOUT = 7

	STATUS_ICON = FireStatusIcon

	def wreak_havoc(self, building):
		super(FireDisaster, self).wreak_havoc(building)
		self._affected_buildings.remove(building)
		building.make_ruin()
