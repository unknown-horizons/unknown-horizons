# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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


from fife.extensions.pychan.widgets import Icon, Widget
from fife.extensions.pychan.widgets.common import Attr, IntAttr

from horizons.gui.widgets.container import AutoResizeContainer
from horizons.gui.widgets.icongroup import TilingHBox


class ProgressBar(AutoResizeContainer):
	"""The ProgressBar is a pychan widget. It can be used in xml files like this:
	<ProgressBar />
	It is used to display a ProgressBar with a certain progress ;). Set the
	widgets progress attribute to set the progress. Pretty straight forward.
	The progress is a value from 0 to 100. Think of it as percent.
	"""
	ATTRIBUTES = AutoResizeContainer.ATTRIBUTES + [
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

	def _set_progress(self, progress):
		self.__progress = progress
		if self.tiles is None:
			self.fill = "content/gui/images/background/widgets/progressbar_fill.png"
		self.tiles.size = (int(progress * self.max_size[0] / 100), self.max_size[1])
		self.adaptLayout()

	def _get_progress(self):
		return self.__progress

	def _set_fill_image(self, image):
		self.__fill = image
		self.tiles = Icon(image=image)
		self.addChild(self.tiles)

	def _get_fill_image(self):
		return self.__fill

	def _set_background(self, background):
		self.__background = background
		icon = Icon(image=background)
		icon.min_size = icon.size = self.max_size
		self.addChild(icon)

	def _get_background(self):
		return self.__background

	progress = property(_get_progress, _set_progress)
	fill = property(_get_fill_image, _set_fill_image)
	background = property(_get_background, _set_background)
