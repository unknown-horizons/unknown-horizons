# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
import os
import os.path
import platform
import subprocess
from pathlib import Path
from typing import List, Optional

from horizons.ext.enum import Enum
from horizons.util.platform import get_old_user_game_directory, get_user_game_directories


"""This file keeps track of the constants that are used in Unknown Horizons.
NOTE: Using magic constants in code is generally a bad style, so avoid where
possible and instead import the proper classes of this file.
"""


def get_git_version():
	"""Function gets latest revision of the working copy.
	It only works in git repositories, and is actually a hack.
	"""
	try:
		from run_uh import get_content_dir_parent_path
		uh_path = get_content_dir_parent_path()
	except ImportError:
		return "<unknown>"

	# Try git describe
	try:
		git = "git"
		if platform.system() == "Windows":
			git = "git.exe"

		# Note that this uses glob patterns, not regular expressions.
		# TAG_STRUCTURE = "20[0-9][0-9].[0-9]*"
		# describe = [git, "describe", "--tags", TAG_STRUCTURE]
		describe = [git, "describe", "--tags"]
		git_string = subprocess.check_output(describe, cwd=uh_path, universal_newlines=True).rstrip('\n')
		return git_string
	except (subprocess.CalledProcessError, RuntimeError):
		pass

	# Read current HEAD out of .git manually
	try:
		git_head_path = Path(uh_path, '.git', 'HEAD')
		if git_head_path.exists():
			with git_head_path.open() as f:
				head = f.readline().strip().partition(' ')
			if head[2]:
				head_file = Path(uh_path, '.git', head[2])
			else:
				head_file = git_head_path

			if head_file.exists():
				with head_file.open() as f:
					return str(f.readline().strip()[0:7])
	except ImportError:
		pass

	# Try gitversion.txt
	try:
		with open(os.path.join("content", "packages", "gitversion.txt")) as f:
			return f.read()
	except IOError:
		pass

	return "<unknown>"


##Versioning
class VERSION:
	RELEASE_NAME    = "Unknown Horizons %s"
	RELEASE_VERSION = get_git_version()
	# change for release:
	IS_DEV_VERSION = True
	#RELEASE_VERSION = u'2019.1'

	REQUIRED_FIFE_MAJOR_VERSION = 0
	REQUIRED_FIFE_MINOR_VERSION = 4
	REQUIRED_FIFE_PATCH_VERSION = 2

	REQUIRED_FIFE_VERSION = (REQUIRED_FIFE_MAJOR_VERSION, REQUIRED_FIFE_MINOR_VERSION, REQUIRED_FIFE_PATCH_VERSION)

	## +=1 this if you changed the savegame "api"
	SAVEGAMEREVISION = 77
	SAVEGAME_LEAST_UPGRADABLE_REVISION = 76

	@staticmethod
	def string():
		return VERSION.RELEASE_NAME % VERSION.RELEASE_VERSION


## WORLD
class UNITS:
	# ./development/print_db_data.py unit
	HUKER_SHIP           = 1000001
	BUILDING_COLLECTOR   = 1000002

	FISHER_BOAT          = 1000004
	PIRATE_SHIP          = 1000005
	TRADER_SHIP          = 1000006
	ANIMAL_COLLECTOR     = 1000007
	STORAGE_COLLECTOR    = 1000008
	FIELD_COLLECTOR      = 1000009
	LUMBERJACK_COLLECTOR = 1000010
	SETTLER_COLLECTOR    = 1000011

	WILD_ANIMAL          = 1000013
	HUNTER_COLLECTOR     = 1000014
	FARM_ANIMAL_COLLECTOR = 1000015
	USABLE_FISHER_BOAT   = 1000016

	FRIGATE              = 1000020

	DISASTER_RECOVERY_COLLECTOR = 1000022

	SWORDSMAN            = 1000023

	# players will be spawned with an instance of this
	PLAYER_SHIP          = HUKER_SHIP

	DIFFERENCE_BUILDING_UNIT_ID = 1000000


class BUILDINGS:
	# ./development/print_db_data.py building
	WAREHOUSE        =  1
	STORAGE          =  2
	RESIDENTIAL      =  3
	MAIN_SQUARE      =  4
	PAVILION         =  5
	SIGNAL_FIRE      =  6
	WEAVER           =  7
	LUMBERJACK       =  8
	HUNTER           =  9
	SETTLER_RUIN     = 10
	FISHER           = 11
	BOAT_BUILDER     = 12
	LOOKOUT          = 13

	TRAIL            = 15

	TREE             = 17
	PASTURE          = 18
	POTATO_FIELD     = 19
	FARM             = 20
	VILLAGE_SCHOOL   = 21
	SUGARCANE_FIELD  = 22
	CLAY_DEPOSIT     = 23
	BRICKYARD        = 24
	CLAY_PIT         = 25
	DISTILLERY       = 26

	MINE             = 28
	SMELTERY         = 29
	TOOLMAKER        = 30
	CHARCOAL_BURNER  = 31
	TAVERN           = 32
	FISH_DEPOSIT     = 33
	MOUNTAIN         = 34
	SALT_PONDS       = 35
	TOBACCO_FIELD    = 36
	TOBACCONIST      = 37
	CATTLE_RUN       = 38
	PIGSTY           = 39
	HERBARY          = 40
	BUTCHERY         = 41
	DOCTOR           = 42
	GRAVEL_PATH      = 43
	WOODEN_TOWER     = 44
	FIRE_STATION     = 45
	CORN_FIELD       = 46
	WINDMILL         = 47
	BAKERY           = 48
	SPICE_FIELD      = 49
	BLENDER          = 50

	BARRACKS         = 53
	STONE_PIT        = 54
	STONEMASON       = 55

	COCOA_FIELD      = 60
	VINEYARD         = 61
	ALVEARIES        = 62
	PASTRY_SHOP      = 63

	WINERY           = 65

	WEAPONSMITH      = 66
	CANNON_FOUNDRY   = 67

	BREWERY          = 68
	HOP_FIELD        = 69

	STONE_DEPOSIT    = 70

	BARRIER          = 71

	AMBIENT          = 72

	SALINE           = 86
	PUBLIC_BATH      = 87

	EXPAND_RANGE = (WAREHOUSE, STORAGE, LOOKOUT)

	TRANSPARENCY_VALUE = 180

	class ACTION:
		# data for calculating gfx for paths.
		# think: animation contains key, if there is a path at offset value
		# you need to sort this before iterating via sorted, since order is important here.
		action_offset_dict = {
		# Direct connections
		  'a': (0, -1),
		  'b': (+1, 0),
		  'c': (0, +1),
		  'd': (-1, 0),
		# Remote connections
		  'e': (+1, -1),
		  'f': (+1, +1),
		  'g': (-1, +1),
		  'h': (-1, -1),
		}

	class BUILD:
		MAX_BUILDING_SHIP_DISTANCE = 5 # max distance ship-building when building from ship


class RES:
	# ./development/print_db_data.py res
	GOLD             =  1
	LAMB_WOOL        =  2
	TEXTILE          =  3
	BOARDS           =  4
	FOOD             =  5
	TOOLS            =  6
	BRICKS           =  7
	TREES            =  8
	GRASS            =  9
	WOOL             = 10
	FAITH            = 11
	WILDANIMALFOOD   = 12
	DEER_MEAT        = 13
	HAPPINESS        = 14
	POTATOES         = 15
	EDUCATION        = 16
	RAW_SUGAR        = 17
	SUGAR            = 18
	COMMUNITY        = 19
	RAW_CLAY         = 20
	CLAY             = 21
	LIQUOR           = 22
	CHARCOAL         = 23
	RAW_IRON         = 24
	IRON_ORE         = 25
	IRON_INGOTS      = 26
	GET_TOGETHER     = 27
	FISH             = 28
	SALT             = 29
	TOBACCO_PLANTS   = 30
	TOBACCO_LEAVES   = 31
	TOBACCO_PRODUCTS = 32
	CATTLE           = 33
	PIGS             = 34
	CATTLE_SLAUGHTER = 35
	PIGS_SLAUGHTER   = 36
	HERBS            = 37
	MEDICAL_HERBS    = 38
	ACORNS           = 39
	CANNON           = 40
	SWORD            = 41
	GRAIN            = 42
	CORN             = 43
	FLOUR            = 44
	SPICE_PLANTS     = 45
	SPICES           = 46
	CONDIMENTS       = 47
	MARBLE_DEPOSIT   = GOLD # 48
	MARBLE_TOPS      = GOLD # 49
	COAL_DEPOSIT     = GOLD # 50
	STONE_DEPOSIT    = 51
	STONE_TOPS       = 52
	COCOA_BEANS      = 53
	COCOA            = 54
	CONFECTIONERY    = 55
	CANDLES          = 56
	VINES            = 57
	GRAPES           = 58
	ALVEARIES        = 59
	HONEYCOMBS       = 60
	GOLD_DEPOSIT     = GOLD # 61
	GOLD_ORE         = GOLD # 62
	GOLD_INGOTS      = GOLD # 63
	GEM_DEPOSIT      = GOLD # 64
	ROUGH_GEMS       = GOLD # 65
	GEMS             = GOLD # 66
	SILVER_DEPOSIT   = GOLD # 67
	SILVER_ORE       = GOLD # 68
	SILVER_INGOTS    = GOLD # 69
	COFFEE_PLANTS    = GOLD # 70
	COFFEE_BEANS     = GOLD # 71
	COFFEE           = GOLD # 72
	TEA_PLANTS       = GOLD # 73
	TEA_LEAVES       = GOLD # 74
	TEA              = GOLD # 75
	FLOWER_MEADOWS   = GOLD # 76
	BLOSSOMS         = GOLD # 77
	BRINE            = GOLD # 78
	BRINE_DEPOSIT    = GOLD # 79
	WHALES           = GOLD # 80
	AMBERGRIS        = GOLD # 81
	LAMP_OIL         = GOLD # 82
	COTTON_PLANTS    = GOLD # 83
	COTTON           = GOLD # 84
	INDIGO_PLANTS    = GOLD # 85
	INDIGO           = GOLD # 86
	GARMENTS         = GOLD # 87
	PERFUME          = GOLD # 88
	HOP_PLANTS       = 89
	HOPS             = 90
	BEER             = 91
	# 92-99 reserved for services
	REPRESENTATION   = GOLD # 92
	SOCIETY          = GOLD # 93
	FAITH_2          = GOLD # 94
	EDUCATION_2      = GOLD # 95
	HYGIENE          = 96
	RECREATION       = GOLD # 97
	BLACKDEATH       = 98
	FIRE             = 99
	# 92-99 reserved for services


class WEAPONS:
	CANNON = RES.CANNON
	SWORD  = RES.SWORD

	DEFAULT_FIGHTING_SHIP_WEAPONS_NUM = 7


class GROUND:
	DEFAULT_LAND = (3, "straight", 45)
	SAND = (6, "straight", 45)
	SHALLOW_WATER = (1, "straight", 45)
	WATER = (0, "straight", 45)

	# sand to shallow water tiles
	COAST_SOUTH = (5, "straight", 45)
	COAST_EAST = (5, "straight", 135)
	COAST_NORTH = (5, "straight", 225)
	COAST_WEST = (5, "straight", 315)
	COAST_SOUTHWEST3 = (5, "curve_in", 135)
	COAST_NORTHWEST3 = (5, "curve_in", 225)
	COAST_NORTHEAST3 = (5, "curve_in", 315)
	COAST_SOUTHEAST3 = (5, "curve_in", 45)
	COAST_NORTHEAST1 = (5, "curve_out", 225)
	COAST_SOUTHEAST1 = (5, "curve_out", 135)
	COAST_SOUTHWEST1 = (5, "curve_out", 45)
	COAST_NORTHWEST1 = (5, "curve_out", 315)

	# grass to sand tiles
	SAND_SOUTH = (4, "straight", 45)
	SAND_EAST =  (4, "straight", 135)
	SAND_NORTH = (4, "straight", 225)
	SAND_WEST =  (4, "straight", 315)
	SAND_SOUTHWEST3 = (4, "curve_in", 135)
	SAND_NORTHWEST3 = (4, "curve_in", 225)
	SAND_NORTHEAST3 = (4, "curve_in", 315)
	SAND_SOUTHEAST3 = (4, "curve_in", 45)
	SAND_NORTHEAST1 = (4, "curve_out", 225)
	SAND_SOUTHEAST1 = (4, "curve_out", 135)
	SAND_SOUTHWEST1 = (4, "curve_out", 45)
	SAND_NORTHWEST1 = (4, "curve_out", 315)

	# shallow water to deep water tiles
	DEEP_WATER_SOUTH = (2, "straight", 45)
	DEEP_WATER_EAST =  (2, "straight", 135)
	DEEP_WATER_NORTH = (2, "straight", 225)
	DEEP_WATER_WEST =  (2, "straight", 315)
	DEEP_WATER_SOUTHWEST3 = (2, "curve_in", 135)
	DEEP_WATER_NORTHWEST3 = (2, "curve_in", 225)
	DEEP_WATER_NORTHEAST3 = (2, "curve_in", 315)
	DEEP_WATER_SOUTHEAST3 = (2, "curve_in", 45)
	DEEP_WATER_NORTHEAST1 = (2, "curve_out", 225)
	DEEP_WATER_SOUTHEAST1 = (2, "curve_out", 135)
	DEEP_WATER_SOUTHWEST1 = (2, "curve_out", 45)
	DEEP_WATER_NORTHWEST1 = (2, "curve_out", 315)


class ACTION_SETS:
	DEFAULT_ANIMATION_LENGTH = 500
	DEFAULT_WEIGHT = 10


class GAME_SPEED:
	TICKS_PER_SECOND = 16
	TICK_RATES = [] # type: List[int]


GAME_SPEED.TICK_RATES = [int(i * GAME_SPEED.TICKS_PER_SECOND) for i in (0.5, 1, 2, 3, 4, 6, 8, 11, 20)]


class COLORS:
	BLACK = 9


class VIEW:
	ZOOM_MAX = 1.5
	ZOOM_MIN = 0.25
	ZOOM_DEFAULT = 1
	ZOOM_LEVELS_FACTOR = 0.875
	CELL_IMAGE_DIMENSIONS = (64, 32)
	ROTATION = 45.0
	TILT = -60
	AUTOSCROLL_WIDTH = 10


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
	# will get added later
	FISHING_BOAT = None # type: ignore
	FRIGATE = 58
	TREES = 256812226
	WOOL = 1654557398
	SWORDSMAN = 1062345232


## GAME-RELATED, BALANCING VALUES
class GAME:
	# seconds: duration of a "month" (running costs and taxes are paid in this interval)
	INGAME_TICK_INTERVAL = 30

	WORLD_WORLDID = 0 # worldid of World object
	# exit after on tick MAX_TICKS (disabled by setting to None)
	MAX_TICKS = None # type: Optional[int]


# Map related constants
class MAP:
	PADDING = 10 # extra usable water around the map edges
	BORDER = 30 # extra unusable water around the padding (to keep the black void at bay)


class GUI:
	CITYINFO_UPDATE_DELAY = 2 # seconds
	DEFAULT_EXCHANGE_AMOUNT = 50  # tons


# Editor
class EDITOR:
	MIN_BRUSH_SIZE = 1
	MAX_BRUSH_SIZE = 3
	DEFAULT_BRUSH_SIZE = 1


# Messagewidget and Logbook
class MESSAGES:
	CUSTOM_MSG_SHOW_DELAY = 6 # delay between messages when passing more than one
	CUSTOM_MSG_VISIBLE_FOR = 90 # after this time the msg gets removed from screen
	LOGBOOK_DEFAULT_DELAY = 1 # delay between condition fulfilled and logbook popping up


# AI values read from the command line; use the values below unless overridden by the CLI or the GUI
class AI:
	HIGHLIGHT_PLANS = False # whether to show the AI players' plans on the map
	HIGHLIGHT_COMBAT = False # whether to show the AI players' combat ranges around each unit
	HUMAN_AI = False # whether the human player is controlled by the AI


class TRADER: # check resource values: ./development/print_db_data.py res
	TILES_PER_TRADER = 100 # create one ship per 100 tiles
	SETTLEMENTS_PER_SHIP = 2 # the settlement : ship ratio
	PRICE_MODIFIER_BUY = 1.0  # buy for x times the resource value
	PRICE_MODIFIER_SELL = 1.0 # sell for x times the resource value
	TRADING_DURATION = 4 # seconds that trader stays at warehouse to simulate (un)loading

	BUSINESS_SENSE = 50 # chance in percent to be sent to a warehouse instead of random spot

	BUY_AMOUNT_MIN = 2  # amount range to buy/sell from settlement per resource
	BUY_AMOUNT_MAX = 10
	SELL_AMOUNT_MIN = 2
	SELL_AMOUNT_MAX = 10


# Taxes and Restrictions
class TIER:
	NATURE = 0
	SAILORS = 0
	PIONEERS = 1
	SETTLERS = 2
	CITIZENS = 3
	MERCHANTS = 4
	ARISTOCRATS = 5

	LOWEST = SAILORS
	HIGHEST = ARISTOCRATS
	CURRENT_MAX = MERCHANTS


class SETTLER:
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
	POPULATION_INIT_RATIO = 15 # every N-th tree gets an animal in the beginning


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

	# The maximum number of items you can set in a trade route slot or warehouse trade slot
	# This was actually only added to make sure the number wouldn't overflow the amount slider
	# If more items can be traded than pixels in the slider it is impossible to accurately select an amount
	# See https://github.com/unknown-horizons/unknown-horizons/issues/1095
	ITEMS_PER_TRADE_SLOT = 50


## ENGINE
class LAYERS:
	WATER = 0
	GROUND = 1
	FIELDS = 2 # ironically doesn't apply to fields anymore...
	OBJECTS = 3

	NUM = 4 # number of layers


class GFX:
	BUILDING_OUTLINE_THRESHOLD = 96
	BUILDING_OUTLINE_WIDTH = 2

	UNIT_OUTLINE_THRESHOLD = 96
	UNIT_OUTLINE_WIDTH = 2

	SHIP_OUTLINE_THRESHOLD = 96
	SHIP_OUTLINE_WIDTH = 2

	# this is modified by the game starting process.
	USE_ATLASES = False


## PATHS

_config_dir, _data_dir, _cache_dir = get_user_game_directories()


class PATHS:
	# paths in user directories
	USER_CONFIG_FILE = os.path.join(_config_dir, "settings.xml")
	USER_DATA_DIR = _data_dir
	LOG_DIR = os.path.join(USER_DATA_DIR, "log")
	USER_MAPS_DIR = os.path.join(USER_DATA_DIR, "maps")
	SCREENSHOT_DIR = os.path.join(USER_DATA_DIR, "screenshots")
	SAVEGAME_DIR = os.path.join(USER_DATA_DIR, "save")
	CACHE_DIR = _cache_dir
	ATLAS_METADATA_PATH = os.path.join(CACHE_DIR, "atlas-metadata.cache")

	# paths relative to uh dir
	DEFAULT_WINDOW_ICON_PATH = os.path.join("content", "gui", "images", "logos", "uh_32.png")
	MAC_WINDOW_ICON_PATH = os.path.join("content", "gui", "icons", "Icon.icns")

	ACTION_SETS_DIRECTORY = os.path.join("content", "gfx")
	TILE_SETS_DIRECTORY = os.path.join("content", "gfx", "base")
	SAVEGAME_TEMPLATE = os.path.join("content", "savegame_template.sql")

	ATLAS_FILES_DIR = os.path.join("content", "gfx", "atlas")
	ATLAS_DB_PATH = os.path.join("content", "atlas.sql")
	ACTION_SETS_JSON_FILE = os.path.join("content", "actionsets.json")
	TILE_SETS_JSON_FILE = os.path.join("content", "tilesets.json")

	SETTINGS_TEMPLATE_FILE = os.path.join("content", "settings-template.xml")
	CONFIG_TEMPLATE_FILE = os.path.join("content", "settings-template.xml")

	DB_FILES = tuple(os.path.join("content", i) for i in
	                 ("game.sql", "balance.sql", "names.sql"))

	ATLAS_SOURCE_DIRECTORIES = tuple(os.path.join("content", "gfx", d)
	                                 for d in (
	                                 "base",
	                                 "buildings",
	                                 "misc",
	                                 "terrain",
	                                 "units",
	                                ))

	#voice paths
	VOICE_DIR = os.path.join("content", "audio", "voice")
	UH_LOGO_FILE = os.path.join("content", "gfx", "uh.png")


_old_user_dir = get_old_user_game_directory()


class OLDPATHS:
	USER_DATA_DIR = _old_user_dir
	USER_CONFIG_FILE = os.path.join(_old_user_dir, "settings.xml")
	CACHE_DIR = _old_user_dir


class SETTINGS:
	UH_MODULE = "unknownhorizons"
	FIFE_MODULE = "FIFE"
	KEY_MODULE = "keys"
	META_MODULE = "meta"


class PLAYER:
	STATS_UPDATE_FREQUENCY = GAME_SPEED.TICKS_PER_SECOND


## SINGLEPLAYER
class SINGLEPLAYER:
	FREEZE_PROTECTION = True
	SEED = None # type: int


## MULTIPLAYER
class MULTIPLAYER:
	MAX_PLAYER_COUNT = 8


class NETWORK:
	SERVER_ADDRESS = "207.180.251.79"
	# change port to 2022 for development server updated after UH commits
	SERVER_PORT = 2002
	CLIENT_ADDRESS = None # type: Optional[str]
	UPDATE_FILE_URL = "http://unknown-horizons.org/current-version.json"


## TRANSLATIONS
class _LanguageNameDict(dict):
	def __getitem__(self, key):
		return self.get(key, [key])[0]

	def get_english(self, key):
		return self.get(key, [key])[1]

	def get_by_value(self, value, english=False):
		for code, (own, eng) in self.items():
			if english and eng == value:
				return code
			elif not english and own == value:
				return code
		return "" # meaning default key


LANGUAGENAMES = _LanguageNameDict({
	""      : ('System default', ''),
	"af"    : ('Afrikaans', 'Afrikaans'),
	"ar"    : ('اَللُّغَةُ اَلْعَرَبِيَّة', 'Arabic'),
	"bg"    : ('Български', 'Bulgarian'),
	"ca"    : ('Català', 'Catalan'),
	'ca@valencia' : ('Català de València', 'Catalan (Valencia)'),
	"cs"    : ('Čeština', 'Czech'),
	"da"    : ('Danske', 'Danish'),
	"de"    : ('Deutsch', 'German'),
	"en"    : ('English', 'English'),
	"eo"    : ('Esperanto', 'Esperanto'),
	"es"    : ('Español', 'Spanish'),
	"et"    : ('Eesti', 'Estonian'),
	"el"    : ('Ελληνικά', 'Greek'),
	"fi"    : ('Suomi', 'Finnish'),
	"fr"    : ('Français', 'French'),
	"frp"   : ('Francoprovençâl', 'Franco-Provencal'),
	"ga"    : ('Gaeilge', 'Irish'),
	"gl"    : ('Galego', 'Galician'),
	"hi"    : ('मानक हिन्दी', 'Hindi'),
	"hr"    : ('Hrvatski', 'Croatian'),
	"hu"    : ('Magyar', 'Hungarian'),
	"id"    : ('Bahasa Indonesia', 'Indonesian'),
	"it"    : ('Italiano', 'Italian'),
	"ja"    : ('日本語', 'Japanese'),
	"ko"    : ('한국말/조선말', 'Korean'),
	"lt"    : ('Lietuvių', 'Lithuanian'),
	"lv"    : ('Latviešu', 'Latvian'),
	"ml"    : ('മലയാളം', 'Malayalam'),
	"nb"    : ('Bokmål', 'Norwegian'),
	"nl"    : ('Nederlands', 'Dutch'),
	"pl"    : ('Polski', 'Polish'),
	"pt_BR" : ('Português Br.', 'Brazilian Portuguese'),
	"pt"    : ('Português', 'Portuguese'),
	"ro"    : ('Română', 'Romanian'),
	"ru"    : ('Русский', 'Russian'),
	"sk"    : ('Slovenský', 'Slovak'),
	"sl"    : ('Slovenski', 'Slovenian'),
	"sr"    : ('Cрпски', 'Serbian'),
	"sv"    : ('Svenska', 'Swedish'),
	"th"    : ('ภาษาไทย', 'Thai'),
	"tr"    : ('Türkçe', 'Turkish'),
	"uk"    : ('Українська', 'Ukrainian'),
	"vi"    : ('Tiếng Việt', 'Vietnamese'),
	"zh_CN" : ('简化字', 'Simplified Chinese'),
	"zh_Hant" : ('繁體字', 'Traditional Chinese'),
	"zh_TW" : ('繁體字', 'Traditional Chinese'),
	"zu"    : ('IsiZulu', 'Zulu'),
})

FONTDEFS = {
	# "af"
	# "ar"
	"bg"    : 'libertine',
	# "ca"
	"ca@valencia" : 'libertine',
	"cs"    : 'libertine',
	"da"    : 'libertine',
	"de"    : 'libertine',
	"en"    : 'libertine',
	"es"    : 'libertine',
	"et"    : 'libertine',
	"el"    : 'libertine',
	"fi"    : 'libertine',
	"fr"    : 'libertine',
	# "frp"
	"ga"    : 'libertine',
	"gl"    : 'libertine',
	# "hi"
	"hr"    : 'libertine',
	"hu"    : 'libertine',
	"id"    : 'libertine',
	"it"    : 'libertine',
	# "ja"
	# "ko"
	"lt"    : 'libertine',
	"lv"    : 'libertine',
	# "ml"
	"nb"    : 'libertine',
	"nl"    : 'libertine',
	"pl"    : 'libertine',
	"pt_BR" : 'libertine',
	"pt"    : 'libertine',
	"ro"    : 'libertine',
	"ru"    : 'libertine',
	"sk"    : 'libertine',
	"sl"    : 'libertine',
	"sr"    : 'libertine',
	"sv"    : 'libertine',
	# "th"
	"tr"    : 'libertine',
	"uk"    : 'libertine',
	# "vi"
	# "zh_CN"
	# "zh_TW"
	"zu"    : 'libertine',
}


class HOTKEYS:
	DISPLAY_KEY = {
		'MINUS': '-',
		'PLUS': '+',
		'COMMA': ',',
		'PERIOD': '.',
		'EXCLAIM': '!',
		'AT': '@',
		'HASH': '#',
		'DOLLAR': '$',
	# XXX Fife does not recognize percent key?
	#	'PERCENT': '%',
		'CARET': '^',
		'AMPERSAND': '&',
		'ASTERISK': '*',
		'LEFTPAREN': '(',
		'RIGHTPAREN': ')',
		'UNDERSCORE': '_',
		'LEFTBRACKET': '[',
		'RIGHTBRACKET': ']',
		'SLASH': '/',
		'COLON': ':',
		'SEMICOLON': ';',
		'LESS': '<',
		'EQUALS': '=',
		'GREATER': '>',
		'QUESTION': '?',
		'BACKSLASH': '\\',
		'BACKQUOTE': '`',
		'QUOTE': "'",
		'QUOTEDBL': '"',
		'ESCAPE': 'Esc',
		'DELETE': 'Del',
		'INSERT': 'Ins',
		'PAGE_UP': 'PgUp',
		'PAGE_DOWN': 'PgDn',
		'PRINT_SCREEN': 'PrtSc',
	}
