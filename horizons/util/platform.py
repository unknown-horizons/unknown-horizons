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

import os
import platform

CSIDL_PERSONAL = 5 # 'My documents' folder for win32 API


def get_home_directory():
	"""
	Returns the home directory of the user running UH.
	"""
	if platform.system() != "Windows":
		return os.path.expanduser('~')
	else:
		import ctypes.wintypes
		buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
		# get the My Documents folder into buf.value
		ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, 0, buf)
		return buf.value


# define here as string to reduce chance of typos
UH = "unknown-horizons"


def get_old_user_game_directory():
	"""
	Returns the old directory where for game-related data.
	This is used when migrating from the old structure to the new
	"""
	user_dir = os.environ.get("UH_USER_DIR")
	if user_dir: # not None or empty string
		return user_dir

	home_directory = get_home_directory()
	if platform.system() != "Windows":
		return os.path.join(home_directory, "." + UH)
	else:
		return os.path.join(home_directory, 'My Games', UH)


def _try_directories(paths, default=None):
	# takes a list of lists of strings as first argument
	# returns the joined path for the first list where all strings exist and are nonempty
	# or the second argument if there is no such list
	# (lists could also be tuples of course)
	for parts in paths:
		if all(parts):
			return os.path.join(*parts)
	return default


def get_user_game_directories():
	"""
	Returns a triplet of directories for game-related data.
	The first value is the directory for configuration files (settings.xml)
	The second is the directory for game data (saves, maps, screenshots, logs)
	The third is the directory for cache (atlas-metadata.cache, yamldata.cache)
	"""
	home_directory = get_home_directory()

	# these are the default directories
	if platform.system() == "Windows":
		user_dir = os.path.join(home_directory, 'My Games', UH)
		config_dir = user_dir
		data_dir = user_dir
		cache_dir = os.path.join(user_dir, "cache")
	else:
		config_dir = os.path.join(home_directory, ".config", UH)
		data_dir = os.path.join(home_directory, ".local", "share", UH)
		cache_dir = os.path.join(home_directory, ".cache", UH)

	# for each of the directories, try the paths with environment variables in this order
	# if one of the environment variables exists, use that path
	# otherwise, keep using the default dir

	config_dir = _try_directories([
		(os.environ.get("UH_USER_CONFIG_DIR"),),
		(os.environ.get("UH_USER_DIR"),),
		(os.environ.get("XDG_CONFIG_HOME"), UH)],
		config_dir)

	if not os.path.exists(config_dir):
		os.makedirs(config_dir)

	data_dir = _try_directories([
		(os.environ.get("UH_USER_DATA_DIR"),),
		(os.environ.get("UH_USER_DIR"),),
		(os.environ.get("XDG_DATA_HOME"), UH)],
		data_dir)

	if not os.path.exists(data_dir):
		os.makedirs(data_dir)

	cache_dir = _try_directories([
		(os.environ.get("UH_USER_CACHE_DIR"),),
		(os.environ.get("UH_USER_DIR"), "cache"),
		(os.environ.get("XDG_CACHE_HOME"), UH)],
		cache_dir)

	if not os.path.exists(cache_dir):
		os.makedirs(cache_dir)

	return config_dir, data_dir, cache_dir
