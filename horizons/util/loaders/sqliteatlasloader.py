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

from typing import Any, List

from fife import fife

import horizons.globals
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.loaders.tilesetloader import TileSetLoader


class SQLiteAtlasLoader:
	"""Loads atlases and appropriate action sets from a JSON file and a SQLite database.
	"""
	def __init__(self):
		self.atlaslib = [] # type: List[Any]

		# TODO: There's something wrong with ground entities if atlas.sql
		# is loaded only here, for now it's added to DB_FILES (empty file if no atlases are used)

		#f = open('content/atlas.sql', "r")
		#sql = "BEGIN TRANSACTION;" + f.read() + "COMMIT;"
		#horizons.globals.db.execute_script(sql)

		self.atlases = horizons.globals.db("SELECT atlas_path FROM atlas ORDER BY atlas_id ASC")
		self.inited = False

	def init(self):
		"""Used to lazy init the loader"""
		for (atlas,) in self.atlases:
			# print 'creating', atlas
			# cast explicit to str because the imagemanager is not able to handle unicode strings
			img = horizons.globals.fife.imagemanager.create(str(atlas))
			self.atlaslib.append(img)
		self.inited = True

	def loadResource(self, anim_id):
		"""
		@param anim_id: String identifier for the image, eg "as_hunter0+idle+135"
		"""

		if not self.inited:
			self.init()
		actionset, action, rotation = anim_id.split('+')

		animationmanager = horizons.globals.fife.animationmanager

		# if we've loaded that animation before, we can finish early
		if animationmanager.exists(anim_id):
			return animationmanager.getPtr(anim_id)

		ani = animationmanager.create(anim_id)

		# Set the correct loader based on the actionset
		loader = self._get_loader(actionset)

		frame_start, frame_end = 0.0, 0.0
		for file in sorted(loader.get_sets()[actionset][action][int(rotation)].keys()):
			entry = loader.get_sets()[actionset][action][int(rotation)][file]
			# we don't need to load images at this point to query for its parameters
			# such as width and height because we can get those from json file
			xpos, ypos, width, height = entry[2:]

			if horizons.globals.fife.imagemanager.exists(file):
				img = horizons.globals.fife.imagemanager.get(file)
			else:
				img = horizons.globals.fife.imagemanager.create(file)
				region = fife.Rect(xpos, ypos, width, height)
				img.useSharedImage(self.atlaslib[entry[1]], region)

			img.setYShift(int(img.getWidth() / 4 - img.getHeight() / 2))
			frame_end = entry[0]
			ani.addFrame(img, max(1, int((frame_end - frame_start) * 1000)))
			frame_start = frame_end
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

	def load_image(self, file, actionset, action, rotation):
		if not self.inited:
			self.init()
		loader = self._get_loader(actionset)
		entry = loader.get_sets()[actionset][action][int(rotation)][file]
		# we don't need to load images at this point to query for its parameters
		# such as width and height because we can get those from json file
		xpos, ypos, width, height = entry[2:]

		if horizons.globals.fife.imagemanager.exists(file):
			img = horizons.globals.fife.imagemanager.get(file)
		else:
			img = horizons.globals.fife.imagemanager.create(file)
			region = fife.Rect(xpos, ypos, width, height)
			img.useSharedImage(self.atlaslib[entry[1]], region)

		return img
