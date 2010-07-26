# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from fife import fife
import horizons.main

from cursortool import CursorTool
from horizons.util import Point

class NavigationTool(CursorTool):
	"""Navigation Class to process mouse actions ingame"""
	def __init__(self, session):
		super(NavigationTool, self).__init__(session)
		self.lastScroll = [0, 0]
		self.lastmoved = fife.ExactModelCoordinate()
		self.middle_scroll_active = False

		class CmdListener(fife.ICommandListener): pass
		self.cmdlist = CmdListener()
		horizons.main.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

	def end(self):
		horizons.main.fife.eventmanager.removeCommandListener(self.cmdlist)
		self.session.view.autoscroll(-self.lastScroll[0], -self.lastScroll[1])
		super(NavigationTool, self).end()

	def mousePressed(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			return # deactivated because of bugs (see #582)
			self.session.view.scroll(-self.lastScroll[0], -self.lastScroll[1])
			self.lastScroll = [evt.getX(), evt.getY()]
			self.middle_scroll_active = True

	def mouseReleased(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			return # deactivated because of bugs (see #582)
			self.lastScroll = [0, 0]
			CursorTool.mouseMoved(self, evt)
			self.middle_scroll_active = False

	# drag ingamemap via MIDDLE mouse button
	def mouseDragged(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			return # deactivated because of bugs (see #582)
			self.session.view.scroll(self.lastScroll[0] - evt.getX(), self.lastScroll[1] - evt.getY())
			self.lastScroll = [evt.getX(), evt.getY()]
		else:
			# Else the event will mistakenly be delegated if the left mouse button is hit while
			# scrolling using the middle mouse button
			if not self.middle_scroll_active:
				NavigationTool.mouseMoved(self, evt)

	# return new mouse position after moving
	def mouseMoved(self, evt):
		if not self.session.world.inited:
			return

		mousepoint = fife.ScreenPoint(evt.getX(), evt.getY())

		# Status menu update
		current = self.session.view.cam.toMapCoordinates(mousepoint, False)
		if abs((current.x-self.lastmoved.x)**2+(current.y-self.lastmoved.y)**2) >= 4**2:
			self.lastmoved = current
			island = self.session.world.get_island(Point(int(round(current.x)), int(round(current.y))))
			if island:
				settlement = island.get_settlement(Point(int(round(current.x)), int(round(current.y))))
				if settlement:
					self.session.ingame_gui.resourceinfo_set(settlement)
				else:
					self.session.ingame_gui.resourceinfo_set(None)
			else:
				self.session.ingame_gui.resourceinfo_set(None)
		# Mouse scrolling
		old = self.lastScroll
		new = [0, 0]
		if mousepoint.x < 5:
			new[0] -= 5 - mousepoint.x
		elif mousepoint.x >= (self.session.view.cam.getViewPort().right()-5):
			new[0] += 6 + mousepoint.x - self.session.view.cam.getViewPort().right()
		if mousepoint.y < 5:
			new[1] -= 5 - mousepoint.y
		elif mousepoint.y >= (self.session.view.cam.getViewPort().bottom()-5):
			new[1] += 6 + mousepoint.y - self.session.view.cam.getViewPort().bottom()
		new = [new[0] * 10, new[1] * 10]
		if new[0] != old[0] or new[1] != old[1]:
			self.session.view.autoscroll(new[0]-old[0], new[1]-old[1])
			self.lastScroll = new	

	# move up mouse wheel = zoom in
	def mouseWheelMovedUp(self, evt):
		self.session.view.zoom_in()
		evt.consume()

	# move down mouse wheel = zoom out
	def mouseWheelMovedDown(self, evt):
		self.session.view.zoom_out()
		evt.consume()

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_APP_ICONIFIED or command.getCommandType() == fife.CMD_INPUT_FOCUS_LOST:
			old = self.lastScroll
			self.session.view.autoscroll(-old[0], -old[1])
			self.lastScroll = [0, 0]
