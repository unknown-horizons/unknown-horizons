# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.command.building import Tear
from horizons.util import Point

class TearingTool(NavigationTool):
	"""
	Represents a dangling tool to remove (tear) buildings.
	"""
	tear_selection_color = (255, 255, 255)

	def __init__(self, session):
		super(TearingTool, self).__init__(session)
		self.coords = None
		self.selected = set()
		self.oldedges = None
		self.tear_tool_active = True
		self.session.gui.on_escape = self.on_escape
		self.session.ingame_gui.hide_menu()
		horizons.main.fife.set_cursor_image("tearing")

	def remove(self):
		self._mark()
		self.tear_tool_active = False
		horizons.main.fife.set_cursor_image("default")
		super(TearingTool, self).remove()

	def mouseDragged(self, evt):
		coords = self.get_world_location_from_event(evt).to_tuple()
		if self.coords is None:
			self.coords = coords
		self._mark(self.coords, coords)
		evt.consume()

	def mouseMoved(self,  evt):
		super(TearingTool, self).mouseMoved(evt)
		coords = self.get_world_location_from_event(evt).to_tuple()
		self._mark(coords)
		evt.consume()

	def on_escape(self):
		self.session.set_cursor()

	def mouseReleased(self,  evt):
		"""Tear selected instances and set selection tool as cursor"""
		if fife.MouseEvent.LEFT == evt.getButton():
			coords = self.get_world_location_from_event(evt).to_tuple()
			if self.coords is None:
				self.coords = coords
			self._mark(self.coords, coords)
			for i in self.selected:
				self.session.view.renderer['InstanceRenderer'].removeColored(i._instance)
				Tear(i).execute(self.session)
			self.selected = set()

			if not evt.isShiftPressed() and not horizons.main.fife.get_uh_setting('UninterruptedBuilding'):
				self.tear_tool_active = False
				self.on_escape()
			evt.consume()

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.on_escape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			self.coords = self.get_world_location_from_event(evt).to_tuple()
			self._mark(self.coords)
		else:
			return
		self.tear_tool_active = False
		evt.consume()

	def _mark(self, *edges):
		"""Highights building instances and keeps self.selected up to date."""
		if len(edges) == 1:
			edges = (edges[0], edges[0])
		elif len(edges) == 2:
			edges = ((min(edges[0][0], edges[1][0]), min(edges[0][1], edges[1][1])), \
					 (max(edges[0][0], edges[1][0]), max(edges[0][1], edges[1][1])))
		else:
			edges = None
		if self.oldedges != edges or edges is None:
			for i in self.selected:
				self.session.view.renderer['InstanceRenderer'].removeColored(i._instance)
			self.selected = set()
			self.oldedges = edges
		if edges is not None:
			for x in xrange(edges[0][0], edges[1][0] + 1):
				for y in xrange(edges[0][1], edges[1][1] + 1):
					b = self.session.world.get_building(Point(x, y))
					if b is not None and b.tearable and self.session.world.player == b.owner:
						self.selected.add(b)
			for i in self.selected:
				self.session.view.renderer['InstanceRenderer'].addColored(i._instance, \
				                                                          *self.tear_selection_color)
