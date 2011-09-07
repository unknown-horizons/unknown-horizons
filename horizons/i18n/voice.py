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


import horizons.main
import os.path
import glob
from horizons.constants import PATHS
from random import randrange

"""
Internationalization for speech|voice files
"""
class Speech:
	"""Definition of category names, those names are the name of directory where speech should be"""
	NEW_SETTLEMENT = "new_settlement" 
	NEW_WORLD = "new_world"
	QUICKSAVE = None
	SCREENSHOT = None
	SETTLER_LEVEL_UP = None
	NEED_MORE_RES = None
	NO_MAIN_SQUARE_IN_RANGE = None
	SETTLERS_MOVED_OUT = None
	MINE_EMPTY = None
	DRAG_ROADS_HINT = None
	DIPLOMACY_STATUS_CHANGED = None

DEFAULT_LANG="en"
DEFAULT_VARIATION=0
DEFAULT_SPEAKER=0

def get_speech_file(category, variation_id=None, speaker_id=DEFAULT_SPEAKER):
	"""Get speech file path.
	@param speaker_id: speaker id
	@param category_id: category id, the same as sentence
	@param variation_id: variation id of sentence
	@params random if true variation is random if false we try to find by variation_id
	@return: Path to Speach file or None if not exist"""
	category_name = eval_category_name(category)
	if category_name == None: return None
	lang = horizons.main.fife.get_locale()
	path = prepare_path(lang, category_name, variation_id, speaker_id)
	if path == None:
		path = prepare_path(DEFAULT_LANG, category_name, DEFAULT_VARIATION, DEFAULT_SPEAKER)
	return path

def prepare_path(lang, category_name, var_id, spkr_id):
	dir_path = get_dir_path(lang, category_name, spkr_id)
	if not os.path.isdir(dir_path): return None
	file_path = get_file_path(dir_path, var_id)
	if (file_path != None) and os.path.isfile(file_path):
		return file_path

def get_file_path(dir_name, var_id):
	"""If var_id is None we get random variation from directory
	"""
	if var_id is not None:
		for infile in glob.glob( os.path.join(dir_name, str(var_id) + '.*') ):
			return infile
	variation_count = count_variations(dir_name)
	if variation_count > 0:
		rand = randrange(0,variation_count)
		filelist = glob.glob( os.path.join(dir_name, '*.*') )
		return filelist[rand]
	else:
		return None

def get_dir_path(lang, category_name, spkr_id):
	return os.path.join(PATHS.VOICE_DIR, lang, str(spkr_id), str(category_name))

def count_variations(dir_name):
  return len([file for file in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name,file))])

def eval_category_name(category):
	cat_name = None
	try:
		cat_name = getattr(Speech, category)
	except:
		print "Incorect name of speech category"
	return cat_name

