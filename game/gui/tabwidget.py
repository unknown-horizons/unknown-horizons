# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main
import pychan
from game.util.inventory_widget import Inventory

class TabWidget(object):
	"""Used to create menus for buildings, ships, etc. Uses multiple tabs.
	@var object: instance of an object that is later used to fill the tabs with information. Can be None for widgets that don't need any external information
	@var system_id: int id of the tab_system, used to get all the tabs for this widget from the db
	@var callbacks: dict(dict) like this: {'widgetname1': callbackdict, 'widgetname2': callbackdict}. Does not have to be provided."""

	def __init__(self, system_id, object=None, callbacks={}):
		self.object = object
		self.tabs = []
		for name, xml, up, down, hover in game.main.db(" SELECT tabs.name, tabs.xml, tabs.button_up_image, tabs.button_down_image, tabs.button_hover_image FROM tab_system LEFT JOIN tabs ON tabs.rowid = tab_system.tab_id WHERE tab_system.system_id=? ORDER BY tab_system.position", system_id):
			self.tabs.append(Tab(name, xml, up, down, hover))
		self.widget = game.main.fife.pychan.loadXML('content/gui/tab_widget/tab_main.xml')
		self.widget.stylize('menu')
		self.widget.position = (
			game.main.session.ingame_gui.gui['minimap'].position[0] - self.widget.size[0] - 50 if game.main.fife.settings.getScreenWidth()/2 + self.widget.size[0]/2 > game.main.session.ingame_gui.gui['minimap'].position[0] else game.main.fife.settings.getScreenWidth()/2 - self.widget.size[0]/2,
			game.main.fife.settings.getScreenHeight() - self.widget.size[1] - 30
		)
		self.widget.active = 0 # index of the currently active tab
		for index, tab in enumerate(self.tabs):
			button = self.widget.findChild(name=str(index)) # load button
			button.up_image = tab.up_image
			button.down_image = tab.hover_image
			button.hover_image = tab.hover_image
			button.capture(game.main.fife.pychan.tools.callbackWithArguments(self.load_tab, index))
			if tab.name in callbacks:
				tab.widget.mapEvents(callbacks[tab.name])
		self.widget.findChild(name='content').addChild(self.tabs[self.widget.active].widget)
		self.tabs[self.widget.active].update(self.object)
		self.widget.findChild(name='content').adaptLayout()

	def load_tab(self, id):
		"""Loads a tab.
		@var id: int for the self.tabs list to get the tab."""
		tab1 = self.widget.findChild(name=(str(id)))
		contentarea = self.widget.findChild(name='content')
		contentarea.removeChild(self.tabs[self.widget.active].widget)
		self.tabs[id].update(self.object)
		contentarea.addChild(self.tabs[id].widget)
		contentarea.adaptLayout()
		self.widget.active = id

	def _update_active(self):
		self.tabs[self.widget.active].update(self.object)

	def show(self):
		"""Shows the widget."""
		self.widget.show()
		self.object.addChangeListener(self._update_active)

	def hide(self):
		"""Hides the widget."""
		self.widget.hide()
		self.object.removeChangeListener(self._update_active)

class Tab(object):
	"""Used to create tabs, stores the widget and needed buttons, that are used by the TabWidget, to display tabs.
	@var name: str used to identify the tab for callbacks for example
	@var button_up/down/hover_image: str file used for the up/down/hover effekt on the tab button for this tab
	@var xml: str xml that is to be loaded."""
	def __init__(self, name, xml, button_up_image, button_down_image, button_hover_image):
		self.name = name
		self.widget = game.main.fife.pychan.loadXML(xml)
		self.widget.stylize('menu')
		self.up_image = str(button_up_image)
		self.down_image = str(button_down_image)
		self.hover_image = str(button_hover_image)

	def update(self, instance):
		"""Updates all labels on the widget with text taken from instances var.
		E.g.: You have a label name='foo', update() will look if instance has
		the attribute foo and if yes, use its value."""
		if instance is not None:
			labels = self.get_named_widgets(pychan.widgets.Label)
			for label in labels:
				if hasattr(instance, label.name):
					label.text = str(getattr(instance, label.name))
			inventorys = self.get_named_widgets(Inventory)
			for inv in inventorys:
				if hasattr(instance, inv.name):
					inv.inventory = getattr(instance, inv.name)
			self.widget._recursiveResizeToContent()

	def get_named_widgets(self, widget_class):
		"""Gets all widget of a certain widget class from the tab. (e.g. pychan.widgets.Label for all labels)"""
		children = []
		def _find_named_widget(widget):
			if widget.name != widget.DEFAULT_NAME and isinstance(widget, widget_class):
				children.append(widget)
		self.widget.deepApply(_find_named_widget)
		return children
