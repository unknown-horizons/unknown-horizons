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
from horizons.util import Point, WeakList
from horizons.constants import BUILDINGS
from horizons.messaging import WorldObjectDeleted

class TearingTool(NavigationTool):
	"""
	Represents a dangling tool to remove (tear) buildings.
	"""
	tear_selection_color = (255, 255, 255)

	def __init__(self, session):
		super(TearingTool, self).__init__(session)
		self.coords = None
		self.selected = WeakList()
		self.oldedges = None
		self.tear_tool_active = True
		self.session.gui.on_escape = self.on_escape
		self.session.ingame_gui.hide_menu()
		horizons.main.fife.set_cursor_image("tearing")
		self._hovering_over = WeakList()
		WorldObjectDeleted.subscribe(self._on_object_deleted)

	def remove(self):
		self._mark()
		self.tear_tool_active = False
		horizons.main.fife.set_cursor_image("default")
		WorldObjectDeleted.subscribe(self._on_object_deleted)
		super(TearingTool, self).remove()

	def mouseDragged(self, evt):
		coords = self.get_world_location(evt).to_tuple()
		if self.coords is None:
			self.coords = coords
		self._mark(self.coords, coords)
		evt.consume()

	def mouseMoved(self,  evt):
		super(TearingTool, self).mouseMoved(evt)
		coords = self.get_world_location(evt).to_tuple()
		self._mark(coords)
		evt.consume()

	def on_escape(self):
		self.session.set_cursor()

	def mouseReleased(self,  evt):
		"""Tear selected instances and set selection tool as cursor"""
		self.log.debug("TearingTool: mouseReleased")
		if fife.MouseEvent.LEFT == evt.getButton():
			coords = self.get_world_location(evt).to_tuple()
			if self.coords is None:
				self.coords = coords
			self._mark(self.coords, coords)
			for i in [i for i in self.selected]:
				self.session.view.renderer['InstanceRenderer'].removeColored(i._instance)
				Tear(i).execute(self.session)
			else:
				if self._hovering_over:
					# we're hovering over a building, but none is selected, so this tear action isn't allowed
					warehouses = [ b for b in self._hovering_over if
					               b.id == BUILDINGS.WAREHOUSE ]
					if warehouses:
						# tried to tear a warehouse, this is especially non-tearable
						pos = warehouses[0].position.origin
						self.session.ingame_gui.message_widget.add(point=pos, string_id="WAREHOUSE_NOT_TEARABLE" )

			self.selected = WeakList()
			self._hovering_over = WeakList()

			if not evt.isShiftPressed() and not horizons.main.fife.get_uh_setting('UninterruptedBuilding'):
				self.tear_tool_active = False
				self.on_escape()
			evt.consume()

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.on_escape()
		elif fife.MouseEvent.LEFT == evt.getButton():
			self.coords = self.get_world_location(evt).to_tuple()
			self._mark(self.coords)
		else:
			return
		self.tear_tool_active = False
		evt.consume()

	def _mark(self, *edges):
		"""Highights building instances and keeps self.selected up to date."""
		self.log.debug("TearingTool: mark")
		if len(edges) == 1:
			edges = (edges[0], edges[0])
		elif len(edges) == 2:
			edges = ((min(edges[0][0], edges[1][0]), min(edges[0][1], edges[1][1])),
					 (max(edges[0][0], edges[1][0]), max(edges[0][1], edges[1][1])))
		else:
			edges = None
		if self.oldedges != edges or edges is None:
			for i in self.selected:
				self.session.view.renderer['InstanceRenderer'].removeColored(i._instance)
			self.selected = WeakList()
			self.oldedges = edges
		if edges is not None:
			self._hovering_over = WeakList()
			for x in xrange(edges[0][0], edges[1][0] + 1):
				for y in xrange(edges[0][1], edges[1][1] + 1):
					b = self.session.world.get_building(Point(x, y))
					if b is not None:
						if b not in self._hovering_over:
							self._hovering_over.append(b)
						if b.tearable and b.owner is not None and b.owner.is_local_player:
							if b not in self.selected:
								self.selected.append(b)
			for i in self.selected:
				self.session.view.renderer['InstanceRenderer'].addColored(i._instance,
				                                                          *self.tear_selection_color)
		self.log.debug("TearingTool: mark done")


	def _on_object_deleted(self, message):
		self.log.debug("TearingTool: on deletion notification %s", message.worldid)
		if message.sender in self.selected:
			self.log.debug("TearingTool: deleted obj present")
			self.selected.remove(message.sender)
