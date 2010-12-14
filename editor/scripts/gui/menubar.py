# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

from fife.extensions.pychan import widgets
from fife.extensions.pychan.tools import callbackWithArguments as cbwa

import scripts.events
import scripts.gui.action
from action import Action, ActionGroup
from fife.fife import Color
from fife.extensions import fife_timer

MENU_ICON_SIZE = 24

class MenuBar(widgets.HBox):
	def __init__(self, *args, **kwargs):
		super(MenuBar, self).__init__(*args, **kwargs)
		
		self.menulist = []
		self._buttonlist = []
		self.gui = None
		self._buildGui()
		
		self._timer = fife_timer.Timer(500, self._autoHideMenu)
		self._timer.start()
			
	def _buildGui(self):
		if self.gui is not None:
			self.removeChild(self.gui)
			self._buttonlist = []
			
		self.gui = widgets.HBox()
		for i, menu in enumerate(self.menulist):
			button = widgets.Button(name=menu.name, text=menu.name)
			button.hexpand = 0
			button.capture(cbwa(self._showMenu, i))
			self._buttonlist.append(button)
			self.gui.addChild(button)
			
		self.gui.addSpacer(widgets.Spacer())
		
		self.addChild(self.gui)
		
	def _showMenu(self, i):
		if self.menulist[i].isVisible():
			self.menulist[i].hide()
			return
	
		# Hide all menus
		for m in self.menulist:
			m.hide()
	
		menu = self.menulist[i]
		button = self._buttonlist[i]
		
		menu.x = 0
		menu.y = button.height

		# Get absolute position of button
		parent = button
		while parent is not None:
			menu.x += parent.x
			menu.y += parent.y
			parent = parent.parent

		menu.show()
		
	def _autoHideMenu(self):
		for i, m in enumerate(self.menulist):
			if not m.isVisible(): continue
			if self._buttonlist[i].real_widget.isFocused(): continue
			if self._isMenuFocused(m) is False:
				m.hide()
		
	def _isMenuFocused(self, widget):
		if widget.real_widget.isFocused(): return True
		if hasattr(widget, "children"):
			for c in widget.children:
				if self._isMenuFocused(c):
					return True
		return False
		
	def addMenu(self, menu):
		if menu is not None and self.menulist.count(menu) <= 0:
			self.menulist.append(menu)
		self._buildGui()
		
	def insertMenu(self, menu, beforeMenu):
		try:
			i = self.menulist.index(beforeMenu)
			self.menulist.insert(i, menu)
			self._buildGui()
			
		except ValueError:
			print "MenuBar::insertMenu:", "MenuBar does not contain specified menu."
			return
			
	def insertMenuAt(self, menu, index):
		self.menulist.insert(index, menu)
		self._buildGui()

	def removeMenu(self, menu):
		self.menulist.remove(menu)
		self._buildGui()
		
	def clear(self):
		self.menulist = []
		self._buildGui()

class Menu(widgets.VBox):
	def __init__(self, name=u"", icon=u"", min_width=100, min_height=15, margins=(2,2), *args, **kwargs):
		super(Menu, self).__init__(*args, **kwargs)
		self.min_width=min_width
		self.min_height=min_height
		self.margins=margins
		
		self.name = name
		self.icon = icon
		
		self._actions = []
		self._actionbuttons = []
		
		self._update()

	def addSeparator(self, separator=None): 
		self.insertSeparator(separator, len(self._actions))

	def addAction(self, action):
		self.insertAction(action, len(self._actions))
		
	def removeAction(self, action):
		self._actions.remove(action)
		
		actions = [action]
		if isinstance(action, ActionGroup):
			actions = action.getActions()
			scripts.gui.action.changed.disconnect(self._updateActionGroup, sender=action)

		for a in actions:
			for b in self._actionbuttons[:]:
				if a == b.action:
					self.removeChild(b)
					self._actionbuttons.remove(b)
			
		self.adaptLayout(False)
		
	def hasAction(self, action):
		for a in self._actions:
			if a == action: return True
		return False
		
	def insertAction(self, action, position=0, before=None):
		if self.hasAction(action):
			print "Action already added to toolbar"
			return

		if before is not None:
			position = self._actions.index(before)

		self._actions.insert(position, action)
		self._insertButton(action, position)
		
	def _updateActionGroup(self, sender):
		position = self._actions.index(sender)
		self.removeAction(sender)
		self.insertAction(sender, position)
		self.adaptLayout(False)
		
	def _insertButton(self, action, position):
		actions = [action]
		if isinstance(action, ActionGroup):
			actions = action.getActions()
			scripts.gui.action.changed.connect(self._updateActionGroup, sender=action)

		if position >= 0:
			actions = reversed(actions)
		
		# Action groups are counted as one action, add the hidde number of actions to position
		for i in range(position):
			if isinstance(self._actions[i], ActionGroup):
				position += len(self._actions[i].getActions()) - 1

		for a in actions:
			button = MenuButton(a, name=a.text)
			self.insertChild(button, position)
			self._actionbuttons.insert(position, button)
		
	def insertSeparator(self, separator=None, position=0, before=None): 
		if separator==None:
			separator = Action(separator=True)
		self.insertAction(separator, position, before)
		
	def clear(self):
		self.removeAllChildren()
		self._actions = []
		
		for i in reversed(range(len(self._actionbuttons))):
			self._actionbuttons[i].removeEvents()
		self._actionbuttons = []

	def _update(self):
		actions = self._actions
		
		self.clear()
		
		for action in actions:
			self.addAction(action)

		self.adaptLayout(False)
		
	def show(self):
		self._update()
		super(Menu, self).show()
		
class MenuButton(widgets.HBox):
	def __init__(self, action, **kwargs):
		self._action = action
		self._widget = None
		
		super(MenuButton, self).__init__(**kwargs)
		
		self.update()

		self.initEvents()
	
	def initEvents(self):
		# Register eventlisteners
		self.capture(self._showTooltip, "mouseEntered")
		self.capture(self._hideTooltip, "mouseExited")
		
		scripts.gui.action.changed.connect(self._actionChanged, sender=self._action)
	
	def removeEvents(self):
		# Remove eventlisteners
		self.capture(None, "mouseEntered")
		self.capture(None, "mouseExited")
		
		scripts.gui.action.changed.disconnect(self.update, sender=self._action)
	
	def setAction(self, action):
		self.removeEvents()
		
		self._action = action
		self.update()
		self.adaptLayout(False)
		
		self.initEvents()
	
	def getAction(self):
		return self._action
	action = property(getAction, setAction)
	
	def _showTooltip(self):
		if self._action is not None and self._action.helptext != "":
			scripts.editor.getEditor().getStatusBar().showTooltip(self._action.helptext)
			
	def _hideTooltip(self):
		scripts.editor.getEditor().getStatusBar().hideTooltip()
		
	def _actionChanged(self):
		self.update()
		self.adaptLayout(False)
		
	def update(self):
		""" Sets up the button widget """
		if self._widget != None:
			self.removeChild(self._widget)
			self._widget = None
			
		if self._action is None:
			return
			
		widget = None
		icon = None
		text = None

		if self._action.isSeparator():
			widget = widgets.HBox()
			widget.base_color += Color(8, 8, 8)
			widget.min_size = (2, 2)
		else:
			hasIcon = len(self._action.icon) > 0
			
			if self._action.isCheckable():
				text = widgets.ToggleButton(text=self._action.text)
				text.toggled = self._action.isChecked()
				text.hexpand = 1
			else:
				text = widgets.Button(text=self._action.text)
			text.min_size = (1, MENU_ICON_SIZE)
			text.max_size = (1000, MENU_ICON_SIZE)
			text.capture(self._action.activate)

			if hasIcon:
				if self._action.isCheckable():
					icon = widgets.ToggleButton(hexpand=0, up_image=self._action.icon,down_image=self._action.icon,hover_image=self._action.icon,offset=(1,1))
					icon.toggled = self._action.isChecked()
				else:
					icon = widgets.ImageButton(hexpand=0, up_image=self._action.icon,down_image=self._action.icon,hover_image=self._action.icon,offset=(1,1))

			else:
				if self._action.isCheckable():
					icon = widgets.ToggleButton(hexpand=0, offset=(1,1))
					icon.toggled = self._action.isChecked()
				else:
					icon = widgets.Button(text=u"", hexpand=0, offset=(1,1))
				
			icon.min_size = icon.max_size = (MENU_ICON_SIZE, MENU_ICON_SIZE)
			icon.capture(self._action.activate)
			
			widget = widgets.HBox()
			widget.addChild(icon)
			widget.addChild(text)
			
		widget.position_technique = "left:center"
		widget.hexpand = 1
		widget.vexpand = 0
		
		self._widget = widget
		self.addChild(self._widget)
		