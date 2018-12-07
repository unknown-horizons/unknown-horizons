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


def create_user_dirs(migrate=True):
	"""Creates the userdir and subdirs. Includes from horizons."""
	from horizons.constants import PATHS
	from horizons.util.migratepaths import migrate_paths

	if migrate:
		migrate_paths()

	for directory in (PATHS.LOG_DIR, PATHS.USER_MAPS_DIR, PATHS.SCREENSHOT_DIR):
		if not os.path.isdir(directory):
			os.makedirs(directory)
