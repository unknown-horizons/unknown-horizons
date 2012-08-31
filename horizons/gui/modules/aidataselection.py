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

from horizons.constants import MULTIPLAYER

class AIDataSelection(object):
	"""Subwidget for selecting AI settings."""

	def __init__(self, parent_gui, widgets):
		"""
		Adds the aidataselection container to a parent gui
		@param parent_gui: a pychan gui object containing a container named "aidataselectioncontainer"
		@param widgets: WidgetsDict
		"""
		widgets.reload('aidataselection')
		self.gui = widgets['aidataselection']
		self.hidden = False

		self.gui.distributeInitialData({'ai_players': [unicode(n) for n in xrange(MULTIPLAYER.MAX_PLAYER_COUNT)]})
		self.gui.distributeData({
			'ai_players': int(horizons.main.fife.get_uh_setting("AIPlayers"))
		})
		parent_gui.findChild(name="aidataselectioncontainer").addChild(self.gui)

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
