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
from panel import Panel
from faketabwidget import FakeTabWidget
from resizablebase import ResizableBase

class DockArea(widgets.VBox, ResizableBase):
	def __init__(self, side, resizable=True, *args, **kwargs):
		widgets.VBox.__init__(self, margins=(0,0,0,0), *args, **kwargs)
		ResizableBase.__init__(self, *args, **kwargs)
		
		self.cursor_id = 0
		self.cursor_type = 0
		
		self.vexpand=0
		self.hexpand=0
		
		self.side = side
		self.resizable_top = (side == "bottom")
		self.resizable_left = (side == "right")
		self.resizable_right = (side == "left")
		self.resizable_bottom = (side == "top")
		
		self.gui = None
		
		self.buildGui()
		self.tabwidgets = []
		self.panels = []
		
	def getDockLocation(self, x, y):
		placeAfter = None
		placeBefore = None
		placeIn = None
		
		if x >= 0 and y >= 0:
			# See if widget was dropped on a tabwidget
			for tabwidget in self.tabwidgets:
				absX, absY = tabwidget.getAbsolutePos()
					
				if absX <= x and absY <= y \
						and absX+tabwidget.width >= x and absY+tabwidget.height >= y:
					# Check if the user tried to place it in front, or after this widget
					if self.side == "left" or self.side == "right":
						if y < absY+10:
							placeBefore = tabwidget
						elif y > absY+tabwidget.height-10:
							placeAfter = tabwidget
					else:
						if x < absX+10:
							placeBefore = tabwidget
						elif x > absX+tabwidget.width-10:
							placeAfter = tabwidget
					if placeAfter is None and placeBefore is None:
						placeIn = tabwidget
					break
					
		return (placeIn, placeBefore, placeAfter)
		
	def dockChild(self, child, x, y):
		for panel in self.panels:
			if panel[0] == child:
				return
	
		child.dockarea = self
		child.setDocked(True)
		
		placeIn, placeBefore, placeAfter = self.getDockLocation(x, y)
	
		if placeIn is None:
			tabwidget = FakeTabWidget(resizable=True)
			tabwidget.hexpand=1
			tabwidget.vexpand=1
		
			if self.side == "left" or self.side == "right":
				tabwidget.resizable_bottom = True
			else:
				tabwidget.resizable_right = True
			self.tabwidgets.append(tabwidget)
			
			if placeBefore:
				self.gui.insertChildBefore(tabwidget, placeBefore)
			elif placeAfter:
				self.gui.insertChild(tabwidget, self.gui.children.index(placeAfter)+1)
			else:
				self.gui.addChild(tabwidget)
		else:
			tabwidget = placeIn

		tab = tabwidget.addTab(child, child.title)
		self.panels.append( (child, tabwidget) )
		
		def undock(event):
			if event.getButton() != 2: # Right click
				return
				
			self.undockChild(child)
			
		tab[2].capture(undock, "mouseClicked")
		self.adaptLayout()
		
	def undockChild(self, child, childIsCaller=False):
		tabwidget = None
		for panel in self.panels:
			if panel[0] == child:
				tabwidget = panel[1]
				self.panels.remove(panel)
				break
		else:
			return
			
		tabwidget.removeTab(child)
		if childIsCaller is False:
			child.setDocked(False)
		
		if len(tabwidget.tabs) <= 0:
			self.gui.removeChild(tabwidget)
			self.tabwidgets.remove(tabwidget)
			
			# This stops a guichan exception when a widget with modul focus gets focused.
			# It is not pretty, but crashes aren't pretty either
			tabwidget.__del__()
			del tabwidget
				
		self.adaptLayout()
		
	def buildGui(self):
		if self.gui:
			self.removeChild(self.gui)
		
		if self.side == "left" or self.side == "right":
			self.gui = widgets.VBox()
		else:
			self.gui = widgets.HBox()
			
		self.gui.vexpand = 1
		self.gui.hexpand = 1
		
		self.addChild(self.gui)
	
	def mouseReleased(self, event):
		if self._resize:
			if self._rLeft or self._rRight:
				# Resize children
				for child in self.gui.findChildren(parent=self.gui):
					child.min_size = (self.width, child.min_size[1])
					child.max_size = (self.width, child.max_size[1])
					
			if self._rTop or self._rBottom:
				# Resize children
				for child in self.gui.findChildren(parent=self.gui):
					child.min_size = (child.min_size[0], self.height)
					child.max_size = (child.max_size[0], self.height)
					
			self.gui.max_size = (self.width, self.height)
			
			ResizableBase.mouseReleased(self, event)
			self.min_size = (0,0) # Override changes done in ResizableBase
		
		#FIXME: This is a little bit of a hack to fix Ticket #444
		self.adaptLayout()
				