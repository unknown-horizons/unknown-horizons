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

from fife.extensions.pychan.widgets import Label

from horizons.gui.modules.loadingscreen import GAMEPLAY_TIPS
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.windows import Window


class HelpDialog(Window):

	def __init__(self, windows):
		super().__init__(windows)

		self.widget = load_uh_widget('help.xml')
		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)
		self.widget.findChild(name='headline').text = GAMEPLAY_TIPS['name']
		tip_box = self.widget.findChild(name='tip_box')
		size = {'max_size': (300, 60), 'min_size': (300, 20)}
		for tip in GAMEPLAY_TIPS['items']:
			tip_label = Label(text=str(tip), wrap_text=True, **size)
			tip_box.addChild(tip_label)

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()
