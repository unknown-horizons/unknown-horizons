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
import shutil
import tempfile
from unittest import TestCase

from horizons.constants import PATHS
from horizons.savegamemanager import SavegameManager
from horizons.util import create_user_dirs


class TestPaths(TestCase):
	odd_characters = "u\xfc\xdf\xfau"

	def test_normal(self):

		create_user_dirs()

	def test_special_character(self):
		"""Make paths have special characters and check some basic operations"""

		outer = tempfile.mkdtemp( self.__class__.odd_characters )
		inner = str(os.path.join(outer, self.__class__.odd_characters))
		inner2 = str(os.path.join(outer, self.__class__.odd_characters + "2"))

		PATHS.USER_DIR = inner

		create_user_dirs()

		scenario_file = os.listdir(SavegameManager.scenarios_dir)[0]
		shutil.copy(os.path.join(SavegameManager.scenarios_dir, scenario_file),
		            inner)

		SavegameManager.scenarios_dir = inner
		SavegameManager.autosave_dir = inner2
		SavegameManager.init()

		# try to read scenario files
		SavegameManager.get_available_scenarios()

		os.remove(os.path.join(inner, scenario_file))

		SavegameManager.create_autosave_filename()

		os.rmdir(inner)
		os.rmdir(inner2)
		os.rmdir(outer)
