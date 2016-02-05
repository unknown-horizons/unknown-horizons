# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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


class AIDataSelection(object):
	"""Subwidget for selecting AI settings."""

	def __init__(self):
		self.gui = load_uh_widget('aidataselection.xml')

		self.gui.distributeInitialData({'ai_players': [unicode(n) for n in xrange(
			MULTIPLAYER.MAX_PLAYER_COUNT)]})
		self.gui.distributeData({
			'ai_players': int(horizons.globals.fife.get_uh_setting("AIPlayers"))
		})

		# FIXME
		# pychan raises an RuntimeError if you attempt to hide a child in a container
		# that is already hidden (or does not exist). Work around by tracking the
		# state of the widget. The initial state depends on the parent widget.
		self.hidden = False

	def get_ai_players(self):
		"""Returns the number that was entered by the user"""
		return self.gui.collectData('ai_players')

	def show(self):
		self.gui.parent.showChild(self.gui)
		self.hidden = False

	def hide(self):
		if not self.hidden:
			self.gui.parent.hideChild(self.gui)
			self.hidden = True

	def get_widget(self):
		return self.gui
