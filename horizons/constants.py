# -.- coding: utf-8 -.-
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

import ctypes
import platform
import os
import locale
import sys

from horizons.ext.enum import Enum

"""This file keeps track of the constants that are used in Unknown Horizons.
NOTE: Using magic constants in code is generally a bad style, so avoid where
possible and instead import the proper classes of this file.
"""

##Versioning
class VERSION:
	def _get_git_version():
		"""Function gets latest revision of the working copy.
		It only works in git repositories, and is actually a hack.
		"""
		try:
			from run_uh import find_uh_position

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
		#if there is no .git directory then check for gitversion.txt
		except ImportError:
			try:
				return unicode(open(os.path.join("content", "gitversion.txt")).read())
			except IOError:
				return u"<unknown>"

		return u"<unknown>"

	RELEASE_NAME    = "Unknown Horizons %s"
	RELEASE_VERSION = _get_git_version()
	# change for release:
	IS_DEV_VERSION = True
	#RELEASE_VERSION = u'2012.1'

	## +=1 this if you changed the savegame "api"
	SAVEGAMEREVISION = 60

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
	WILD_ANIMAL          = 1000013
	USABLE_FISHER_BOAT   = 1000016
	FRIGATE              = 1000020

	# players will be spawned with an instance of this
	PLAYER_SHIP          = HUKER_SHIP

	# collectors
	BUILDING_COLLECTOR          = 1000002
	ANIMAL_COLLECTOR            = 1000007
	STORAGE_COLLECTOR           = 1000008
	FIELD_COLLECTOR             = 1000009
	LUMBERJACK_COLLECTOR        = 1000010
	SETTLER_COLLECTOR           = 1000011
	HUNTER_COLLECTOR            = 1000014
	FARM_ANIMAL_COLLECTOR       = 1000015
	DISASTER_RECOVERY_COLLECTOR = 1000022

	DIFFERENCE_BUILDING_UNIT_ID = 1000000

class WEAPONS:
	CANNON = 40
	DAGGER = 41

	DEFAULT_FIGHTING_SHIP_WEAPONS_NUM = 7

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

	IRON_MINE        = 28
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

	VINTNER          = 65


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
	CANNON           = WEAPONS.CANNON
	DAGGER           = 41
	GRAIN            = 42
	CORN             = 43
	FLOUR            = 44
	SPICE_PLANTS     = 45
	SPICES           = 46
	CONDIMENTS       = 47
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
	FIRE             = 99

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

class GAME_SPEED:
	TICKS_PER_SECOND = 16
	TICK_RATES = [ int(i*16) for i in (0.5, 1, 2, 3, 4, 6, 8, 11, 20) ]

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
	TREES = 256812226
	WOOL = 1654557398


## GAME-RELATED, BALANCING VALUES
class GAME:
	INGAME_TICK_INTERVAL = 30 # seconds. duration of a "month" (running costs and taxes are
	# payed in this interval).

	WORLD_WORLDID = 0 # worldid of World object
	MAX_TICKS = None # exit after on tick MAX_TICKS (disabled by setting to None)

class GUI:
	CITYINFO_UPDATE_DELAY = 2 # seconds

# Messagewidget and Logbook
class MESSAGES:
	CUSTOM_MSG_SHOW_DELAY = 6 # delay between messages when passing more than one
	CUSTOM_MSG_VISIBLE_FOR = 90 # after this time the msg gets removed from screen
	LOGBOOK_DEFAULT_DELAY = 4 # delay between condition fulfilled and logbook popping up

# AI values read from the command line; use the values below unless overridden by the CLI or the GUI
class AI:
	HIGHLIGHT_PLANS = False # whether to show the AI players' plans on the map
	HUMAN_AI = False # whether the human player is controlled by the AI

class TRADER: # check resource values: ./development/print_db_data.py res
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
	CURRENT_MAX = 3 # counting starts at 0!

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

if 'UH_USER_DIR' in os.environ:
	# Prefer the value from the environment. Used to override user dir when
	# running GUI tests.
	_user_dir = os.environ['UH_USER_DIR']
elif platform.system() != "Windows":
	_user_dir = os.path.join(os.path.expanduser('~'), '.unknown-horizons')
else:
	dll = ctypes.windll.shell32
	buf = ctypes.create_string_buffer(300)
	dll.SHGetSpecialFolderPathA(None, buf, 0x0005, False) # get the My Documents folder
	my_games = os.path.join(buf.value, 'My Games')
	if not os.path.exists(my_games):
		os.makedirs(my_games)
	_user_dir = os.path.join(my_games, 'unknown-horizons')
try:
	_user_dir = unicode(_user_dir, locale.getpreferredencoding()) # this makes umlaut-paths work on win
except Exception as inst:
	_user_dir = unicode(_user_dir, sys.getfilesystemencoding()) # locale.getpreferredencoding() does not work @ mac



class GFX:
	BUILDING_OUTLINE_THRESHOLD = 96
	BUILDING_OUTLINE_WIDTH = 2

	UNIT_OUTLINE_THRESHOLD = 96
	UNIT_OUTLINE_WIDTH = 2

	SHIP_OUTLINE_THRESHOLD = 96
	SHIP_OUTLINE_WIDTH = 2

	USE_ATLASES = False

class PATHS:
	# paths in user dir
	USER_DIR = _user_dir
	LOG_DIR = os.path.join(_user_dir, "log")
	USER_CONFIG_FILE = os.path.join(_user_dir, "settings.xml")
	SCREENSHOT_DIR = os.path.join(_user_dir, "screenshots")

	# paths relative to uh dir
	ACTION_SETS_DIRECTORY = os.path.join("content", "gfx")
	TILE_SETS_DIRECTORY = os.path.join("content", "gfx", "base")
	SAVEGAME_TEMPLATE = os.path.join("content", "savegame_template.sql")
	ISLAND_TEMPLATE = os.path.join("content", "island_template.sql")
	ACTION_SETS_JSON_FILE = os.path.join("content", "actionsets.json")
	TILE_SETS_JSON_FILE = os.path.join("content", "tilesets.json")

	CONFIG_TEMPLATE_FILE = os.path.join("content", "settings-template.xml")

	DB_FILES = tuple(os.path.join("content", i) for i in \
	                 ("game.sql", "balance.sql"))

	if GFX.USE_ATLASES:
		DB_FILES = DB_FILES + (os.path.join("content", "atlas.sql"), )

	#voice paths
	VOICE_DIR = os.path.join("content", "audio", "voice")

class PLAYER:
	STATS_UPDATE_FREQUENCY = GAME_SPEED.TICKS_PER_SECOND

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
	UPDATE_FILE_URL = "http://updates.unknown-horizons.org/current_version.php"

## TRANSLATIONS
class _LanguageNameDict(dict):
	def __getitem__(self, key):
		return self.get(key, key)

	def get_by_value(self, value):
		for item in self.iteritems():
			if item[1] == value:
				return item[0]
		return "" # meaning default key


LANGUAGENAMES = _LanguageNameDict({
"" 			: u'System default',
"af"    : u'Afrikaans',
"bg"    : u'Български',
"ca"    : u'Català',
'ca@valencia' : u'Català de València',
"cs"    : u'Čeština',
"da"    : u'Danske',
"de"    : u'Deutsch',
"en"    : u'English',
"es"    : u'Español',
"et"    : u'Eesti',
"el"    : u'Ελληνικά',
"fi"    : u'Suomi',
"fr"    : u'Français',
"gl"    : u'Galego',
"hi"    : u'मानक हिन्दी',
"hr"    : u'Hrvatski',
"hu"    : u'Magyar',
"it"    : u'Italiano',
"ja"    : u'日本語',
"lt"    : u'Lietuvių',
"ko"    : u'한국말/조선말',
"nb"    : u'Norw. Bokmål',
"nl"    : u'Nederlands',
"pl"    : u'Polski',
"pt_BR" : u'Português Br.',
"pt"    : u'Português',
"ro"    : u'Română',
"ru"    : u'Русский',
"sl"    : u'Slovenski',
"sv"    : u'Svenska',
"tr"    : u'Türkçe',
"vi"    : u'Tiếng Việt',
"zh_CN" : u'普通話',
})

FONTDEFS = {
	# "af"
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
	"gl"    : 'libertine',
	# "hi"
	"hr"    : 'libertine',
	"hu"    : 'libertine',
	"it"    : 'libertine',
	# "ja"
	"lt"    : 'libertine',
	# "ko"
	"nb"    : 'libertine',
	"nl"    : 'libertine',
	"pl"    : 'libertine',
	"pt_BR" : 'libertine',
	"pt"    : 'libertine',
	"ro"    : 'libertine',
	"ru"    : 'libertine',
	"sl"    : 'libertine',
	"sv"    : 'libertine',
	"tr"    : 'libertine',
	# "vi"
	# "zh_CN"
}

AUTO_CONTINUE_CAMPAIGN=True
