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

from fife.extensions import pychan
from fife.extensions.pychan import widgets

import scripts.events
import action
import scripts.editor
from action import Action, ActionGroup
from fife.fife import Color
from panel import Panel
from resizablebase import ResizableBase

class ToolBar(Panel):
	ORIENTATION = {
			"Horizontal"	: 0,
			"Vertical"		: 1
		}

	BUTTON_STYLE = {
				"IconOnly"			: 0,
				"TextOnly"			: 1,
				"TextUnderIcon"		: 2,
				"TextBesideIcon"	: 3
			}

	def __init__(self, button_style=0, panel_size=27, orientation=0, *args, **kwargs):
		super(ToolBar, self).__init__(resizable=False, *args, **kwargs)
		
		self._actions = []
		self._actionbuttons = []
		self._button_style = 0
		self._panel_size = panel_size
		self.gui = None
		
		self._orientation = orientation
		self._button_style = button_style

		self._updateToolbar()
		
		self.capture(self.mouseReleased, "mouseReleased", "toolbar")
		self.capture(self.mouseClicked, "mouseClicked", "toolbar")

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
					self.gui.removeChild(b)
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
		if isinstance(sender, ActionGroup):
			# Toolbar didn't properly handle events where
			# an action in actiongroup was removed
			self._updateToolbar()
		else:
			position = self._actions.index(sender)
			self.removeAction(sender)
			self.insertAction(sender, position)
			self.adaptLayout()
		
		
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
			button = ToolbarButton(a, button_style=self._button_style, name=a.text)
			self.gui.insertChild(button, position)
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
		
	def setButtonStyle(self, button_style):
		self._button_style = ToolBar.BUTTON_STYLE['IconOnly']
		for key, val in ToolBar.BUTTON_STYLE.iteritems():
			if val == button_style:
				self._button_style = button_style
				break

		self._updateToolbar()
		
	def getButtonStyle(self):
		return self._button_style
	button_style = property(getButtonStyle, setButtonStyle)
		
	def _updateToolbar(self):
		actions = self._actions
		
		self.clear()
		
		if self._orientation == ToolBar.ORIENTATION['Vertical']:
			self.gui = widgets.VBox(min_size=(self._panel_size, self._panel_size))
		else:
			self.gui = widgets.HBox(min_size=(self._panel_size, self._panel_size))
		self.addChild(self.gui)
		
		for action in actions:
			self.addAction(action)

		self.adaptLayout()
		
	def setOrientation(self, orientation):
		if orientation == ToolBar.ORIENTATION['Vertical']:
			self._orientation = ToolBar.ORIENTATION['Vertical']
			self._max_size = (self._panel_size, 5000)
		else:
			self._orientation = ToolBar.ORIENTATION['Horizontal']
			self._max_size = (5000, self._panel_size)
		self._orientation = orientation
		
		self._updateToolbar()
		
	def getOrientation(self):
		return self._orientation
	orientation = property(getOrientation, setOrientation)
		
	def setPanelSize(self, panel_size):
		self._panel_size = panel_size
		self.min_size = self.gui.min_size = (self._panel_size, self._panel_size)
		self.setOrientation(self._orientation)
		
	def getPanelSize(self):
		return self._panel_size
	panel_size = property(getPanelSize, setPanelSize)
			
	def mouseClicked(self, event):
		if event.getButton() == 2: # Right click
			if self.isDocked():
				self.setDocked(False)
				event.consume()
			
	def mouseDragged(self, event):
		if self._resize is False and self.isDocked() is False:
			mouseX = self.x+event.getX()
			mouseY = self.y+event.getY()
			self._editor.getToolbarAreaAt(mouseX, mouseY, True)
		else:
			ResizableBase.mouseDragged(self, event)
	
	def mouseReleased(self, event):
		# Resize/move done
		self.real_widget.setMovable(self._movable)
		
		if self._resize:
			ResizableBase.mouseReleased(self, event)
		elif self._movable:
			mouseX = self.x+event.getX()
			mouseY = self.y+event.getY()
		
			dockArea = self._editor.getToolbarAreaAt(mouseX, mouseY)
			if dockArea is not None:
				self._editor.dockWidgetTo(self, dockArea, mouseX, mouseY)
			
class ToolbarButton(widgets.VBox):
	def __init__(self, action, button_style=0, **kwargs):
		self._action = action
		self._widget = None
		
		super(ToolbarButton, self).__init__(**kwargs)
		
		self.setButtonStyle(button_style)
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
	
	def setButtonStyle(self, button_style):
		self._button_style = ToolBar.BUTTON_STYLE['IconOnly']
		for key, val in ToolBar.BUTTON_STYLE.iteritems():
			if val == button_style:
				self._button_style = button_style
				break
		
	def getButtonStyle(self):
		return self._button_style
	button_style = property(getButtonStyle, setButtonStyle)
	
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
			widget = widgets.VBox()
			widget.base_color += Color(8, 8, 8)
			widget.min_size = (2, 2)
		else:
			if self._button_style != ToolBar.BUTTON_STYLE['TextOnly'] and len(self._action.icon) > 0:
				if self._action.isCheckable():
					icon = widgets.ToggleButton(hexpand=0, up_image=self._action.icon,down_image=self._action.icon,hover_image=self._action.icon,offset=(1,1))
					icon.toggled = self._action.isChecked()
				else:
					icon = widgets.ImageButton(hexpand=0, up_image=self._action.icon,down_image=self._action.icon,hover_image=self._action.icon,offset=(1,1))
				icon.capture(self._action.activate)
				
			if self._button_style != ToolBar.BUTTON_STYLE['IconOnly'] or len(self._action.icon) <= 0:
				if self._action.isCheckable():
					text = widgets.ToggleButton(hexpand=0, text=self._action.text,offset=(1,1))
					text.toggled = self._action.isChecked()
				else:
					text = widgets.Button(text=self._action.text)
				text.capture(self._action.activate)
			
			if self._button_style == ToolBar.BUTTON_STYLE['TextOnly'] or len(self._action.icon) <= 0:
				widget = text
				
			elif self._button_style == ToolBar.BUTTON_STYLE['TextUnderIcon']:
				widget = widgets.VBox()
				icon.position_technique = "center:top"
				text.position_technique = "center:bottom"
				widget.addChild(icon)
				widget.addChild(text)
				
			elif self._button_style == ToolBar.BUTTON_STYLE['TextBesideIcon']:
				widget = widgets.HBox()
				widget.addChild(icon)
				widget.addChild(text)
					
			else:
				widget = icon
			
		widget.position_technique = "left:center"
		widget.hexpand = 0
		
		self._widget = widget
		self.addChild(self._widget)
		