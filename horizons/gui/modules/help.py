# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.windows import Window


class HelpDialog(Window):

	def __init__(self, windows, session=None):
		super(HelpDialog, self).__init__(windows)

		self._session = session
		self.widget = load_uh_widget('help.xml')
		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)

	def show(self):
		self.widget.show()
		if self._session:
			PauseCommand().execute(self._session)

	def hide(self):
		if self._session:
			UnPauseCommand().execute(self._session)
		self.widget.hide()
