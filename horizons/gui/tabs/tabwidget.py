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
from horizons.i18n import load_xml_translated

class TabWidget(object):

	default_button_upimage = ''
	default_button_downimage = ''
	default_button_hoverimage = ''

	def __init__(self, tabs=[], position=None):
		super(TabWidget, self).__init__()
		self._tabs = tabs
		if position is None:
			self.position = (10,10) #TODO: add positioning here
		else:
			self.position = position
		self.current_tab = self._tabs[0] # Start with the first tab
		self.widget = load_xml_translated("content/gui/tabwidget_base.xml") # TODO create this widget

	def init_tabs(self):
		"""Add enough tabbuttons for all widgets."""
		# Check if the button_image_{up,down,hover} are set and use them if set.
		pass

	def show_tab(self, number):
		"""Used as callback function for the TabButtons.
		@param number: tab number that is to be shown.
		"""
		self.current_tab.hide()
		self.current_tab = self._tabs[number]
		self.show()

	def draw_widget(self):
		"""Draws the widget, but does not show it automatically"""
		self.current_tab.position = (self.wigdet.position[0]+self.widget.size[0], self.widget.position[1]+self.widget.size[1])
		self.current_tab.refresh()

	def show(self):
		"""Show the current widget"""
		self.draw_widget()
		self.widget.show()
		self.current_tab.show()

	def hide(self):
		self.current_tab.hide()
		self.widget.hide()






