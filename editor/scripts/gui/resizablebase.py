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

from fife import fife
import scripts
from fife.extensions import pychan

class ResizableBase(object):
	def __init__(self, resizable=True, *args, **kwargs):
		self._engine = scripts.editor.getEditor().getEngine()
	
		self.resizable = resizable
		self.resizable_top = True
		self.resizable_left = True
		self.resizable_right = True
		self.resizable_bottom = True
		
		self._resize = False
		
		self.capture(self.mouseEntered, "mouseEntered", "ResizableBase")
		self.capture(self.mouseExited, "mouseExited", "ResizableBase")
		self.capture(self.mouseMoved, "mouseMoved", "ResizableBase")
		self.capture(self.mouseDragged, "mouseDragged", "ResizableBase")
		self.capture(self.mousePressed, "mousePressed", "ResizableBase")
		self.capture(self.mouseReleased, "mouseReleased", "ResizableBase")
		
		self.cursor_id = 0
		self.cursor_type = 1
		
	
	def mouseEntered(self, event):
		# Save cursor id
		if self.resizable and self._resize is False:
			cursor = self._engine.getCursor()
			self.cursor_id = cursor.getId()
			self.cursor_type = cursor.getType()
		
	def mouseMoved(self, event):
		if self.resizable is False: 
			return
			
		# Hack to allow consuming mousemove events
		key = (event.getX(), event.getY())
		if _mousemoveevent.has_key( key ) is False:
			_mousemoveevent.clear()
			_mousemoveevent[key] = event
		elif _mousemoveevent[key].isConsumed():
			return
			
			
		titleheight = 0
		if hasattr(self.real_widget, "getTitleBarHeight"):
			titleheight = self.real_widget.getTitleBarHeight()

		cursor = self._engine.getCursor()
		
		left	= event.getX() < 5 and self.resizable_left
		right	= event.getX() > self.width-5 and self.resizable_right
		top		= event.getY() < 5 and self.resizable_top
		bottom	= event.getY() - titleheight > self.height-5 and self.resizable_bottom

		if left and top:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZENW)
		elif right and top:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZENE)
		elif left and bottom:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZESW)
		elif right and bottom:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZESE)
		elif left:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZEW)
		elif right:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZEE)
		elif top:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZEN)
		elif bottom:
			cursor.set(fife.CURSOR_NATIVE, fife.NC_RESIZES)
		else:
			cursor.set(self.cursor_type, self.cursor_id)
			return
			
		event.consume()
		_mousemoveevent[key].consume()
		
	def mouseExited(self, event):
		# Reset cursor to whatever it was before it entered this window
		if self.resizable and self._resize is False:
			cursor = self._engine.getCursor()
			cursor.set(self.cursor_type, self.cursor_id)
		
	def mouseDragged(self, event):
		if self.resizable and self._resize:
			diffX = event.getX()
			diffY = event.getY()
			
			# Resize horizontally
			if self._rLeft:
				self.x += diffX
				self.width -= diffX
			elif self._rRight:
				self.width = diffX

			# Resize vertically
			if self._rTop:
				self.y += diffY
				self.height -= diffY
			elif self._rBottom:
				titleheight = 0
				if hasattr(self.real_widget, "getTitleBarHeight"):
					titleheight = self.real_widget.getTitleBarHeight()
				self.height = diffY-titleheight

	def mousePressed(self, event):
		if self.resizable is False:
			return
			
		titleheight = 0
		if hasattr(self.real_widget, "getTitleBarHeight"):
			titleheight = self.real_widget.getTitleBarHeight()
			
		self._rLeft		= event.getX() < 5 and self.resizable_left
		self._rRight	= event.getX() > self.width-5 and self.resizable_right
		self._rTop		= event.getY() < 5 and self.resizable_top
		self._rBottom	= event.getY() - titleheight > self.height-5 and self.resizable_bottom
		
		if self._rLeft or self._rRight or self._rTop or self._rBottom:
			self._resize = True
			self.min_size = (30, 30)
			event.consume()
		
	def mouseReleased(self, event):
		if self._resize:
			self.min_size = (self.width, self.height)
			self.adaptLayout()
			event.consume()
			
			titleheight = 0
			if hasattr(self.real_widget, "getTitleBarHeight"):
				titleheight = self.real_widget.getTitleBarHeight()
		
			self._resize = False
			if event.getX() <= 0 or event.getX() >= self.width \
					or event.getY() <= 0 or event.getY() >= self.height+titleheight:
				self.mouseExited(event)
				
# Ugly hack to allow consumption of mousemove events
_mousemoveevent = {}

