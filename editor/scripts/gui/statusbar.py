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

class StatusBar(widgets.HBox):
	"""
	A basic widget which displays information of the current status of the program.
	
	Use the text property to set the text to be displayed. Use showTooltip() to display
	a temporary message.
	"""
	def __init__(self, text=u"", panel_size=25, *args, **kwargs):
		super(StatusBar, self).__init__(*args, **kwargs)
		self.min_size = (panel_size, panel_size)
		
		self._tooltip = None
		self._label = widgets.Label(text=text)
		self.addChild(self._label)
		
		self._text = u""
		self._tooltipDisplayed = False
	   
	def setText(self, text):
		""" Sets the text to be displayed whenever a tooltip isn't displayed """
		self._text = text
		if not self.isTooltipDisplayed():
			self._label.text = text
		
	def getText(self):
		return self._text
	text = property(getText, setText)

	def showTooltip(self, text):
		""" Shows a text which is visible until hideTooltip is called """
		self._label.text = text
		self._tooltipDisplayed = True
		
	def hideTooltip(self):
		""" Removes the text set by showTooltip. Whatever text previously set by setText is then displayed. """
		self._label.text = self._text
		self._tooltipDisplayed = False
		
	def isTooltipDisplayed(self):
		""" Returns true if tool tip is displayed """
		return self._tooltipDisplayed
