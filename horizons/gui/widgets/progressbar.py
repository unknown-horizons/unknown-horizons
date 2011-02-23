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

from fife.extensions import pychan

class ProgressBar(pychan.widgets.Container):
	"""The ProgressBar is a pychan widget. It can be used in xml files like this:
	<ProgressBar />
	It is used to display a ProgressBar with a certain progress ;). Set the
	widgets progress attribute to set the progress. Pretty straight forward.
	The progress is a value from 0 to 100. Think of it as percent.
	"""

	def __init__(self, progress=0, **kwargs):
		super(ProgressBar, self).__init__(**kwargs)
		self.size = (200, 10)
		self.__progress = progress
		self.icon = None
		self._init_gui()

	def _init_gui(self):
		self.icon = pychan.widgets.Icon(image = "content/gui/images/background/widgets/progressbar_bg.png")
		self.icon.min_size = (0, 0)
		self.addChild(self.icon)
		self._draw()

	def _draw(self):
		self.icon.size = (int(self.progress/100.0*self.size[0]), self.size[1])

	def _set_progress(self, progress):
		self.__progress = progress
		self._draw()

	def _get_progress(self):
		return self.__progress

	progress = property(_get_progress, _set_progress)
