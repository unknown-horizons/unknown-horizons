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

import logging
import threading

from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.loaders.tilesetloader import TileSetLoader
from horizons.util.python.callback import Callback

log = logging.getLogger("preload")


class PreloadingThread(threading.Thread):
	"""
	Preloads game data while in the main menu. Once a game is started, `wait_for_finish` is
	called to end the thread.
	"""
	def __init__(self):
		threading.Thread.__init__(self)
		self.lock = threading.Lock()

	def run(self):
		"""
		Preloads game data.

		Keeps releasing and acquiring lock, runs until lock can't be acquired.
		"""
		from horizons.entities import Entities

		try:
			# create own db reader instance, since it's not thread-safe
			from horizons.main import _create_main_db
			mydb = _create_main_db()

			preload_functions = [
				ActionSetLoader.load,
				TileSetLoader.load,
				Callback(Entities.load_grounds, mydb, load_now=True),
				Callback(Entities.load_buildings, mydb, load_now=True),
				Callback(Entities.load_units, load_now=True)
			]

			for f in preload_functions:
				if not self.lock.acquire(False):
					break
				log.debug("Preload: %s", f)
				f()
				log.debug("Preload: %s is done", f)
				self.lock.release()
			log.debug("Preloading done.")
		except Exception as e:
			log.warning("Exception occurred in preloading thread: %s", e)
		finally:
			if self.lock.locked():
				self.lock.release()

	def wait_for_finish(self):
		"""
		Wait for preloading to finish.
		"""
		self.lock.acquire()
		# wait until it finished its current action
		if self.is_alive():
			self.join()
			assert not self.is_alive()
		else:
			try:
				self.lock.release()
			except RuntimeError:
				# due to timing issues, the lock might be released already
				pass
