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

import os.path
import re
import locale

from ext.enum import Enum

"""This file keeps track of some constants, that have to be used in the code.
NOTE: Using constants is generally a bad style, so avoid where possible."""

##Versioning
class VERSION:
	def _set_version():
		"""Function gets latest revision of the working copy.
		It only works in git repositories, and is acctually a hack.
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

	RELEASE_NAME    = _("Unknown Horizons Version %s")
	RELEASE_VERSION = _set_version()

	# change to sth like this for release
	#RELEASE_NAME = _("Unknown Horizons Alpha %s")
	#RELEASE_VERSION = u'2011.2'

	## +=1 this if you changed the savegame "api"
	SAVEGAMEREVISION= 15

	@staticmethod
	def string():
		return VERSION.RELEASE_NAME % VERSION.RELEASE_VERSION

## WORLD
class UNITS:
	# ./development/print_db_data.py unit
	PLAYER_SHIP_CLASS          = 1000001
	BUILDING_COLLECTOR_CLASS   = 1000002
	PIRATE_SHIP_CLASS          = 1000005
	TRADER_SHIP_CLASS          = 1000006
	WILD_ANIMAL_CLASS          = 1000013

	DIFFERENCE_BUILDING_UNIT_ID = 1000000

class BUILDINGS:
	# ./development/print_db_data.py building
	BRANCH_OFFICE_CLASS = 1
	STORAGE_CLASS = 2
	RESIDENTIAL_CLASS = 3
	MARKET_PLACE_CLASS = 4
	SIGNAL_FIRE_CLASS = 6
	SETTLER_RUIN_CLASS = 10
	TRAIL_CLASS = 10
	TREE_CLASS = 17
	CLAY_DEPOSIT_CLASS = 23
	FISH_DEPOSIT_CLASS = 33
	MOUNTAIN_CLASS = 34

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
	GOLD_ID   = 1
	WILDANIMALFOOD_ID = 12
	HAPPINESS_ID = 14
	FISH_ID = 28

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
	TICK_RATES = [16, 32, 48, 64]

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
	# NOTE: 'none' is not used by an acctual production, just for a producer
	CAPACITY_UTILISATION_CONSIDERED_SECONDS = 60 # seconds, that count for cap. util. calculation


## GAME-RELATED, BALANCING VALUES
class GAME:
	INGAME_TICK_INTERVAL = 30 # seconds. duration of a "month" (running costs and taxes are
	# payed in this interval).

	WORLD_WORLDID = 0 # worldid of World object

# Messagewidget and Logbook
class MESSAGES:
	CUSTOM_MSG_SHOW_DELAY = 6 # delay between messages when passing more than one
	CUSTOM_MSG_VISIBLE_FOR = 90 # after this time the msg gets removed from screen
	LOGBOOK_DEFAULT_DELAY = 4 # delay between condition fulfilled and logbook popping up

# AI
class TRADER: # check resource values: ./development/print_db_data.py res
	PRICE_MODIFIER_BUY = 0.9  # buy for x times the resource value
	PRICE_MODIFIER_SELL = 1.5 # sell for x times the resource value
	TRADING_DURATION = 4 # seconds that trader stays at branch office to simulate (un)loading

	BUSINESS_SENSE = 50 # chance in percent to be sent to a branch office instead of random spot

	BUY_AMOUNT = (2, 8)  # amount range to buy/sell from settlement per resource
	SELL_AMOUNT = (2, 8) # => randomly picks an amount in this range for each trade

# Taxes and Restrictions
class SETTLER:
	CURRENT_MAX_INCR = 2 # counting starts at 0!
	TAX_SETTINGS_MIN = 0.5
	TAX_SETTINGS_MAX = 1.5
	TAX_SETTINGS_STEP = 0.1

class WILD_ANIMAL:
	HEALTH_INIT_VALUE = 50 # animals start with this value
	HEALTH_INCREASE_ON_FEEDING = 4 # health increases by this value on feeding
	HEALTH_DECREASE_ON_NO_JOB = 2 # health decreases by this value when they have no food
	HEALTH_LEVEL_TO_REPRODUCE = 70 # this level has to be reached for reproducing

class COLLECTORS:
	DEFAULT_WORK_DURATION = 16 # how many ticks collectors pretend to work at target
	DEFAULT_WAIT_TICKS = 32 # how long collectors wait before again looking for a job

class STORAGE:
	DEFAULT_STORAGE_SIZE = 30 # Our usual inventorys are 30 tons big

	# Distributing overall delimiter, if one slot is "full" with respect to
	# this value, you can't load further in any of the slots even if empty.
	SHIP_TOTAL_STORAGE = 120

## ENGINE
class LAYERS:
	WATER = 0
	GROUND = 1
	FIELDS = 2
	OBJECTS = 3

	NUM = 4 # number of layers

## PATHS
# workaround, so it can be used to create paths withing PATHS
_user_dir = os.path.join(os.path.expanduser('~'), '.unknown-horizons')
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

## MULTIPLAYER
class MULTIPLAYER:
	MAX_PLAYER_COUNT = 8

class NETWORK:
	SERVER_ADDRESS = "master.unknown-horizons.org"
	SERVER_PORT = 2001
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
	})

AUTO_CONTINUE_CAMPAIGN=True
