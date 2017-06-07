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

from fife.extensions.pychan.widgets import HBox, Label

import horizons.globals
from horizons.gui.util import load_uh_widget
from horizons.util.color import Color
from horizons.util.python.callback import Callback


class PlayerDataSelection:
	"""Subwidget for selecting player name and color.
	Used by Multiplayer and Singleplayer menu."""

	def __init__(self, color_palette=None):
		"""
		@param widgets: WidgetsDict
		"""
		self.gui = load_uh_widget('playerdataselection.xml')

		self.colors = self.gui.findChild(name='playercolor')

		colorlabels = []
		events = {}

		# need the id to save it as int in settings file.
		for color in (Color.get_defaults() if color_palette is None else color_palette):
			label = Label(name='{color}'.format(color=color.name),
			              text="    ",
			              max_size=(20, 20),
			              min_size=(20, 20),
			              background_color=color)
			events['{label}/mouseClicked'.format(label=color.name)] = \
			                             Callback(self.set_color, color.id)
			colorlabels.append(label)

		# split into three rows with at max 5 entries in each row
		# right now there are 14 different colors to choose from.
		for i in range(0, len(colorlabels), 5):
			hbox = HBox(name='line_{index}'.format(index=i))
			hbox.addChildren(colorlabels[i:i + 5])
			self.colors.addChild(hbox)

		playertextfield = self.gui.findChild(name='playername')
		def playertextfield_clicked():
			if playertextfield.text == 'Unnamed Traveler':
				playertextfield.text = ""
		playertextfield.capture(playertextfield_clicked, event_name='mouseClicked')

		self.gui.mapEvents(events)
		self.update_data()

	def set_color(self, color_id):
		"""Updates the background color of large label where players
		see their currently chosen color.
		@param color_id: int. Gets converted to util.Color object.
		"""
		try:
			self.selected_color = Color.get(color_id)
		except KeyError:
			# For some reason, color_id can be 0 apparently:
			# http://forum.unknown-horizons.org/viewtopic.php?t=6927
			# Reset that setting to 1 if the problem occurs.
			self.selected_color = Color.get(1)
		self.gui.findChild(name='selectedcolor').background_color = self.selected_color

	def set_player_name(self, playername):
		"""Updates the player name"""
		self.gui.distributeData({
			'playername': str(playername),
			})

	def get_player_name(self):
		"""Returns the name that was entered by the user"""
		return self.gui.collectData('playername')

	def get_player_color(self):
		"""Returns the color that the player selected as Color obj"""
		return self.selected_color

	def get_widget(self):
		return self.gui

	def update_data(self):
		"""Update the player's name and color from the settings"""
		self.set_color(horizons.globals.fife.get_uh_setting("ColorID"))
		self.set_player_name(horizons.globals.fife.get_uh_setting("Nickname"))

	def save_settings(self):
		"""Stores the current player_name and color into settings"""
		horizons.globals.fife.set_uh_setting("Nickname", self.get_player_name())
		horizons.globals.fife.set_uh_setting("ColorID", self.get_player_color().id)
		horizons.globals.fife.save_settings()
