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

import logging
import traceback
import weakref

from fife.extensions.pychan.widgets import Container, Icon

from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import ImageButton
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.util.python.callback import Callback


@metaChangeListenerDecorator('remove')
class TabWidget(object):
	"""The TabWidget class handles widgets which consist of many
	different tabs(subpanels, switchable via buttons(TabButtons).
	"""
	log = logging.getLogger("gui.tabs.tabwidget")

	def __init__(self, ingame_gui, tabs=None, name=None, active_tab=None):
		"""
		@param ingame_gui: IngameGui instance
		@param tabs: tab instances to show
		@param name: optional name for the tabwidget
		@param active_tab: int id of tab, 0 <= active_tab < len(tabs)
		"""
		super(TabWidget, self).__init__()
		self.name = name
		self.ingame_gui = ingame_gui
		self._tabs = [] if not tabs else tabs
		self.current_tab = self._tabs[0] # Start with the first tab
		self.current_tab.ensure_loaded() # loading current_tab widget
		self.widget = load_uh_widget("tab_base.xml")
		self.widget.position_technique = 'right-239:top+209'
		self.content = self.widget.findChild(name='content')
		self._init_tab_buttons()
		# select a tab to show (first one is default)
		if active_tab is not None:
			self.show_tab(active_tab)

	def _init_tab_buttons(self):
		"""Add enough tabbuttons for all widgets."""
		def on_tab_removal(tabwidget):
			# called when a tab is being removed (via weakref since tabs shouldn't have references to the parent tabwidget)
			# If one tab is removed, the whole tabwidget will die..
			# This is easy usually the desired behavior.
			if tabwidget():
				tabwidget().on_remove()

		# Load buttons
		for index, tab in enumerate(self._tabs):
			# don't add a reference to the
			tab.add_remove_listener(Callback(on_tab_removal, weakref.ref(self)))
			container = Container(name="container_{}".format(index))
			background = Icon(name="bg_{}".format(index))
			button = ImageButton(name=str(index), size=(50, 50))
			if self.current_tab is tab:
				background.image = tab.button_background_image_active
				button.path = tab.path_active
			else:
				background.image = tab.button_background_image
				button.path = tab.path
			button.capture(Callback(self.show_tab, index))
			if hasattr(tab, 'helptext') and tab.helptext:
				button.helptext = tab.helptext
			container.size = (50,52)
			container.addChild(background)
			container.addChild(button)
			self.content.addChild(container)
		self.widget.size = (54, 55*len(self._tabs))
		self.widget.adaptLayout()

		self._apply_layout_hack()

	def show_tab(self, number):
		"""Used as callback function for the TabButtons.
		@param number: tab number that is to be shown.
		"""
		if number >= len(self._tabs):
			# this usually indicates a non-critical error, therefore we can handle it without crashing
			traceback.print_stack()
			self.log.warning("Invalid tab number %s, available tabs: %s", number, self._tabs)
			return
		if self.current_tab.is_visible():
			self.current_tab.hide()
		new_tab = self._tabs[number]
		old_bg = self.content.findChild(name = "bg_{}".format(self._tabs.index(self.current_tab)))
		old_bg.image = self.current_tab.button_background_image
		name = str(self._tabs.index(self.current_tab))
		old_button = self.content.findChild(name=name)
		old_button.path = self.current_tab.path

		new_bg = self.content.findChild(name = "bg_{}".format(number))
		new_bg.image = self.current_tab.button_background_image_active
		new_button = self.content.findChild(name=str(number))
		new_button.path = new_tab.path_active
		self.current_tab = new_tab
		# important to display the tabs correctly in front
		self.widget.hide()
		self.show()

		self._apply_layout_hack()

	def _apply_layout_hack(self):
		# pychan layouting depends on time, it's usually in a better mood later.
		# this introduces some flickering, but fixes #916
		from horizons.extscheduler import ExtScheduler
		def do_apply_hack():
			# just query widget when executing, since if lazy loading is used, the widget
			# does not exist yet in the outer function
			self.current_tab.widget.adaptLayout()
		ExtScheduler().add_new_object(do_apply_hack, self, run_in=0)

	def _draw_widget(self):
		"""Draws the widget, but does not show it automatically"""
		self.current_tab.position = (self.widget.position[0] + self.widget.size[0] - 11,
		                             self.widget.position[1] - 52)
		self.current_tab.refresh()

	def show(self):
		"""Show the current widget"""
		# show before drawing so that position_technique properly sets
		# button positions (which we want to draw our tabs relative to)
		self.widget.show()
		self._draw_widget()
		self.current_tab.show()
		self.ingame_gui.minimap_to_front()

	def hide(self, caller=None):
		"""Hides current tab and this widget"""
		self.current_tab.hide()
		self.widget.hide()
