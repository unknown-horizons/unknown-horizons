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

import horizons.globals
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.loaders.tilesetloader import TileSetLoader


class SQLiteAnimationLoader:
	"""Loads animations from a SQLite database.
	"""
	def __init__(self):
		pass

	def loadResource(self, anim_id):
		"""
		@param anim_id: String identifier for the image, eg "as_hunter0+idle+135"
		"""

		actionset, action, rotation = anim_id.split('+')

		animationmanager = horizons.globals.fife.animationmanager

		# if we've loaded that animation before, we can finish early
		if animationmanager.exists(anim_id):
			return animationmanager.getPtr(anim_id)

		# Set the correct loader based on the actionset
		loader = self._get_loader(actionset)

		ani = animationmanager.create(anim_id)
		frame_start, frame_end = 0.0, 0.0
		for f in sorted(loader.get_sets()[actionset][action][int(rotation)].keys()):
			frame_end = loader.get_sets()[actionset][action][int(rotation)][f]
			img = horizons.globals.fife.imagemanager.load(f)
			img.setYShift(int(img.getWidth() / 4 - img.getHeight() / 2))
			ani.addFrame(img, max(1, int((float(frame_end) - frame_start) * 1000)))
			frame_start = float(frame_end)
		# currently unused. would trigger onInstanceActionFrame of
		# fife.InstanceActionListener instance
		ani.setActionFrame(-1)
		return ani

	def _get_loader(self, actionset):
			if actionset.startswith("ts_"):
				loader = TileSetLoader
			elif actionset.startswith("as_"):
				loader = ActionSetLoader
			else:
				assert False, "Invalid set being loaded: " + actionset
			return loader

	def load_image(self, f, actionset, action, rotation):
		loader = self._get_loader(actionset)
		entry = loader.get_sets()[actionset][action][int(rotation)][f]

		if horizons.globals.fife.imagemanager.exists(f):
			img = horizons.globals.fife.imagemanager.get(f)
		else:
			img = horizons.globals.fife.imagemanager.create(f)
			img.forceLoadInternal() # make sure width and height can be read
		return img
