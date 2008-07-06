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

from navigationtool import NavigationTool
from selectiontool import SelectionTool
from game.command.building import Tear

import fife
import game.main

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class TearingTool(NavigationTool):
	"""@param building_id: rowid of the selected building type"
	@param player_id: player id of the player that builds the building
	@param ship: If building from a ship, restrict to range of ship
	@param settle: bool Tells the building tool if a new settlement is created. Default: False
	"""

	def begin(self):
		super(TearingTool, self).begin()
		self.coords = None
		self.selected = []
		self.oldedges = None
		game.main.onEscape = self.onEscape

	def end(self):
		game.main.onEscape = lambda : None
		super(TearingTool, self).end()

	def mouseDragged(self, evt):
		coords = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		self._mark(self.coords, (int(coords.x + 0.5), int(coords.y + 0.5)))
		evt.consume()

	def mouseMoved(self,  evt):
		super(TearingTool, self).mouseMoved(evt)
		coords = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		self._mark((int(coords.x + 0.5), int(coords.y + 0.5)))
		evt.consume()

	def onEscape(self):
		self._mark()
		game.main.session.cursor = SelectionTool()

	def mouseReleased(self,  evt):
		if fife.MouseEvent.LEFT == evt.getButton():
			coords = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			self._mark(self.coords, (int(coords.x + 0.5), int(coords.y + 0.5)))
			for i in self.selected:
				game.main.session.manager.execute(Tear(i))
			game.main.session.cursor = SelectionTool()
			evt.consume()

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.onEscape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			coords = game.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			self.coords = (int(coords.x + 0.5), int(coords.y + 0.5))
			self._mark(self.coords)
		else:
			return
		evt.consume()

	def _mark(self, *edges):
		if len(edges) == 1:
			edges = (edges[0], edges[0])
		elif len(edges) == 2:
			edges = ((min(edges[0][0], edges[1][0]), min(edges[0][1], edges[1][1])), (max(edges[0][0], edges[1][0]), max(edges[0][1], edges[1][1])))
		else:
			edges = None
		if self.oldedges != edges or edges is None:
			for i in self.selected:
				game.main.session.view.renderer['InstanceRenderer'].removeColored(i._instance)
			self.selected = []
			self.oldedges = edges
		if edges is not None:
			for x in xrange(edges[0][0], edges[1][0] + 1):
				for y in xrange(edges[0][1], edges[1][1] + 1):
					b = game.main.session.world.get_building(x,y)
					if b is not None and b not in self.selected:
						self.selected.append(b)
			for i in self.selected:
				game.main.session.view.renderer['InstanceRenderer'].addColored(i._instance, 255, 255, 255)
