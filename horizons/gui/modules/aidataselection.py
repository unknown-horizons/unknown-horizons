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

import horizons.globals
from horizons.constants import MULTIPLAYER
from horizons.gui.util import load_uh_widget


class AIDataSelection:
	"""Subwidget for selecting AI settings."""

	def __init__(self):
		self.gui = load_uh_widget('aidataselection.xml')

		self.gui.distributeInitialData({'ai_players': [str(n) for n in range(MULTIPLAYER.MAX_PLAYER_COUNT)]})
		self.gui.distributeData({
			'ai_players': int(horizons.globals.fife.get_uh_setting("AIPlayers"))
		})

	def get_ai_players(self):
		"""Returns the number that was entered by the user"""
		return self.gui.collectData('ai_players')

	def show(self):
		self.gui.show()

	def hide(self):
		self.gui.hide()

	def get_widget(self):
		return self.gui
