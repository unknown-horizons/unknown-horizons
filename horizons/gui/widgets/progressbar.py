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


from fife.extensions.pychan.widgets import ABox, Icon, Widget
from fife.extensions.pychan.widgets.common import Attr, IntAttr

from horizons.gui.widgets.icongroup import TilingHBox


class ProgressBar(ABox):
	"""The ProgressBar is a pychan widget. It can be used in xml files like this:
	<ProgressBar />
	It is used to display a ProgressBar with a certain progress ;). Set the
	widgets progress attribute to set the progress. Pretty straight forward.
	The progress is a value from 0 to 100. Think of it as percent.
	"""
	ATTRIBUTES = ABox.ATTRIBUTES + [
		IntAttr('progress'), Attr('fill'), Attr('background'),
	]

	def __init__(self, progress=0, fill=None, background=None, **kwargs):
		super(ProgressBar, self).__init__(**kwargs)
		if self.max_size == Widget.DEFAULT_MAX_SIZE:
			self.max_size = (100, 16)
		self.__progress = progress
		self.__fill = fill
		self.__background = background
		self.tiles = None
		self.bg_icon = None

	def _set_progress(self, progress):
		self.__progress = progress
		if self.bg_icon is None:
			self.background = "content/gui/images/background/bar_bg.png"
		if self.tiles is None:
			self.fill = "content/gui/images/background/widgets/progressbar_fill.png"
		self.tiles.size = (int(self.max_size[0] * progress / 100.0), self.max_size[1])
		self.adaptLayout()

	def _get_progress(self):
		return self.__progress

	def _set_fill_image(self, image):
		self.__fill = image
		self.tiles = Icon(image=image, scale=True)
		self.addChild(self.tiles)

	def _get_fill_image(self):
		return self.__fill

	def _set_background(self, background):
		self.__background = background
		self.bg_icon = Icon(image=background, scale=True)
		self.bg_icon.min_size = self.bg_icon.size = self.max_size
		self.addChild(self.bg_icon)

	def _get_background(self):
		return self.__background

	progress = property(_get_progress, _set_progress)
	fill = property(_get_fill_image, _set_fill_image)
	background = property(_get_background, _set_background)


class TilingProgressBar(ProgressBar):
	"""ProgressBar that tiles its fill image instead of stretching.

	Also supports distinct left and right border/frame images which count
	towards the displayed progress value and fill images of width > 1px.
	"""
	ATTRIBUTES = ProgressBar.ATTRIBUTES + [Attr('left'), Attr('right')]

	def __init__(self, left=None, right=None, **kwargs):
		super(TilingProgressBar, self).__init__(**kwargs)
		self.__left = left
		self.__right = right
		self.tiles = TilingHBox()
		self.addChild(self.tiles)
		self.tiles_width = 1
		self.left_width = 0
		self.right_width = 0

	def _get_progress(self):
		return self.__progress
	def _set_progress(self, progress):
		self.__progress = progress
		fill_width = (progress / 100.0) * (self.max_size[0] / self.tiles_width)
		self.tiles.amount = int(fill_width) - self.left_width - self.right_width
		self.adaptLayout()

	def _get_left_image(self):
		return self.__left
	def _set_left_image(self, image):
		self.__left = image
		self.left_width = Icon(image=image).size[0]
		self.tiles.start_img = image

	def _get_fill_image(self):
		return self.__fill
	def _set_fill_image(self, image):
		self.__fill = image
		self.tiles_width = Icon(image=image).size[0]
		self.tiles.tiles_img = image

	def _get_right_image(self):
		return self.__right
	def _set_right_image(self, image):
		self.__right = image
		self.right_width = Icon(image=image).size[0]
		self.tiles.final_img = image

	progress = property(_get_progress, _set_progress)
	left = property(_get_left_image, _set_left_image)
	fill = property(_get_fill_image, _set_fill_image)
	right = property(_get_right_image, _set_right_image)
