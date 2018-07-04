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
import os.path
import re

from horizons.extscheduler import ExtScheduler


class PychanAnimation:
	"""Displays images in short succession in a pychan icon."""

	def __init__(self, icon, directory):
		self.icon = icon
		files = [os.path.join(directory, filename)
		         for filename in os.listdir(directory)
		         if filename.endswith('.png')]

		def find_int(f):
			return int(re.search(r'\d+', os.path.basename(f)).group())
		self.files = sorted(files, key=find_int)
		self.cur = -1

	def start(self, interval, loops):
		"""Starts the animation.
		@param interval: seconds
		@param loops: number of loops or -1 for infininte
		"""
		self.interval = interval
		self._next()
		ExtScheduler().add_new_object(self._next, self, run_in=interval, loops=loops)

	def stop(self):
		"""Stops the animation (leaves current image)"""
		ExtScheduler().rem_call(self, self._next)

	def _next(self):
		self.cur = (self.cur + 1) % len(self.files)
		# don't set hover image, on mouseover, something has to happen
		# so that the user knows this is a button and now an image
		for img in ('image', 'up_image', 'down_image'):
			if hasattr(self.icon, img):
				setattr(self.icon, img, self.files[self.cur])
