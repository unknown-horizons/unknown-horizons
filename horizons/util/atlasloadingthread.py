# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
import subprocess
import sys
import threading

import horizons.globals
from horizons.constants import GFX, PATHS


class AtlasLoadingThread(threading.Thread):
	"""Class used to preload and generate the atlas files if necessary"""

	def __init__(self, lock):
		threading.Thread.__init__(self)
		self.lock = lock

	def run(self):
		self.lock.acquire()
		horizons_path = os.path.dirname(horizons.__file__)
		args = [sys.executable, os.path.join(horizons_path, 'engine', 'generate_atlases.py'),
		        str(horizons.globals.fife.get_uh_setting('MaxAtlasSize'))]
		atlas_generator = subprocess.Popen(args, stdout=None, stderr=subprocess.STDOUT)
		atlas_generator.wait()
		assert atlas_generator.returncode is not None
		if atlas_generator.returncode != 0:
			print('Atlas generation failed. Continuing without atlas support.')
			print('This just means that the game will run a bit slower.')
			print('It will still run fine unless there are other problems.')
			print()
			GFX.USE_ATLASES = False
		else:
			GFX.USE_ATLASES = True
			PATHS.DB_FILES = PATHS.DB_FILES + (PATHS.ATLAS_DB_PATH, )
		self.lock.release()
