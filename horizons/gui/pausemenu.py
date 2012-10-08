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

import horizons.main

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.window import Window
from horizons.util.startgameoptions import StartGameOptions


class PauseMenu(Window):
	widget_name = 'ingamemenu'

	def show(self):
		PauseCommand(suggestion=True).execute(self._gui.session)

		self._widget_loader.reload(self.widget_name)
		self.widget = self._widget_loader[self.widget_name]

		event_map = {
			'loadgame'       : self.load_game,
			'loadgameButton' : self.load_game,
			'savegame'       : self.save_game,
			'savegameButton' : self.save_game,
			'settings'       : lambda: self.windows.show(self._gui._settings),
			'settingsLink'   : lambda: self.windows.show(self._gui._settings),
			'help'           : self._gui.toggle_help,
			'helpLink'       : self._gui.toggle_help,
			'start'          : self.windows.close,
			'startGame'      : self.windows.close,
			'quit'           : self._gui.quit_session,
			'closeButton'    : self._gui.quit_session,
		}

		self.widget.mapEvents(event_map)
		self._capture_escape(self.widget)
		self.widget.position_technique = "automatic"
		self.widget.show()
		self._focus(self.widget)

	def hide(self):
		UnPauseCommand(suggestion=True).execute(self._gui.session)
		self.widget.hide()

	def save_game(self):
		"""Wrapper for saving for separating gui messages from save logic"""
		success = self._gui.session.save()
		if not success:
			# There was a problem during the 'save game' procedure.
			self.windows.show_popup(_('Error'), _('Failed to save.'))

	def load_game(self):
		saved_game = self.windows.show(self._gui._saveload, mode='load')
		if saved_game is None:
			return False # user aborted dialog

		self._gui.main_gui.show_loading_screen()
		options = StartGameOptions(saved_game)
		horizons.main.start_singleplayer(options)
		return True

