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
	def __init__(self):
		super(NavigationTool, self).__init__()
		self.lastScroll = [0, 0]
		self.lastmoved = fife.ExactModelCoordinate()

	def __del__(self):
		super(NavigationTool, self).__del__()
		game.main.session.view.autoscroll(-self.lastScroll[0], -self.lastScroll[1])
		print 'deconstruct',self

	def mouseMoved(self, evt):
		mousepoint = fife.ScreenPoint(evt.getX(), evt.getY())
		# Status menu update
		current = game.main.session.view.cam.toMapCoordinates(mousepoint, False)
		if abs((current.x-self.lastmoved.x)**2+(current.y-self.lastmoved.y)**2) >= 4**2:
			self.lastmoved = current
			island = game.main.session.world.get_island(int(current.x), int(current.y))
			if island:
				settlement = island.get_settlement_at_position(int(current.x), int(current.y))
				if settlement:
					game.main.session.ingame_gui.status_set('wood', str(settlement.inventory['wood']))
					game.main.session.ingame_gui.status_set('tools', str(settlement.inventory['tools']))
					game.main.session.ingame_gui.status_set('bricks', str(settlement.inventory['bricks']))
					game.main.session.ingame_gui.status_set('food', str(settlement.inventory['food']))
					game.main.session.ingame_gui.gui['status'].show()
				else:
					game.main.session.ingame_gui.gui['status'].hide()
			else:
				game.main.session.ingame_gui.gui['status'].hide()
		# Mouse scrolling
		old = self.lastScroll
		new = [0, 0]
		if mousepoint.x < 50:
			new[0] -= 50 - mousepoint.x
		elif mousepoint.x >= (game.main.session.view.cam.getViewPort().right()-50):
			new[0] += 51 + mousepoint.x - game.main.session.view.cam.getViewPort().right()
		if mousepoint.y < 50:
			new[1] -= 50 - mousepoint.y
		elif mousepoint.y >= (game.main.session.view.cam.getViewPort().bottom()-50):
			new[1] += 51 + mousepoint.y - game.main.session.view.cam.getViewPort().bottom()
		if new[0] != old[0] or new[1] != old[1]:
			game.main.session.view.autoscroll(new[0]-old[0], new[1]-old[1])
			self.lastScroll = new

	def mouseWheelMovedUp(self, evt):
		game.main.session.view.zoom_in()
		evt.consume()

	def mouseWheelMovedDown(self, evt):
		game.main.session.view.zoom_out()
		evt.consume()
