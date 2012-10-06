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
from horizons.gui.window import Window


class MainMenu(Window):
	widget_name = 'mainmenu'

	def show(self):
		event_map={
			'startSingle'      : lambda: self.windows.show(self._gui._singleplayer), # first is the icon in menu
			'start'            : lambda: self.windows.show(self._gui._singleplayer), # second is the label in menu
			'startMulti'       : lambda: self.windows.show(self._gui._multiplayer),
			'start_multi'      : lambda: self.windows.show(self._gui._multiplayer),
			'settingsLink'     : lambda: self.windows.show(self._gui._settings),
			'settings'         : lambda: self.windows.show(self._gui._settings),
			'helpLink'         : self._gui.on_help,
			'help'             : self._gui.on_help,
			'closeButton'      : self._gui.show_quit,
			'quit'             : self._gui.show_quit,
			'dead_link'        : lambda: self.windows.show(self._gui._call_for_support), # call for help; SoC information
			'chimebell'        : lambda: self.windows.show(self._gui._call_for_support),
			'creditsLink'      : lambda: self.windows.show(self._gui._credits),
			'credits'          : lambda: self.windows.show(self._gui._credits),
			'loadgameButton'   : horizons.main.load_game,
			'loadgame'         : horizons.main.load_game,
			'changeBackground' : self._gui.get_random_background_by_button
		}

		self.widget = self._widget_loader[self.widget_name]
		self.widget.mapEvents(event_map)
		self.widget.capture(self._on_keypress, event_name="keyPressed")
		self.widget.show()
		self.widget.is_focusable = True
		self.widget.requestFocus()

	def hide(self):
		self.widget.hide()

	def _on_keypress(self, event):
		if event.getKey().getValue() == fife.Key.ESCAPE:
			self._gui.show_quit()
