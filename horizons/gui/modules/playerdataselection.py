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

from fife.extensions.pychan.widgets import HBox, Label

import horizons.globals
from horizons.gui.util import load_uh_widget
from horizons.util.color import Color
from horizons.util.python.callback import Callback


class PlayerDataSelection(object):
	"""Subwidget for selecting player name and color.
	Used by Multiplayer and Singleplayer menu."""

	def __init__(self, color_palette=None):
		"""
		@param widgets: WidgetsDict
		"""
		self.gui = load_uh_widget('playerdataselection.xml')

		self.colors = self.gui.findChild(name='playercolor')
		self.selected_color = horizons.globals.fife.get_uh_setting("ColorID") # starts at 1!
		self.set_color(self.selected_color)

		colorlabels = []
		events = {}

		# need the id to save it as int in settings file.
		for color in (Color if color_palette is None else color_palette):
			label = Label(name = u'{color}'.format(color=color.name),
			              text = u"    ",
			              max_size = (20, 20),
			              min_size = (20, 20),
			              background_color = color)
			events['{label}/mouseClicked'.format(label=color.name)] = \
			                             Callback(self.set_color, color.id)
			colorlabels.append(label)

		# split into three rows with at max 5 entries in each row
		# right now there are 14 different colors to choose from.
		for i in xrange(0, len(colorlabels), 5):
			hbox = HBox(name='line_{index}'.format(index=i))
			hbox.addChildren(colorlabels[i:i+5])
			self.colors.addChild(hbox)

		self.gui.distributeData({
			'playername': unicode(horizons.globals.fife.get_uh_setting("Nickname")),
		})
		self.gui.mapEvents(events)

	def set_color(self, color_id):
		"""Updates the background color of large label where players
		see their currently chosen color. Stores result in settings.
		@param color_id: int. Gets converted to FIFE Color object.
		"""
		self.selected_color = Color[color_id]
		horizons.globals.fife.set_uh_setting("ColorID", color_id)
		self.gui.findChild(name='selectedcolor').background_color = Color[color_id]

	def set_player_name(self, playername):
		horizons.globals.fife.set_uh_setting("Nickname", playername)
		self.gui.distributeData({
			'playername': unicode(playername),
			})

	def get_player_name(self):
		"""Returns the name that was entered by the user"""
		return self.gui.collectData('playername')

	def get_player_color(self):
		"""Returns the color that the player selected as Color obj"""
		return self.selected_color

	def get_widget(self):
		return self.gui
