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

import logging
import weakref

from fife.extensions import pychan
from horizons.gui.widgets.tooltip import TooltipButton

import horizons.main
from horizons.util.gui import load_uh_widget
from horizons.util import Callback
from horizons.util.changelistener import metaChangeListenerDecorator

@metaChangeListenerDecorator('remove')
class TabWidget(object):
	"""The TabWidget class handles widgets which consist of many
	different tabs(subpanels, switchable via buttons(TabButtons).
	"""
	log = logging.getLogger("gui.tabs.tabwidget")

	def __init__(self, ingame_gui, tabs=None, position=None, name=None, active_tab=None):
		"""
		@param ingame_gui: IngameGui instance
		@param tabs: tab instances to show
		@param position: position as tuple (x, y)
		@param name: optional name for the tabwidget
		@param active_tab: int id of tab, 0 <= active_tab < len(tabs)
		"""
		super(TabWidget, self).__init__()
		self.name = name
		self.ingame_gui = ingame_gui
		self._tabs = [] if not tabs else tabs
		self.current_tab = self._tabs[0] # Start with the first tab
		self.widget = load_uh_widget("tab_base.xml")
		if position is None:
			# add positioning here
			self.widget.position = (
				horizons.main.fife.engine_settings.getScreenWidth() - 290,
				209
			)
		else:
			self.widget.position = position
		self.content = self.widget.findChild(name='content')
		self._init_tabs()
		# select a tab to show (first one is default)
		if active_tab is not None:
			self._show_tab(active_tab)

	def _init_tabs(self):
		"""Add enough tabbuttons for all widgets."""
		def on_tab_removal(tabwidget):
			# called when a tab is being removed (via weakref since tabs shouldn't have references to the parent tabwidget)
			# If one tab is removed, the whole tabwidget will die..
			# This is easy usually the desired behaviour.
			if tabwidget():
				tabwidget().on_remove()

		# Load buttons
		for index, tab in enumerate(self._tabs):
			# don't add a reference to the
			tab.add_remove_listener(Callback(on_tab_removal, weakref.ref(self)))
			container = pychan.Container()
			background = pychan.Icon()
			background.name = "bg_%s" % index
			button = TooltipButton()
			button.name = index
			if self.current_tab is tab:
				background.image = tab.button_background_image_active
				button.up_image = tab.button_active_image
			else:
				background.image = tab.button_background_image
				button.up_image = tab.button_up_image
			button.down_image = tab.button_down_image
			button.hover_image = tab.button_hover_image
			button.is_focusable = False
			button.size = (50, 50)
			button.capture(Callback(self._show_tab, index))
			if hasattr(tab, 'tooltip') and tab.tooltip is not None:
				button.tooltip = unicode(tab.tooltip)
			container.size = background.size
			container.addChild(background)
			container.addChild(button)
			self.content.addChild(container)
		self.widget.size = (50, 55*len(self._tabs))
		self.widget.adaptLayout()

		self._apply_layout_hack()

	def _show_tab(self, number):
		"""Used as callback function for the TabButtons.
		@param number: tab number that is to be shown.
		"""
		if not number in range(len(self._tabs)):
			# this usually indicates a non-critical error, therefore we can handle it without crashing
			import traceback
			traceback.print_stack()
			self.log.warn("Invalid tab number %s, available tabs: %s", number, self._tabs)
			return
		self.current_tab.hide()
		new_tab = self._tabs[number]
		old_bg = self.content.findChild(name = "bg_%s" % self._tabs.index(self.current_tab))
		old_bg.image = self.current_tab.button_background_image
		old_button = self.content.findChild(name=self._tabs.index(self.current_tab))
		old_button.up_image = self.current_tab.button_up_image

		new_bg = self.content.findChild(name = "bg_%s" % number)
		new_bg.image = self.current_tab.button_background_image_active
		new_button = self.content.findChild(name=number)
		new_button.up_image = new_tab.button_active_image
		self.current_tab = new_tab
		# important to display the tabs correctly in front
		self.widget.hide()
		self.show()

		self._apply_layout_hack()

	def _apply_layout_hack(self):
		# pychan layouting depends on time, it's usually in a better mood later.
		# this introduces some flickering, but fixes #916
		from horizons.extscheduler import ExtScheduler
		ExtScheduler().add_new_object(self.current_tab.widget.adaptLayout, self, run_in=0)

	def _draw_widget(self):
		"""Draws the widget, but does not show it automatically"""
		self.current_tab.position = (self.widget.position[0] + self.widget.size[0] - 11,
		                             self.widget.position[1] - 52)
		self.current_tab.refresh()

	def show(self):
		"""Show the current widget"""
		self.current_tab.ensure_loaded()
		self._draw_widget()
		self.current_tab.show()
		self.widget.show()
		self.ingame_gui.minimap_to_front()

	def hide(self, caller=None):
		"""Hide the current widget"""
		self.current_tab.hide()
		self.widget.hide()

	def _get_x(self):
		"""Returs the widget's x position"""
		return self.widget.position[0]

	def _set_x(self, value):
		"""Sets the widget's x position"""
		self.widget.position = (value, self.widget.position[1])

	# Shortcut to set and retrieve the widget's current x position.
	x = property(_get_x, _set_x)

	def _get_y(self):
		"""Returns the widget's y position"""
		return self.widget.position[1]

	def _set_y(self, value):
		"""Sets the widget's y position"""
		self.widget.position = (self.widget.position[0], value)

	# Shortcut to set and retrieve the widget's current y position.
	y = property(_get_y, _set_y)





