# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from horizons.util import Color


class PlayerDataSelection(object):
	"""Subwidget for selecting player name and color.
	Used by Multiplayer and Singleplayer menu."""

	def __init__(self, parent_gui, widgets):
		"""
		Adds the playerdataselection container to a parent gui
		@param parent_gui: a pychan gui object containing a container named "playerdataselectioncontainer"
		@param widgets: WidgetsDict
		"""
		widgets.reload( 'playerdataselection' )
		self.gui = widgets[ 'playerdataselection' ]

		self.gui.distributeInitialData({ 'playercolor' : [ _(color.name) for color in Color ] })
		self.gui.distributeData({
			'playername': unicode(horizons.main.fife.get_uh_setting("Nickname")),
			'playercolor': 0
		})
		parent_gui.findChild(name="playerdataselectioncontainer").addChild( self.gui )

	def get_player_name(self):
		"""Returns the name that was entered by the user"""
		return self.gui.collectData('playername')

	def get_player_color(self):
		"""Returns the color that the player selected as Color obj"""
		return Color[self.gui.collectData('playercolor')+1] # +1 cause list entries start with 0, color indexes with 1

