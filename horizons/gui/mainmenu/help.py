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

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.mainmenu import Dialog
from horizons.gui.widgets.imagebutton import OkButton


class Help(Dialog):
	widget_name = 'help'
	return_events = {OkButton.DEFAULT_NAME: True}

	def pre(self, *args, **kwargs):
		# make game pause if there is a game and we're not in the main menu
		# TODO check missing if we're in the main menu
		if self._gui.session:
			PauseCommand().execute(self._gui.session)
			self._gui.session.ingame_gui.on_escape() # close dialogs that might be open

	def post(self, retval):
		if self._gui.session:
			UnPauseCommand().execute(self._gui.session)
