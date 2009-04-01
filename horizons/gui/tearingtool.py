# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import fife

import horizons.main

from navigationtool import NavigationTool
from selectiontool import SelectionTool
from horizons.command.building import Tear
from horizons.world.building.storages import StorageBuilding

class TearingTool(NavigationTool):
	"""
	Represents a dangling tool after a building was selected from the list.
	Builder visualizes if and why a building can not be built under the cursor position.
	@param building_id: rowid of the selected building type"
	@param player_id: player id of the player that builds the building
	@param ship: If building from a ship, restrict to range of ship
	@param settle: bool Tells the building tool if a new settlement is created. Default: False
	"""

	def __init__(self):
		super(TearingTool, self).__init__()
		self.coords = None
		self.selected = []
		self.oldedges = None
		horizons.main.gui.on_escape = self.onEscape
		horizons.main.fife.cursor.set(fife.CURSOR_IMAGE, horizons.main.fife.tearing_cursor_image)

	def end(self):
		horizons.main.fife.cursor.set(fife.CURSOR_IMAGE, horizons.main.fife.default_cursor_image)
		super(TearingTool, self).end()

	def mouseDragged(self, evt):
		coords = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		if self.coords is None:
			self.coords = (int(round(coords.x)), int(round(coords.y)))
		self._mark(self.coords, (int(round(coords.x)), int(round(coords.y))))
		evt.consume()

	def mouseMoved(self,  evt):
		super(TearingTool, self).mouseMoved(evt)
		coords = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
		self._mark((int(round(coords.x)), int(round(coords.y))))
		evt.consume()

	def onEscape(self):
		self._mark()
		horizons.main.session.cursor = SelectionTool()

	def mouseReleased(self,  evt):
		if fife.MouseEvent.LEFT == evt.getButton():
			coords = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			if self.coords is None:
				self.coords = (int(round(coords.x)), int(round(coords.y)))
			self._mark(self.coords, (int(round(coords.x)), int(round(coords.y))))
			for i in self.selected:
				horizons.main.session.manager.execute(Tear(i))
			horizons.main.session.cursor = SelectionTool()
			evt.consume()

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.onEscape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			coords = horizons.main.session.view.cam.toMapCoordinates(fife.ScreenPoint(evt.getX(), evt.getY()), False)
			self.coords = (int(round(coords.x)), int(round(coords.y)))
			self._mark(self.coords)
		else:
			return
		evt.consume()

	def _mark(self, *edges):
		if len(edges) == 1:
			edges = (edges[0], edges[0])
		elif len(edges) == 2:
			edges = ((min(edges[0][0], edges[1][0]), min(edges[0][1], edges[1][1])),\
					 (max(edges[0][0], edges[1][0]), max(edges[0][1], edges[1][1])))
		else:
			edges = None
		if self.oldedges != edges or edges is None:
			for i in self.selected:
				horizons.main.session.view.renderer['InstanceRenderer'].removeColored(i._instance)
			self.selected = []
			self.oldedges = edges
		if edges is not None:
			for x in xrange(edges[0][0], edges[1][0] + 1):
				for y in xrange(edges[0][1], edges[1][1] + 1):
					b = horizons.main.session.world.get_building(x,y)
					if b is not None and b not in self.selected and not isinstance(b, StorageBuilding):
						self.selected.append(b)
			for i in self.selected:
				horizons.main.session.view.renderer['InstanceRenderer'].addColored(i._instance, 255, 255, 255)
