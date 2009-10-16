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

import os.path

from ext.enum import Enum

"""This file keeps track of some constants, that have to be used in the code.
NOTE: Using constants is generally a bad style, so avoid where possible."""

##Versioning
class VERSION:
	def _set_version(version=None):
		"""Function gets latest revision of the working copy to display in background.
		@param version: String to display instead of revision."""
		from run_uh import find_uh_position
		if version == None:
			rev = None
			uh_path = find_uh_position()
			if os.path.exists(uh_path + '/.svn/entries'):
				import re
				entries_file = open(uh_path + '/.svn/entries', 'r').read()
				if re.match('\d', entries_file):
					rev = re.search('\d+\s+dir\s+(\d+)', entries_file).groups()[0]
				else:
					from xml.dom import minidom
					rev = minidom.parse(entries_file).getElementsByTagName("entry")[0].getAttribute("revision")
				rev = u"r" + rev
				return unicode(rev)
			elif os.path.exists(uh_path + '/.git/logs/refs/remotes/git-svn'):
				import re
				log_file = open(uh_path + '/.git/logs/refs/remotes/git-svn', 'r').read()
				rev  = re.search('\s+r+(\d+)$', log_file).groups()[0]
				rev = u"r" + rev
				return unicode(rev)
			else:
				return u""
		else:
			return unicode(version)

	#RELEASE_NAME   = _("Unknwon Horizons Alpha %s")
	RELEASE_NAME    = _("Unknown Horizons Snapshot %s")
	RELEASE_VERSION = _set_version()

	@staticmethod
	def string():
		return VERSION.RELEASE_NAME % VERSION.RELEASE_VERSION

## WORLD
class UNITS:
	PLAYER_SHIP_CLASS          = 1000001
	BUILDING_COLLECTOR_CLASS   = 1000002
	TRADER_SHIP_CLASS          = 1000006
	WILD_ANIMAL_CLASS          = 1000013

class BUILDINGS:
	BRANCH_OFFICE_CLASS = 1
	MARKET_PLACE_CLASS = 4
	SETTLER_RUIN_CLASS = 10
	TREE_CLASS = 17
	SIGNAL_FIRE_CLASS = 6

class RES:
	GOLD_ID   = 1
	HAPPINESS_ID = 14

class GROUND:
	WATER = 4
	DEFAULT_LAND = 1

## ENGINE
class LAYERS:
	WATER = 0
	GROUND = 1
	OBJECTS = 2

## PATHS
# workaround, so it can be used to create paths withing PATHS
_user_dir = "%s/.unknown-horizons" % os.path.expanduser('~')
class PATHS:
	USER_DIR = _user_dir
	LOG_DIR = _user_dir + "/log"
	USER_CONFIG_FILE = _user_dir + "/config.sqlite"
	ACTION_SETS_DIRECTORY = 'content/gfx/'
	SCREENSHOT_DIR = _user_dir + "/screenshots"
	SAVEGAME_TEMPLATE = "content/savegame_template.sqlite"

## The Production States available in the game sorted by importance from least
## to most important
class PRODUCTION:
	STATES = Enum('none', 'waiting_for_res', 'inventory_full', 'producing', 'paused', 'done')
	# NOTE: 'done' is only for SingleUseProductions
	# NOTE: 'none' is not used by an acctual production, just for a producer
	CAPACITY_UTILISATION_CONSIDERED_SECONDS = 60 # seconds, that count for cap. util. calculation


## GAME-RELATED, BALANCING VALUES
class GAME:
	INGAME_TICK_INTERVAL = 30 # seconds. duration of a "month" (running costs and taxes are
														# payed in this interval).

class SETTLER:
	TAX_SETTINGS = Enum(u'medium', u'high')
	TAX_SETTINGS_VALUES = [1.0, 1.5]

class WILD_ANIMAL:
	HEALTH_INIT_VALUE = 50 # animals start with this value
	HEALTH_INCREASE_ON_FEEDING = 4 # health increases by this value on feeding
	HEALTH_DECREASE_ON_NO_JOB = 2 # health decreases by this value when they have no food
	HEALTH_LEVEL_TO_REPRODUCE = 70 # this level has to be reached for reproducing

