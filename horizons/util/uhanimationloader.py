# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.util.loaders.tilesetloader import TileSetLoader
from horizons.util.loaders.actionsetloader import ActionSetLoader

class UHAnimationLoader(fife.ResourceLoader):
	"""Loads Unknown Horizons animations using action/tile sets
	"""
	def __init__(self, imagepool):
		super(UHAnimationLoader, self).__init__()
		self.thisown = 0
		self.imagepool = imagepool

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
		commands = location.getFilename().split(':')
		id = commands.pop(0)
		actionset, action, rotation = id.rsplit('-', 2)
		commands = zip(commands[0::2], commands[1::2])

		set_loader = None
		if actionset.startswith('ts_'):
			set_loader = TileSetLoader
		else:
			set_loader = ActionSetLoader

		ani = fife.Animation()
		frame_start, frame_end = 0.0, 0.0
		for file in sorted(set_loader.get_sets()[actionset][action][int(rotation)].iterkeys()):
			frame_end = set_loader.get_sets()[actionset][action][int(rotation)][file]
			idx = self.imagepool.addResourceFromFile(file)
			img = self.imagepool.getImage(idx)
			for command, arg in commands:
				if command == 'shift':
					x, y = arg.split(',')
					if x.startswith('left'):
						x = int(x[4:]) + int(img.getWidth() / 2)
					elif x.startswith('right'):
						x = int(x[5:]) - int(img.getWidth() / 2)
					elif x.startswith(('center', 'middle')):
						x = int(x[6:])
					else:
						x = int(x)

					if y.startswith('top'):
						y = int(y[3:]) + int(img.getHeight() / 2)
					elif y.startswith('bottom'):
						y = int(y[6:]) - int(img.getHeight() / 2)
					elif y.startswith(('center', 'middle')):
						y = int(y[6:])
					else:
						y = int(y)

					img.setXShift(x)
					img.setYShift(y)
				elif command == 'cut':
					loc = fife.ImageLocation('asdf')
					loc.setParentSource(img)
					x, y, w, h = arg.split(',')

					if x.startswith('left'):
						x = int(x[4:])
					elif x.startswith('right'):
						x = int(x[5:]) + img.getWidth()
					elif x.startswith(('center', 'middle')):
						x = int(x[6:]) + int(img.getWidth() / 2)
					else:
						x = int(x)

					if y.startswith('top'):
						y = int(y[3:])
					elif y.startswith('bottom'):
						y = int(y[6:]) - img.getHeight()
					elif y.startswith(('center', 'middle')):
						y = int(y[6:]) + int(img.getHeight() / 2)
					else:
						y = int(y)

					if w.startswith('left'):
						w = int(w[4:]) - x
					elif w.startswith('right'):
						w = int(w[5:]) + img.getWidth() - x
					elif w.startswith(('center', 'middle')):
						w = int(w[6:]) + int(img.getWidth() / 2) - x
					else:
						w = int(w)

					if h.startswith('top'):
						h = int(h[3:]) - y
					elif h.startswith('bottom'):
						h = int(h[6:]) + img.getHeight() - y
					elif h.startswith(('center', 'middle')):
						h = int(h[6:]) + int(img.getHeight() / 2) - y
					else:
						h = int(h)

					loc.setXShift(x)
					loc.setYShift(y)
					loc.setWidth(w)
					loc.setHeight(h)

					idx = self.imagepool.addResourceFromLocation(loc)
					#img = horizons.main.fife.imagepool.getImage(idx)
			ani.addFrame(fife.ResourcePtr(self.imagepool, idx), max(1, int((float(frame_end) - frame_start)*1000)))
			frame_start = float(frame_end)
		ani.setActionFrame(0)
		ani.thisown = 0
		return ani


