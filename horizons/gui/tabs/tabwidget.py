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

import logging
from operator import attrgetter
import traceback
import weakref

from fife.extensions.pychan.widgets import Container, Icon, VBox

from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import ImageButton
from horizons.util.python.callback import Callback
from horizons.util.changelistener import metaChangeListenerDecorator

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
		self.widget = load_uh_widget("tab_base.xml")
		self.widget.position_technique = 'right:top+159'

		self.buttons = VBox(name='buttons', position_technique='right-239:top+209')

		self.tab_bg = self.widget.findChild(name='tab_background')
		self.content = self.widget.findChild(name='content')
		self.left_icon = self.widget.findChild(name='header_icon_left')
		self.right_icon = self.widget.findChild(name='header_icon_right')

		self._init_tab_buttons()
		# select a tab to show (first one is default)
		if active_tab is None:
			self.show_tab(0)
		else:
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
			# TODO "the"?
			# don't add a reference to the
			tab.add_remove_listener(Callback(on_tab_removal, weakref.ref(self)))
			container = Container(name="container_%s" % index)
			background = Icon(name="bg_%s" % index)
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
			container.size = background.size
			container.addChildren(background, button)
			self.buttons.addChild(container)

	def show_tab(self, number):
		"""Used as callback function for the TabButtons.
		@param number: tab number that is to be shown.
		"""
		if not number in range(len(self._tabs)):
			# this usually indicates a non-critical error, therefore we can handle it without crashing
			traceback.print_stack()
			self.log.warning("Invalid tab number %s, available tabs: %s", number, self._tabs)
			return

		old_number = "%s" % self._tabs.index(self.current_tab)
		if number == old_number:
			return

		new_tab = self._tabs[number]

		if self.current_tab.is_visible():
			self.current_tab.hide()

		old_name = "bg_%s" % self._tabs.index(self.current_tab)
		old_bg = self.buttons.findChild(name=old_name)
		old_bg.image = self.current_tab.button_background_image
		old_button = self.buttons.findChild(name=old_number)
		old_button.path = self.current_tab.path

		new_bg = self.buttons.findChild(name = "bg_%s" % number)

		new_bg.image = self.current_tab.button_background_image_active
		new_button = self.buttons.findChild(name=str(number))
		new_button.path = new_tab.path_active
		self.current_tab = new_tab
		self.current_tab.ensure_loaded()

		headline_text = getattr(self.current_tab.widget, 'headline', None)
		if headline_text is None:
			headline_text = u'{instance.name}'
		if headline_text.startswith('{') and headline_text.endswith('}'):
			template = headline_text[1:-1]
			headline_text = attrgetter(template)(self.current_tab)

		headline = self.content.parent.findChild(name='headline')
		headline.text = headline_text

		left_icon = getattr(self.current_tab.widget, 'left_icon', None)
		self.left_icon.image = left_icon
		right_icon = getattr(self.current_tab.widget, 'right_icon', None)
		self.right_icon.image = right_icon

		self.content.removeAllChildren()
		self.content.addChild(self.current_tab.widget)
		self.current_tab.show()
		self.current_tab.refresh()
		self.content.parent.adaptLayout()  # resize AutoResizeContainer
		self.tab_bg.amount = (self.content.parent.size[1] + 25) // 50
		self.widget.adaptLayout()  # resize AutoResizeContainer

	def show(self):
		"""Show the current widget"""
		self.widget.show()
		self.buttons.show()
		self.ingame_gui.minimap_to_front()

	def hide(self, caller=None):
		"""Hide the current widget"""
		self.buttons.hide()
		self.widget.hide()
