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

from horizons.constants import BUILDINGS
from horizons.util.python import decorators

class BUILD_RESULT:
	OK = 0
	NEED_RESOURCES = 1
	IMPOSSIBLE = 2
	UNKNOWN_ERROR = 3
	ALL_BUILT = 4
	NEED_PARENT_FIRST = 5
	SKIP = 6
	OUT_OF_SETTLEMENT = 7

class GOAL_RESULT:
	SKIP = 0 # just execute the next goal
	BLOCK_SETTLEMENT_RESOURCE_USAGE = 1 # don't execute any goal that uses resources in this settlement
	BLOCK_ALL_BUILDING_ACTIONS = 2 # no more building during this tick

class BUILDING_PURPOSE:
	NONE = 1
	RESERVED = 2
	WAREHOUSE = 3
	ROAD = 4
	FISHER = 5
	LUMBERJACK = 6
	TREE = 7
	STORAGE = 8
	FARM = 9
	POTATO_FIELD = 10
	CLAY_PIT = 11
	BRICKYARD = 12
	PASTURE = 13
	WEAVER = 14
	SUGARCANE_FIELD = 15
	DISTILLERY = 16
	MAIN_SQUARE = 17
	RESIDENCE = 18
	PAVILION = 19
	VILLAGE_SCHOOL = 20
	TAVERN = 21
	IRON_MINE = 22
	SMELTERY = 23
	TOOLMAKER = 24
	CHARCOAL_BURNER = 25
	BOAT_BUILDER = 26
	SIGNAL_FIRE = 27
	TOBACCO_FIELD = 28
	TOBACCONIST = 29
	SALT_PONDS = 30
	FIRE_STATION = 31

	purpose_to_building = {}
	building_to_purpose = {}

	@classmethod
	def init_translation(cls):
		cls.purpose_to_building[cls.WAREHOUSE] = BUILDINGS.WAREHOUSE_CLASS
		cls.purpose_to_building[cls.ROAD] = BUILDINGS.TRAIL_CLASS
		cls.purpose_to_building[cls.FISHER] = BUILDINGS.FISHERMAN_CLASS
		cls.purpose_to_building[cls.LUMBERJACK] = BUILDINGS.LUMBERJACK_CLASS
		cls.purpose_to_building[cls.TREE] = BUILDINGS.TREE_CLASS
		cls.purpose_to_building[cls.STORAGE] = BUILDINGS.STORAGE_CLASS
		cls.purpose_to_building[cls.FARM] = BUILDINGS.FARM_CLASS
		cls.purpose_to_building[cls.POTATO_FIELD] = BUILDINGS.POTATO_FIELD_CLASS
		cls.purpose_to_building[cls.CLAY_PIT] = BUILDINGS.CLAY_PIT_CLASS
		cls.purpose_to_building[cls.BRICKYARD] = BUILDINGS.BRICKYARD_CLASS
		cls.purpose_to_building[cls.PASTURE] = BUILDINGS.PASTURE_CLASS
		cls.purpose_to_building[cls.WEAVER] = BUILDINGS.WEAVER_CLASS
		cls.purpose_to_building[cls.SUGARCANE_FIELD] = BUILDINGS.SUGARCANE_FIELD_CLASS
		cls.purpose_to_building[cls.DISTILLERY] = BUILDINGS.DISTILLERY_CLASS
		cls.purpose_to_building[cls.MAIN_SQUARE] = BUILDINGS.MAIN_SQUARE_CLASS
		cls.purpose_to_building[cls.RESIDENCE] = BUILDINGS.RESIDENTIAL_CLASS
		cls.purpose_to_building[cls.PAVILION] = BUILDINGS.PAVILION_CLASS
		cls.purpose_to_building[cls.VILLAGE_SCHOOL] = BUILDINGS.VILLAGE_SCHOOL_CLASS
		cls.purpose_to_building[cls.TAVERN] = BUILDINGS.TAVERN_CLASS
		cls.purpose_to_building[cls.IRON_MINE] = BUILDINGS.IRON_MINE_CLASS
		cls.purpose_to_building[cls.SMELTERY] = BUILDINGS.SMELTERY_CLASS
		cls.purpose_to_building[cls.TOOLMAKER] = BUILDINGS.TOOLMAKER_CLASS
		cls.purpose_to_building[cls.CHARCOAL_BURNER] = BUILDINGS.CHARCOAL_BURNER_CLASS
		cls.purpose_to_building[cls.BOAT_BUILDER] = BUILDINGS.BOATBUILDER_CLASS
		cls.purpose_to_building[cls.SIGNAL_FIRE] = BUILDINGS.SIGNAL_FIRE_CLASS
		cls.purpose_to_building[cls.TOBACCO_FIELD] = BUILDINGS.TOBACCO_FIELD_CLASS
		cls.purpose_to_building[cls.TOBACCONIST] = BUILDINGS.TOBACCONIST_CLASS
		cls.purpose_to_building[cls.SALT_PONDS] = BUILDINGS.SALT_PONDS_CLASS
		cls.purpose_to_building[cls.FIRE_STATION] = BUILDINGS.FIRE_STATION_CLASS

		for purpose, building_id in cls.purpose_to_building.iteritems():
			cls.building_to_purpose[building_id] = purpose

	@classmethod
	def get_building(cls, purpose):
		return cls.purpose_to_building[purpose]

	@classmethod
	def get_purpose(cls, building_id):
		return cls.purpose_to_building[building_id]

BUILDING_PURPOSE.init_translation()

decorators.bind_all(BUILD_RESULT)
decorators.bind_all(GOAL_RESULT)
decorators.bind_all(BUILDING_PURPOSE)
