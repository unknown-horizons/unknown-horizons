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

from horizons.constants import RESEARCH
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.windows import Window

DONE = 'content/gui/images/background/square_120.png'

class ResearchLine(object):

	def __init__(self, research, y_position):
		super(ResearchLine, self).__init__()

		self._gui = load_uh_widget('research_line.xml')
		self._gui.position = (self._gui.position[0], self._gui.position[1] + 150 * y_position)
		self.left_bg = self._gui.findChild(name='left_bg')
		self.right_bg = self._gui.findChild(name='right_bg')

	def researched(self, first=True, second=False):
		if first:
			self.left_bg.image = DONE
		if second:
			self.right_bg.image = DONE


class ResearchDialog(Window):
	def __init__(self, windows, session=None):
		super(ResearchDialog, self).__init__(windows)

		self.research_options = {}
		self._session = session

	def _init(self):
		self._gui = load_uh_widget('research.xml')

		for i, research in enumerate(RESEARCH.THINGS):
			line = ResearchLine(research, i)
			self.research_options[i] = line
			self._gui.addChild(line._gui)

		tf = [True, False]
		self._session.random.shuffle(tf)

		self.researched(0, [True, True])
		self.researched(1, tf)
		self.researched(2, [False, False])

		self._gui.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)

	def researched(self, index, todo=None):
		self.research_options[index].researched(*todo)

	def show(self):
		self._init()

		self._gui.show()

	def hide(self):
		self._gui.hide()
