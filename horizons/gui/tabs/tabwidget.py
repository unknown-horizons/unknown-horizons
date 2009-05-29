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
import pychan

from horizons.i18n import load_xml_translated

class TabWidget(object):
	"""The TabWidget class handles widgets which consist of many
	different tabs(subpanels, switchable via buttons(TabButtons).
	"""

	def __init__(self, tabs=[], position=None):
		super(TabWidget, self).__init__()
		self._tabs = tabs
		self.current_tab = self._tabs[0] # Start with the first tab
		self.widget = load_xml_translated("tab_widget/tab_base.xml")
		if position is None:
			# add positioning here
			self.widget.position = (100, 100)
		else:
			self.widget.position = position
		self.content = self.widget.findChild(name='content')
		self.init_tabs()

	def init_tabs(self):
		"""Add enough tabbuttons for all widgets."""
		# Load buttons
		for index, tab in enumerate(self._tabs):
			button = pychan.ImageButton()
			button.name = index
			if self.current_tab is tab:
				button.up_image = tab.button_active_image
			else:
				button.up_image = tab.button_up_image
			button.down_image = tab.button_down_image
			button.hover_image = tab.button_hover_image
			button.size = (50, 50)
			button.capture(pychan.tools.callbackWithArguments(self.show_tab, index))
			self.content.addChild(button)
		self.content._recursiveResizeToContent()

		self.widget.size = (50, 50*len(self._tabs))

		self.content.adaptLayout()
		self.widget._recursiveResizeToContent()

	def show_tab(self, number):
		"""Used as callback function for the TabButtons.
		@param number: tab number that is to be shown.
		"""
		self.current_tab.hide()
		new_tab = self._tabs[number]
		old_button = self.content.findChild(name=self._tabs.index(self.current_tab))
		old_button.up_image = self.current_tab.button_up_image
		new_button = self.content.findChild(name=number)
		new_button.up_image = new_tab.button_active_image
		self.current_tab = new_tab
		self.show()

	def draw_widget(self):
		"""Draws the widget, but does not show it automatically"""
		self.current_tab.position = (self.widget.position[0]+self.widget.size[0],
									 self.widget.position[1])
		self.current_tab.refresh()

	def show(self):
		"""Show the current widget"""
		self.draw_widget()
		self.widget.show()
		self.current_tab.show()

	def hide(self):
		"""Hide the current widget"""
		self.current_tab.hide()
		self.widget.hide()

	def get_x(self):
		"""Returs the widget's x position"""
		return self.widget.position[0]

	def set_x(self, value):
		"""Sets the widget's x position"""
		self.widget.position = (value, self.widget.position[1])

	# Shortcut to set and retrieve the widget's current x position.
	x = property(get_x, set_x)

	def get_y(self):
		"""Returns the widget's y position"""
		return self.widget.position[1]

	def set_y(self, value):
		"""Sets the widget's y position"""
		self.widget.position = (self.widget.position[0], value)

	# Shortcut to set and retrieve the widget's current y position.
	y = property(get_y, set_y)





