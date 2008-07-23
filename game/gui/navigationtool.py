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

from cursortool import CursorTool
import game.main
import fife

class NavigationTool(CursorTool):
	"""The Selectiontool is used to select instances on the game screen.
	@param game: the main game Instance
	"""
	def begin(self):
		super(NavigationTool, self).begin()
		self.lastScroll = [0, 0]
		self.lastmoved = fife.ExactModelCoordinate()
		self.debug = False
		self.middle_scroll_active = False

		#ugly but works o_O
		class CmdListener(fife.ICommandListener): pass
		self.cmdlist = CmdListener()
		game.main.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

	def end(self):
		game.main.fife.eventmanager.removeCommandListener(self.cmdlist)
		game.main.session.view.autoscroll(-self.lastScroll[0], -self.lastScroll[1])
		super(NavigationTool, self).end()

	def mousePressed(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			game.main.session.view.autoscroll(-self.lastScroll[0], -self.lastScroll[1])
			self.lastScroll = [evt.getX(), evt.getY()]
			self.middle_scroll_active = True

	def mouseReleased(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			self.lastScroll = [0, 0]
			CursorTool.mouseMoved(self, evt)
			self.middle_scroll_active = False

	def mouseDragged(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			game.main.session.view.scroll(self.lastScroll[0] - evt.getX(), self.lastScroll[1] - evt.getY())
			self.lastScroll = [evt.getX(), evt.getY()]
		else:
			# Else the event will mistakenly be delegated if the left mouse button is hit while
			# scrolling using the middle mouse button
			if not self.middle_scroll_active:
				NavigationTool.mouseMoved(self, evt)

	def mouseMoved(self, evt):
		mousepoint = fife.ScreenPoint(evt.getX(), evt.getY())
		# Status menu update
		current = game.main.session.view.cam.toMapCoordinates(mousepoint, False)
		#if self.debug:
		#	print 'pos: x:', int(current.x + 0.5), 'y:', int(current.y + 0.5)
		if abs((current.x-self.lastmoved.x)**2+(current.y-self.lastmoved.y)**2) >= 4**2:
			self.lastmoved = current
			island = game.main.session.world.get_island(int(current.x + 0.5), int(current.y + 0.5))
			if island:
				settlements = island.get_settlements(int(current.x + 0.5), int(current.y + 0.5))
				if len(settlements) > 0:
					game.main.session.ingame_gui.cityinfo_set(settlements.pop())
				else:
					game.main.session.ingame_gui.cityinfo_set(None)
			else:
				game.main.session.ingame_gui.cityinfo_set(None)
		# Mouse scrolling
		old = self.lastScroll
		new = [0, 0]
		if mousepoint.x < 5:
			new[0] -= 5 - mousepoint.x
		elif mousepoint.x >= (game.main.session.view.cam.getViewPort().right()-5):
			new[0] += 6 + mousepoint.x - game.main.session.view.cam.getViewPort().right()
		if mousepoint.y < 5:
			new[1] -= 5 - mousepoint.y
		elif mousepoint.y >= (game.main.session.view.cam.getViewPort().bottom()-5):
			new[1] += 6 + mousepoint.y - game.main.session.view.cam.getViewPort().bottom()
		new = [new[0] * 10, new[1] * 10]
		if new[0] != old[0] or new[1] != old[1]:
			game.main.session.view.autoscroll(new[0]-old[0], new[1]-old[1])
			self.lastScroll = new

	def mouseWheelMovedUp(self, evt):
		game.main.session.view.zoom_in()
		evt.consume()

	def mouseWheelMovedDown(self, evt):
		game.main.session.view.zoom_out()
		evt.consume()

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_APP_ICONIFIED or command.getCommandType() == fife.CMD_INPUT_FOCUS_LOST:
			old = self.lastScroll
			game.main.session.view.autoscroll(-old[0], -old[1])
			self.lastScroll = [0, 0]
