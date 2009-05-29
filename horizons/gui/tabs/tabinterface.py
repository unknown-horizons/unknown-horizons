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

class TabInterface(object):
	"""
	The TabInterface should be used by all classes that represent Tabs for the TabWidget.

	It is important that the currently used widget by the tab is always set to self.widget,
	to ensure proper functionality.
	If you want to override the TabButton image used for the tab, you also have to set the
	button_image_{up,down,hover} variables.

	Use the refresh() method to implement any redrawing of the widget. The TabWidget will
	call this method based on callbacks. If you set any callbacks yourself, make sure you
	get them removed when the widget is deleted.

	Make sure to call the init_values() function after you set self.widget, to ensure
	proper initialization of needed properties.
	"""

	def __init__(self, widget = None, button_up_image='content/gui/tab_widget/tab.png', button_down_image='content/gui/tab_widget/tab.png', button_hover_image='content/gui/tab_widget/tab2.png', button_active_image='content/gui/tab_widget/tab.png', **kwargs):
		super(TabInterface, self).__init__()
		self.widget = widget
		self.button_up_image = button_up_image # Used for the TabButtons upimage
		self.button_down_image = button_down_image # Used for the TabButtons downimage
		self.button_hover_image = button_hover_image # Used for the TabButtons hoverimage
		self.button_active_image = button_active_image # Used for the TabButtons active image

	def init_values(self):
		"""Call this methode after the widget has been initialised."""
		self.x = self.widget.position[0]
		self.y = self.widget.position[1]
		self.widget.stylize("menu")

	def show(self):
		"""Shows the current widget"""
		self.widget.show()

	def hide(self):
		"""Hides the current wigdet"""
		self.widget.hide()

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		pass

	def get_x(self):
		return self.widget.position[0]

	def set_x(self, value):
		self.widget.position = (value, self.widget.position[1])

	# Shortcut to set and retrieve the widget's current x position.
	x = property(get_x, set_x)

	def get_position(self):
		return self.widget.position

	def set_position(self, value):
		self.widget.position = value

	# Shortcut to set and retrieve the widget's current y position.
	position = property(get_position, set_position)

	def __del__(self):
		"""Do cleanup work here."""
		pass