# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.gui.utility import stylize_widget
from horizons.util import PychanChildFinder
from horizons.util.changelistener import metaChangeListenerDecorator

@metaChangeListenerDecorator('remove')
class TabInterface(object):
	"""
	The TabInterface should be used by all classes that represent Tabs for the
	TabWidget.

	It is important that the currently used widget by the tab is always set to
	self.widget, to ensure proper functionality.
	If you want to override the TabButton image used for the tab, you also have
	to set the button_image_{up,down,hover} variables.

	Use the refresh() method to implement any redrawing of the widget. The
	TabWidget will call this method based on callbacks. If you set any callbacks
	yourself, make sure you get them removed when the widget is deleted.

	Make sure to call the init_values() function after you set self.widget, to
	ensure proper initialization of needed properties.
	"""

	def __init__(self, widget = None, **kwargs):
		super(TabInterface, self).__init__()
		if widget is not None:
			self.widget = load_xml_translated(widget)
			self.widget.child_finder = PychanChildFinder(self.widget)
		else:
			self.widget = None
		# You can override these if you want to use separate images for your tab
		self.button_up_image = 'content/gui/images/tabwidget/tab.png' # TabButtons usual image
		self.button_down_image = 'content/gui/images/tabwidget/tab.png' # TabButtons image when mouse is pressed
		self.button_hover_image = 'content/gui/images/tabwidget/tab_a.png' # TabButtons hoverimage
		self.button_active_image = 'content/gui/images/tabwidget/tab.png' # TabButtons active image
		self.button_background_image = 'content/gui/images/tabwidget/tab_dark.png' # TabButtons background image
		self.button_background_image_active = 'content/gui/images/tabwidget/tab_active_xxl.png' # TabButtons background image when selected

	def init_values(self):
		"""Call this method after the widget has been initialised."""
		self.x_pos = self.widget.position[0]
		self.y_pos = self.widget.position[1]
		stylize_widget(self.widget, style='menu_black')

	def show(self):
		"""Shows the current widget"""
		self.widget.show()

	def hide(self):
		"""Hides the current widget"""
		self.widget.hide()

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		pass

	def _get_x(self):
		"""Returs the widget's x position"""
		return self.widget.position[0]

	def __set_x(self, value):
		"""Sets the widget's x position"""
		self.widget.position = (value, self.widget.position[1])

	# Shortcut to set and retrieve the widget's current x position.
	x_pos = property(_get_x, __set_x)

	def _get_y(self):
		"""Returns the widget's y position"""
		return self.widget.position[1]

	def _set_y(self, value):
		"""Sets the widget's y position"""
		self.widget.position = (self.widget.position[0], value)

	# Shortcut to set and retrieve the widget's current y position.
	y_pos = property(_get_y, _set_y)

	def _get_position(self):
		"""Returns the widget's position as"""
		return self.widget.position

	def _set_position(self, value):
		"""Sets the widgets position"""
		self.widget.position = value

	# Shortcut to set and retrieve the widget's current y position.
	position = property(_get_position, _set_position)

	def __del__(self):
		"""Do cleanup work here."""
		pass
