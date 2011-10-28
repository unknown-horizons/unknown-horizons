# -.- coding: utf-8 -.-
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

import ctypes
import platform
import os.path
import re
import locale

from horizons.ext.enum import Enum

"""This file keeps track of the constants that are used in Unknown Horizons.
NOTE: Using magic constants in code is generally a bad style, so avoid where
possible and instead import the proper classes of this file.
"""

##Versioning
class VERSION:
	def _set_version():
		"""Function gets latest revision of the working copy.
		It only works in git repositories, and is actually a hack.
		"""
		try:
			from run_uh import find_uh_position
		except ImportError:
			return u"<unknown>"

		uh_path = find_uh_position()
		git_head_path = os.path.join(uh_path, '.git', 'HEAD')
		if os.path.exists(git_head_path):
			head = open(git_head_path).readline().strip().partition(' ')
			if head[2]:
				head_file = os.path.join(uh_path, '.git', head[2])
			else:
				head_file = git_head_path
			if os.path.exists(head_file):
				return unicode(open(head_file).readline().strip()[0:7])
		return u"<unknown>"

	RELEASE_NAME    = "Unknown Horizons Version %s"
	RELEASE_VERSION = _set_version()

	# change to sth like this for release, please don't add %s to the first string
	#RELEASE_NAME = _("Unknown Horizons") + unicode(" %s")
	#RELEASE_VERSION = u'2011.3'

	## +=1 this if you changed the savegame "api"
	SAVEGAMEREVISION= 43

	@staticmethod
	def string():
		return VERSION.RELEASE_NAME % VERSION.RELEASE_VERSION

## WORLD
class UNITS:
	# ./development/print_db_data.py unit
	PLAYER_SHIP_CLASS          = 1000001
	BUILDING_COLLECTOR_CLASS   = 1000002
	FISHER_BOAT                = 1000004
	PIRATE_SHIP_CLASS          = 1000005
	TRADER_SHIP_CLASS          = 1000006
	WILD_ANIMAL_CLASS          = 1000013
	USABLE_FISHER_BOAT         = 1000016
	FRIGATE                    = 1000020

	DIFFERENCE_BUILDING_UNIT_ID = 1000000

class WEAPONS:
	CANNON = 40
	DAGGER = 41

class BUILDINGS:
	# ./development/print_db_data.py building
	BRANCH_OFFICE_CLASS = 1
	STORAGE_CLASS = 2
	RESIDENTIAL_CLASS = 3
	MAIN_SQUARE_CLASS = 4
	PAVILION_CLASS = 5
	SIGNAL_FIRE_CLASS = 6
	WEAVER_CLASS = 7
	LUMBERJACK_CLASS = 8
	HUNTER_CLASS = 9
	SETTLER_RUIN_CLASS = 10
	FISHERMAN_CLASS = 11
	BOATBUILDER_CLASS = 12
	TRAIL_CLASS = 15
	TREE_CLASS = 17
	PASTURE_CLASS = 18
	POTATO_FIELD_CLASS = 19
	FARM_CLASS = 20
	VILLAGE_SCHOOL_CLASS = 21
	SUGARCANE_FIELD_CLASS = 22
	CLAY_DEPOSIT_CLASS = 23
	BRICKYARD_CLASS = 24
	CLAY_PIT_CLASS = 25
	DISTILLERY_CLASS = 26
	IRON_MINE_CLASS = 28
	SMELTERY_CLASS = 29
	TOOLMAKER_CLASS = 30
	CHARCOAL_BURNER_CLASS = 31
	TAVERN_CLASS = 32
	FISH_DEPOSIT_CLASS = 33
	MOUNTAIN_CLASS = 34
	SALT_PONDS_CLASS = 35
	TOBACCO_FIELD_CLASS = 36
	TOBACCONIST_CLASS = 37

	TRANSPARENCY_VALUE = 180

	class ACTION:
		# data for calculating gfx for paths.
		# think: animation contains key, if there is a path at offset value
		# you need to sort this before iterating via sorted, since order is important here
		action_offset_dict = {
		'a' : (0, -1),
		'b' : (1, 0),
		'c' : (0, 1),
		'd' : (-1, 0)
		}

	class BUILD:
		MAX_BUILDING_SHIP_DISTANCE = 5 # max distance ship-building when building from ship

class RES:
	# ./development/print_db_data.py res
	GOLD_ID = 1
	LAMB_WOOL_ID = 2
	TEXTILE_ID = 3
	BOARDS_ID = 4
	FOOD_ID = 5
	TOOLS_ID = 6
	BRICKS_ID = 7
	WOOD_ID = 8
	WOOL_ID = 10
	FAITH_ID = 11
	WILDANIMALFOOD_ID = 12
	DEER_MEAT_ID = 13
	HAPPINESS_ID = 14
	POTATOES_ID = 15
	EDUCATION_ID = 16
	RAW_SUGAR_ID = 17
	SUGAR_ID = 18
	COMMUNITY_ID = 19
	RAW_CLAY_ID = 20
	CLAY_ID = 21
	LIQUOR_ID = 22
	RAW_IRON_ID = 24
	GET_TOGETHER_ID = 27
	FISH_ID = 28
	SALT_ID = 29
	TOBACCO_PLANTS_ID = 30
	TOBACCO_LEAVES_ID = 31
	TOBACCO_PRODUCTS_ID = 32

class GROUND:
	DEFAULT_LAND = 1
	SAND = 2
	SHALLOW_WATER = 3
	WATER = 4

	# sand to shallow water tiles
	COAST_SOUTH = 49
	COAST_EAST = 50
	COAST_NORTH = 51
	COAST_WEST = 52
	COAST_SOUTHWEST3 = 60
	COAST_NORTHWEST3 = 59
	COAST_NORTHEAST3 = 58
	COAST_SOUTHEAST3 = 57
	COAST_NORTHEAST1 = 65
	COAST_SOUTHEAST1 = 66
	COAST_SOUTHWEST1 = 67
	COAST_NORTHWEST1 = 68

	# grass to sand tiles
	SAND_SOUTH = 9
	SAND_EAST = 10
	SAND_NORTH = 11
	SAND_WEST = 12
	SAND_SOUTHWEST3 = 20
	SAND_NORTHWEST3 = 19
	SAND_NORTHEAST3 = 18
	SAND_SOUTHEAST3 = 17
	SAND_NORTHEAST1 = 25
	SAND_SOUTHEAST1 = 26
	SAND_SOUTHWEST1 = 27
	SAND_NORTHWEST1 = 28

	# shallow water to deep water tiles
	DEEP_WATER_SOUTH = 89
	DEEP_WATER_EAST = 90
	DEEP_WATER_NORTH = 91
	DEEP_WATER_WEST = 92
	DEEP_WATER_SOUTHWEST3 = 100
	DEEP_WATER_NORTHWEST3 = 99
	DEEP_WATER_NORTHEAST3 = 98
	DEEP_WATER_SOUTHEAST3 = 97
	DEEP_WATER_NORTHEAST1 = 105
	DEEP_WATER_SOUTHEAST1 = 106
	DEEP_WATER_SOUTHWEST1 = 107
	DEEP_WATER_NORTHWEST1 = 108

class GAME_SPEED:
	TICKS_PER_SECOND = 16
	TICK_RATES = [8, 16, 32, 48, 64, 96, 128, 176] #starting at 0.5x with max of 11x

class COLORS:
	BLACK = 9

class VIEW:
	ZOOM_MAX = 1
	ZOOM_MIN = 0.25
	ZOOM_LEVELS_FACTOR = 0.875
	CELL_IMAGE_DIMENSIONS = (64, 32)
	ROTATION = 45.0
	TILT = -60
	ZOOM = 1

## The Production States available in the game sorted by importance from least
## to most important
class PRODUCTION:
	# ./development/print_db_data.py lines
	STATES = Enum('none', 'waiting_for_res', 'inventory_full', 'producing', 'paused', 'done')
	# NOTE: 'done' is only for SingleUseProductions
	# NOTE: 'none' is not used by an actual production, just for a producer
	STATISTICAL_WINDOW = 1000 # How many latest ticks are relevant for keeping track of how busy a production is

class PRODUCTIONLINES:
	HUKER = 15
	FISHING_BOAT = None # will get added later
	FRIGATE = 58

## GAME-RELATED, BALANCING VALUES
class GAME:
	INGAME_TICK_INTERVAL = 30 # seconds. duration of a "month" (running costs and taxes are
	# payed in this interval).

	WORLD_WORLDID = 0 # worldid of World object
	MAX_TICKS = None # exit after on tick MAX_TICKS (disabled by setting to None)

# Messagewidget and Logbook
class MESSAGES:
	CUSTOM_MSG_SHOW_DELAY = 6 # delay between messages when passing more than one
	CUSTOM_MSG_VISIBLE_FOR = 90 # after this time the msg gets removed from screen
	LOGBOOK_DEFAULT_DELAY = 4 # delay between condition fulfilled and logbook popping up

# AI values read from the command line; use the values below unless overridden by the CLI or the GUI
class AI:
	HIGHLIGHT_PLANS = False # whether to show the AI players' plans on the map
	AI_PLAYERS = 1 # number of AI players in a game started from the command line
	HUMAN_AI = False # whether the human player is controlled by the AI

class TRADER: # check resource values: ./development/print_db_data.py res
	PRICE_MODIFIER_BUY = 0.9  # buy for x times the resource value
	PRICE_MODIFIER_SELL = 1.5 # sell for x times the resource value
	TRADING_DURATION = 4 # seconds that trader stays at branch office to simulate (un)loading

	BUSINESS_SENSE = 50 # chance in percent to be sent to a branch office instead of random spot

	BUY_AMOUNT = (2, 8)  # amount range to buy/sell from settlement per resource
	SELL_AMOUNT = (2, 8) # => randomly picks an amount in this range for each trade

# Taxes and Restrictions
class SETTLER:
	SAILOR_LEVEL = 0
	PIONEER_LEVEL = 1
	SETTLER_LEVEL = 2
	CURRENT_MAX_INCR = 2 # counting starts at 0!
	TAX_SETTINGS_MIN = 0.5
	TAX_SETTINGS_MAX = 1.5
	TAX_SETTINGS_STEP = 0.1

class WILD_ANIMAL:
	HEALTH_INIT_VALUE = 50 # animals start with this value
	HEALTH_INCREASE_ON_FEEDING = 8 # health increases by this value on feeding
	HEALTH_DECREASE_ON_NO_JOB = 20 # health decreases by this value when they have no food
	HEALTH_LEVEL_TO_REPRODUCE = 75 # this level has to be reached for reproducing
	POPULATION_LIMIT = 15 # minimum number of trees per animal to allow reproducing
	FOOD_AVAILABLE_ON_START = 0.5 # probability that a tree has wild animal food in the beginning
	POPUlATION_INIT_RATIO = 15 # every N-th tree gets an animal in the beginning

class COLLECTORS:
	DEFAULT_WORK_DURATION = 16 # how many ticks collectors pretend to work at target
	DEFAULT_WAIT_TICKS = 32 # how long collectors wait before again looking for a job
	DEFAULT_STORAGE_SIZE = 8
	STATISTICAL_WINDOW = 1000 # How many latest ticks are relevant for calculating how busy a collector is

class STORAGE:
	DEFAULT_STORAGE_SIZE = 30 # Our usual inventorys are 30 tons big

	# Distributing overall delimiter, if one slot is "full" with respect to
	# this value, you can't load further in any of the slots even if empty.
	SHIP_TOTAL_STORAGE = 120
	SHIP_TOTAL_SLOTS_NUMBER = 4

## ENGINE
class LAYERS:
	WATER = 0
	GROUND = 1
	FIELDS = 2
	OBJECTS = 3

	NUM = 4 # number of layers

## PATHS
# workaround, so it can be used to create paths within PATHS

if platform.system() != "Windows":
	_user_dir = os.path.join(os.path.expanduser('~'), '.unknown-horizons')
else:
	dll = ctypes.windll.shell32
	buf = ctypes.create_string_buffer(300)
	dll.SHGetSpecialFolderPathA(None, buf, 0x0005, False) # get the My Documents folder
	my_games = os.path.join(buf.value, 'My Games')
	if not os.path.exists(my_games):
		os.makedirs(my_games)
	_user_dir = os.path.join(my_games, 'unknown-horizons')
_user_dir = unicode(_user_dir, locale.getpreferredencoding()) # this makes umlaut-paths work on win

class PATHS:
	# paths in user dir
	USER_DIR = _user_dir
	LOG_DIR = os.path.join(_user_dir, "log")
	USER_CONFIG_FILE = os.path.join(_user_dir, "settings.xml")
	SCREENSHOT_DIR = os.path.join(_user_dir, "screenshots")

	# paths relative to uh dir
	ACTION_SETS_DIRECTORY = os.path.join("content", "gfx")
	TILE_SETS_DIRECTORY = os.path.join("content", "gfx", "base")
	SAVEGAME_TEMPLATE = os.path.join("content", "savegame_template.sqlite")
	ACTION_SETS_JSON_FILE = os.path.join("content", "actionsets.json")

	CONFIG_TEMPLATE_FILE = os.path.join("content", "settings-template.xml")

	DB_FILES = tuple(os.path.join("content", i) for i in \
	                 ("game.sql", "balance.sql", "atlas.sql") )
	#voice paths
	VOICE_DIR = os.path.join("content", "audio", "voice")

class PLAYER:
	STATS_UPDATE_FREQUENCY = 42

## SINGLEPLAYER
class SINGLEPLAYER:
	SEED = None

## MULTIPLAYER
class MULTIPLAYER:
	MAX_PLAYER_COUNT = 8

class NETWORK:
	SERVER_ADDRESS = "master.unknown-horizons.org"
	SERVER_PORT = 2002
	CLIENT_ADDRESS = None

## TRANSLATIONS
class _LanguageNameDict(dict):
	def __getitem__(self, key):
		return self.get(key, key)

LANGUAGENAMES = _LanguageNameDict({
	"bg"    : u'Български',
	"ca"    : u'Català',
  'ca@valencia' : u'Català de València',
	"cs"    : u'Čeština',
	"da"    : u'Danske',
	"de"    : u'Deutsch',
	"en"    : u'English',
	"es"    : u'Español',
	"et"    : u'Eesti',
	"fi"    : u'Suomi',
	"fr"    : u'Français',
	"hu"    : u'Magyar',
	"it"    : u'Italiano',
	"lt"    : u'Lietuvių',
	"nb"    : u'Norw. Bokmål',
	"nl"    : u'Nederlands',
	"pl"    : u'Polski',
	"pt_BR" : u'Português Br.',
	"pt"    : u'Português',
	"ru"    : u'Русский',
	"sl"    : u'Slovenski',
	"sv"    : u'Svenska',
	})

AUTO_CONTINUE_CAMPAIGN=True
