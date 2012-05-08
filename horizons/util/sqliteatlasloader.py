# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from fife import fife

import horizons.main

from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.loaders.tilesetloader import TileSetLoader

class SQLiteAtlasLoader(object):
	"""Loads atlases and appropriate action sets from a JSON file and a SQLite database.
	"""
	def __init__(self):
		self.atlaslib = []

		# TODO: There's something wrong with ground entities if atlas.sql
		# is loaded only here, for now it's added to DB_FILES (empty file if no atlases are used)

		#f = open('content/atlas.sql', "r")
		#sql = "BEGIN TRANSACTION;" + f.read() + "COMMIT;"
		#horizons.main.db.execute_script(sql)

		self.atlases = horizons.main.db("SELECT atlas_path FROM atlas ORDER BY atlas_id ASC")

		for (atlas,) in self.atlases:
			# print 'creating', atlas
			# cast explicit to str because the imagemanager is not able to handle unicode strings
			img = horizons.main.fife.imagemanager.create(str(atlas))
			self.atlaslib.append(img)


	def loadResource(self, location):
		"""
		@param location: String with the location. See below for details:
		Location format: <animation_id>:<command>:<params> (e.g.: "123:shift:left-16, bottom-8)
		Available commands:
		- shift:
		Shift the image using the params left, right, center, middle for x shifting and
		y-shifting with the params: top, bottom, center, middle.
		A param looks like this: "param_x(+/-)value, param_y(+/-)value" (e.g.: left-16, bottom+8)
		- cut:
		#TODO: complete documentation
		"""
		commands = location.split(':')
		id = commands.pop(0)
		actionset, action, rotation = id.split('+')
		commands = zip(commands[0::2], commands[1::2])

		ani = fife.Animation.createAnimation()

		# Set the correct loader based on the actionset
		loader = self._get_loader(actionset)


		frame_start, frame_end = 0.0, 0.0
		for file in sorted(loader.get_sets()[actionset][action][int(rotation)].iterkeys()):
			entry = loader.get_sets()[actionset][action][int(rotation)][file]
			# we don't need to load images at this point to query for its parameters
			# such as width and height because we can get those from json file
			xpos, ypos, width, height = entry[2:]

			if horizons.main.fife.imagemanager.exists(file):
				img = horizons.main.fife.imagemanager.get(file)
			else:
				img = horizons.main.fife.imagemanager.create(file)
				region = fife.Rect(xpos, ypos, width, height)
				img.useSharedImage(self.atlaslib[entry[1]], region)

			for command, arg in commands:
				if command == 'shift':
					x, y = arg.split(',')
					if x.startswith('left'):
						x = int(x[4:]) + int(width / 2)
					elif x.startswith('right'):
						x = int(x[5:]) - int(width / 2)
					elif x.startswith(('center', 'middle')):
						x = int(x[6:])
					else:
						x = int(x)

					if y.startswith('top'):
						y = int(y[3:]) + int(height / 2)
					elif y.startswith('bottom'):
						y = int(y[6:]) - int(height / 2)
					elif y.startswith(('center', 'middle')):
						y = int(y[6:])
					else:
						y = int(y)

					img.setXShift(x)
					img.setYShift(y)

			frame_end = entry[0]
			ani.addFrame(img, max(1, int((float(frame_end) - frame_start)*1000)))
			frame_start = float(frame_end)
		ani.setActionFrame(0)
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
		loader = self._get_loader(actionset)
		entry = loader.get_sets()[actionset][action][int(rotation)][file]
		# we don't need to load images at this point to query for its parameters
		# such as width and height because we can get those from json file
		xpos, ypos, width, height = entry[2:]

		if horizons.main.fife.imagemanager.exists(file):
			img = horizons.main.fife.imagemanager.get(file)
		else:
			img = horizons.main.fife.imagemanager.create(file)
			region = fife.Rect(xpos, ypos, width, height)
			img.useSharedImage(self.atlaslib[entry[1]], region)

		return img

