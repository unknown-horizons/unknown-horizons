# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import fife

class EventListenerBase(fife.IKeyListener, fife.ICommandListener, fife.IMouseListener,
	                fife.ConsoleExecuter, fife.IWidgetListener):
	def __init__(self, engine, regKeys=False, regCmd=False, regMouse=False, regConsole=False, regWidget=False):
		self.eventmanager = engine.getEventManager()
		
		fife.IKeyListener.__init__(self)
		if regKeys:
			self.eventmanager.addKeyListener(self)
		fife.ICommandListener.__init__(self)
		if regCmd:
			self.eventmanager.addCommandListener(self)
		fife.IMouseListener.__init__(self)
		if regMouse:
			self.eventmanager.addMouseListener(self)
		fife.ConsoleExecuter.__init__(self)
		if regConsole:
			engine.getGuiManager().getConsole().setConsoleExecuter(self)
		fife.IWidgetListener.__init__(self)
		if regWidget:
			self.eventmanager.addWidgetListener(self)
		
	
	def mousePressed(self, evt):
		pass
	def mouseReleased(self, evt):
		pass	
	def mouseEntered(self, evt):
		pass
	def mouseExited(self, evt):
		pass
	def mouseClicked(self, evt):
		pass
	def mouseWheelMovedUp(self, evt):
		pass	
	def mouseWheelMovedDown(self, evt):
		pass
	def mouseMoved(self, evt):
		pass
	def mouseDragged(self, evt):
		pass
	def keyPressed(self, evt):
		pass
	def keyReleased(self, evt):
		pass
	def onCommand(self, command):
		pass
	def onToolsClick(self):
		print "No tools set up yet"
	def onConsoleCommand(self, command):
		pass
	def onWidgetAction(self, evt):
		pass
