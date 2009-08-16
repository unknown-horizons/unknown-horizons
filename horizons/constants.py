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
	HAPPINESS_ID = 14


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
# workaround, so it can be used to create paths withing PATHS
_user_dir = "%s/.unknown-horizons" % user.home
class PATHS:
	USER_DIR = _user_dir
	LOG_DIR = _user_dir + "/log"

## The Production States available in the game sorted by importance from least
## to most important
PRODUCTION_STATES = Enum('waiting_for_res', 'inventory_full', 'producing', 'paused')


## GAME-RELATED, BALANCING VALUES
class SETTLER:
	HAPPINESS_INIT_VALUE = 50 # settlers start with this value
	HAPPINESS_MIN_VALUE = 0 # settlers die at this value
	HAPPINESS_MAX_VALUE = 100
	HAPPINESS_INHABITANTS_INCREASE_REQUIREMENT = 70 # if above this, inhabitants increase
	HAPPINESS_INHABITANTS_DECREASE_LIMIT = 30 # if below this, inhabitants decrease
	HAPPINESS_LEVEL_UP_REQUIREMENT = 80 # happiness has to be over this for leveling up
	HAPPINESS_LEVEL_DOWN_LIMIT = 10 # settlers level down if below this value

	TICK_INTERVAL = 30 # seconds; interval for settler to pay res, check for level up, etc.

class WILD_ANIMAL:
	HEALTH_INIT_VALUE = 50 # animals start with this value
	HEALTH_INCREASE_ON_FEEDING = 2 # health increases by this value on feedig
	HEALTH_DECREASE_ON_NO_JOB = 2 # health decreases by this value when they have no food
	HEALTH_LEVEL_TO_REPRODUCE = 100 # this level has to be reached for reproducing

