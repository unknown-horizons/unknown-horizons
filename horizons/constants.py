# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import user
from ext.enum import Enum

"""This file keeps track of some constants, that have to be used in the code.
NOTE: Using constants is generally a bad style, so avoid where possible."""

## WORLD
class UNITS:
	PLAYER_SHIP_CLASS          = 1000001
	BUILDING_COLLECTOR_CLASS   = 1000002
	TRADER_SHIP_CLASS          = 1000006
	WILD_ANIMAL_CLASS          = 1000013

class BUILDINGS:
	TREE_CLASS = 17

class RES:
	GOLD_ID   = 1
	BOARDS_ID = 4
	FOOD_ID   = 5
	TOOLS_ID  = 6


## SYSTEM
class MESSAGES:
	NEW_SETTLEMENT = 1
	NEW_WORLD = 2
	QUICKSAVE = 3
	SCREENSHOT = 4

## ENGINE
class LAYERS:
	WATER = 0
	GROUND = 1
	OBJECTS = 2

## PATHS
class PATHS:
	USER_DIR = "%s/.unknown-horizons" % user.home

## The Production States available in the game sorted by importance from least
## to most important
PRODUCTION_STATES = Enum('waiting_for_res', 'inventory_full', 'producing', 'paused')
