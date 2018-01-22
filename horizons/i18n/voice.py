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

import glob
import os.path
from random import randrange
from typing import Optional

import horizons.globals
from horizons.constants import PATHS


"""
Internationalization for speech|voice files
"""


class Speech:
	"""Definition of category names, those names are the name of directory where speech should be"""
	CHAT = None # type: Optional[str]
	NEW_SETTLEMENT = "new_settlement"
	NEW_WORLD = "new_world"
	SAVED_GAME = None # type: Optional[str]
	QUICKSAVE = None # type: Optional[str]
	AUTOSAVE = None # type: Optional[str]
	SCREENSHOT = None # type: Optional[str]
	SETTLER_LEVEL_UP = None # type: Optional[str]
	NEED_MORE_RES = None # type: Optional[str]
	NO_MAIN_SQUARE_IN_RANGE = None # type: Optional[str]
	SETTLERS_MOVED_OUT = None # type: Optional[str]
	MINE_EMPTY = None # type: Optional[str]
	DRAG_ROADS_HINT = None # type: Optional[str]
	DIPLOMACY_STATUS_ALLY_NEUTRAL = None # type: Optional[str]
	DIPLOMACY_STATUS_ALLY_ENEMY = None # type: Optional[str]
	DIPLOMACY_STATUS_ENEMY_ALLY = None # type: Optional[str]
	DIPLOMACY_STATUS_ENEMY_NEUTRAL = None # type: Optional[str]
	DIPLOMACY_STATUS_NEUTRAL_ALLY = None # type: Optional[str]
	DIPLOMACY_STATUS_NEUTRAL_ENEMY = None # type: Optional[str]
	MAX_TIER_REACHED = None # type: Optional[str]
	YOU_HAVE_WON = None # type: Optional[str]
	FIELD_NEEDS_FARM = None # type: Optional[str]
	WAREHOUSE_NOT_TEARABLE = None # type: Optional[str]
	ROUTE_DISABLED = None # type: Optional[str]
	MOVE_OUTSIDE_OF_WORLD = None # type: Optional[str]
	MOVE_INVALID_LOCATION = None # type: Optional[str]
	NEW_SHIP = None # type: Optional[str]
	NEW_SOLDIER = None # type: Optional[str]
	NEW_INHABITANT = None # type: Optional[str]
	YOU_LOST = None # type: Optional[str]
	BUILDING_ON_FIRE = None # type: Optional[str]
	BUILDING_INFECTED_BY_BLACK_DEATH = None # type: Optional[str]


DEFAULT_LANG = "en"
DEFAULT_VARIATION = 0
DEFAULT_SPEAKER = 0


def get_speech_file(category, variation_id=None, speaker_id=DEFAULT_SPEAKER):
	#TODO expand this docstring
	"""Get speech file path.
	@param category: category id, the same as sentence
	@param variation_id: variation id of sentence
	@param speaker_id: speaker id
	@return: path to speech file or None if not exist"""
	category_name = eval_category_name(category)
	if category_name is None:
		return None
	lang = horizons.globals.fife.get_locale()
	path = prepare_path(lang, category_name, variation_id, speaker_id)
	if path is None:
		path = prepare_path(DEFAULT_LANG, category_name, DEFAULT_VARIATION, DEFAULT_SPEAKER)
	return path


def prepare_path(lang, category_name, var_id, spkr_id):
	dir_path = get_dir_path(lang, category_name, spkr_id)
	if not os.path.isdir(dir_path):
		return None
	file_path = get_file_path(dir_path, var_id)
	if file_path is not None and os.path.isfile(file_path):
		return file_path


def get_file_path(dir_name, var_id):
	"""If var_id is None we get random variation from directory
	"""
	if var_id is not None:
		for infile in glob.glob(os.path.join(dir_name, str(var_id) + '.*')):
			return infile
	variation_count = count_variations(dir_name)
	if variation_count > 0:
		rand = randrange(0, variation_count)
		filelist = glob.glob(os.path.join(dir_name, '*.*'))
		return filelist[rand]
	else:
		return None


def get_dir_path(lang, category_name, spkr_id):
	return os.path.join(PATHS.VOICE_DIR, lang, str(spkr_id), str(category_name))


def count_variations(dir_name):
	return len([file for file in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, file))])


def eval_category_name(category):
	cat_name = None
	try:
		cat_name = getattr(Speech, category)
	except:
		print("Incorrect name of speech category: {}".format(category))
		print("You might want to add this here in voice.py.")
	return cat_name
