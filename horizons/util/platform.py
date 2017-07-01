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
from pathlib import PurePath

CSIDL_PERSONAL = 5 # 'My documents' folder for win32 API


def get_home_directory():
	"""
	Returns the home directory of the user running UH.
	"""
	if platform.system() != "Windows":
		return PurePath(os.path.expanduser('~'))
	else:
		import ctypes.wintypes
		buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
		# get the My Documents folder into buf.value
		ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, 0, buf)
		return PurePath(buf.value)


def get_user_game_directory():
	"""
	Returns the directory where we store game-related data, such as savegames.
	"""
	home_directory = get_home_directory()
	if platform.system() != "Windows":
		return home_directory.joinpath('.unknown-horizons')
	else:
		return home_directory.joinpath('My Games', 'unknown-horizons')
