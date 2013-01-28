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


from fife.extensions.pychan.widgets import Icon
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
	ATTRIBUTES = AutoResizeContainer.ATTRIBUTES + [IntAttr('progress'), Attr('background')]

	def __init__(self, progress=0, background=None, **kwargs):
		super(ProgressBar, self).__init__(**kwargs)
		self.fill = "content/gui/images/background/widgets/progressbar_fill.png"
		self.__progress = progress
		self.__background = background
		self.tiles = TilingHBox()
		self.tiles.tiles_img = self.fill
		self.tiles.start_img = self.tiles.final_img = None
		self.addChild(self.tiles)

	def _set_progress(self, progress):
		self.__progress = progress
		self.tiles.amount = int(progress)

	def _get_progress(self):
		return self.__progress

	def _set_background(self, background):
		self.__background = background
		self.addChild(Icon(image=background))

	def _get_background(self):
		return self.__background

	progress = property(_get_progress, _set_progress)
	background = property(_get_background, _set_background)
