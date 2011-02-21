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
import scripts.editor
from fife import fife
from resizablebase import ResizableBase

class Panel(widgets.Window, ResizableBase):
	""" Panel is a window which can be resized and docked. 
	"""
	def __init__(self, dockable=True, *args, **kwargs):
		widgets.Window.__init__(self, *args, **kwargs)
		ResizableBase.__init__(self, *args, **kwargs)
	
		self.dockable = dockable
		self._movable = self.real_widget.isMovable()
		self._resizable = self.resizable

		self._floating = True
		self._titlebarheight = 16
		
		self.dockarea = None
		
		self._editor = scripts.editor.getEditor()
		
		self._panel_startPos = (0, 0)
		
	def setDocked(self, docked):
		""" 
		Dock or undock the panel
		
		setDocked(True) will disable resizing and moving
		of this panel, but will not dock it in a dockarea.
		
		setDocked(False) will enable resizing and moving.
		If this panel is docked in a dockarea or widget,
		it will undock itself. The new position will be 
		offset by panelSize.
		"""
		if self.dockable is False:
			return
		
		if docked is True and self._floating == True:
			self._floating = False
			self.real_widget.setTitleBarHeight(0)
			self.real_widget.setMovable(False)
			self._movable = False
			self.resizable = False
				
		elif docked is False and self._floating is False:			
			self._floating = True
			self._movable = True
			self.real_widget.setMovable(True)
			self.resizable = self._resizable
			
			# Since x and y coordinates are reset if the widget gets hidden,
			# we need to store them
			absX, absY = self.getAbsolutePos()
			
			# Remove from parent widget
			if self.dockarea is not None:
				# Use dockareas undock method
				self.dockarea.undockChild(self, True)
				self.dockarea = None

			elif self.parent is not None:
				# Force removal
				widgetParent = self.parent
				widgetParent.removeChild(self)
				widgetParent.adaptLayout()
				self.hide()
				
			self.real_widget.setTitleBarHeight(self._titlebarheight)
			self.show()
			
			# Slighly offset toolbar when undocking
			mw = pychan.internal.screen_width() / 2
			mh = pychan.internal.screen_height() / 2
			if absX < mw:
				self.x = absX + self._titlebarheight
			else:
				self.x = absX - self._titlebarheight
			if absY < mh:
				self.y = absY + self._titlebarheight
			else:
				self.y = absY - self._titlebarheight

	def isDocked(self):
		""" Returns true if the panel is docked """
		return self._floating == False
		
	def mousePressed(self, event):
		if self.resizable is False:
			return
			
		self._panel_startPos = (self.x, self.y)
		
		ResizableBase.mousePressed(self, event)
		if self._rLeft or self._rRight or self._rTop or self._rBottom:
			self._movable = self.real_widget.isMovable()
			self.real_widget.setMovable(False) # Don't let guichan move window while we resize
			
	def mouseDragged(self, event):
		self._dragging = True
		if self._resize is False and self.isDocked() is False:
			if (self.x, self.y) == self._panel_startPos:
				return
			mouseX = self.x+event.getX()
			mouseY = self.y+event.getY()
			self._editor.getDockAreaAt(mouseX, mouseY, True)
		else:
			ResizableBase.mouseDragged(self, event)
	
	def mouseReleased(self, event):	
		didMove = False
		if (self.x, self.y) != self._panel_startPos:
			didMove = True
		
		# Resize/move done
		self.real_widget.setMovable(self._movable)
		
		if self._resize:
			ResizableBase.mouseReleased(self, event)
		elif self._movable and didMove:
			mouseX = self.x+event.getX()
			mouseY = self.y+event.getY()
			
			dockArea = self._editor.getDockAreaAt(mouseX, mouseY)
			if dockArea is not None:
				self._editor.dockWidgetTo(self, dockArea, mouseX, mouseY)
		
	def hide(self):
		""" Hides the panel. If the widget is docked, it is first undocked """
		if self.isDocked():
			self.setDocked(False)
		widgets.Window.hide(self)
		
	def show(self):
		""" Show the panel. """
		if self.isDocked():
			return
		widgets.Window.show(self)
				
	
# Register widget to pychan
if 'Panel' not in widgets.WIDGETS:
	widgets.WIDGETS['Panel'] = Panel
		