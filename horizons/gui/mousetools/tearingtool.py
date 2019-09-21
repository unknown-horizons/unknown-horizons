# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import weakref

from fife import fife

import horizons.globals
from horizons.command.building import Tear
from horizons.constants import BUILDINGS
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.i18n import gettext as T, ngettext as NT
from horizons.messaging import WorldObjectDeleted
from horizons.util.python.weaklist import WeakList
from horizons.util.shapes import Point


class TearingTool(NavigationTool):
	"""
	Represents a dangling tool to remove (tear) buildings.
	"""
	tear_selection_color = (255, 255, 255)
	nearby_objects_radius = 4

	def __init__(self, session):
		super().__init__(session)
		self._transparent_instances = set() # fife instances modified for transparency
		self.coords = None
		self.selected = WeakList()
		self.oldedges = None
		self.tear_tool_active = True
		self.session.ingame_gui.hide_menu()
		self.session.selected_instances.clear()
		horizons.globals.fife.set_cursor_image("tearing")
		self._hovering_over = WeakList()
		WorldObjectDeleted.subscribe(self._on_object_deleted)

	def remove(self):
		self._mark()
		self.tear_tool_active = False
		horizons.globals.fife.set_cursor_image("default")
		WorldObjectDeleted.unsubscribe(self._on_object_deleted)
		super().remove()

	def mouseDragged(self, evt):
		coords = self.get_world_location(evt).to_tuple()
		if self.coords is None:
			self.coords = coords
		self._mark(self.coords, coords)
		evt.consume()

	def mouseMoved(self, evt):
		super().mouseMoved(evt)
		coords = self.get_world_location(evt).to_tuple()
		self._mark(coords)
		evt.consume()

	def on_escape(self):
		self.session.ingame_gui.set_cursor()

	def mouseReleased(self, evt):
		"""Tear selected instances and set selection tool as cursor"""
		self.log.debug("TearingTool: mouseReleased")
		if evt.getButton() == fife.MouseEvent.LEFT and not evt.isConsumedByWidgets():
			coords = self.get_world_location(evt).to_tuple()
			if self.coords is None:
				self.coords = coords
			self._mark(self.coords, coords)
			selection_list_copy = [building for building in self.selected]
			if self.selected:
				for building in selection_list_copy:
					self.session.view.renderer['InstanceRenderer'].removeColored(building._instance)
					if (building.id not in BUILDINGS.EXPAND_RANGE) or self.confirm_ranged_delete(building):
						Tear(building).execute(self.session)
			elif self._hovering_over:
				# we're hovering over a building, but none is selected, so this tear action isn't allowed
				warehouses = [b for b in self._hovering_over if
					       b.id == BUILDINGS.WAREHOUSE and b.owner.is_local_player]
				if warehouses:
					# tried to tear a warehouse, this is especially non-tearable
					pos = warehouses[0].position.origin
					self.session.ingame_gui.message_widget.add(point=pos, string_id="WAREHOUSE_NOT_TEARABLE")

			self.selected = WeakList()
			self._hovering_over = WeakList()
			if not evt.isShiftPressed() and not horizons.globals.fife.get_uh_setting('UninterruptedBuilding'):
				self.tear_tool_active = False
				self.on_escape()
			evt.consume()

	def confirm_ranged_delete(self, building):
			buildings_to_destroy = len(Tear.additional_removals_after_tear(building)[0])
			if buildings_to_destroy == 0:
				return True

			title = T("Destroy all buildings")
			msg = T("This will destroy all the buildings that fall outside of"
		            " the settlement range.")
			msg += "\n\n"
			msg += NT("%s additional building will be destroyed.",
		              "%s additional buildings will be destroyed",
		              buildings_to_destroy) % buildings_to_destroy
			return building.session.ingame_gui.open_popup(title, msg, show_cancel_button=True)

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
		elif evt.getButton() == fife.MouseEvent.LEFT and not evt.isConsumedByWidgets():
			self.coords = self.get_world_location(evt).to_tuple()
			self._mark(self.coords)
		else:
			return
		self.tear_tool_active = False
		evt.consume()

	def _mark(self, *edges):
		"""Highights building instances and keeps self.selected up to date."""
		self._restore_transparent_instances()
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
			for x in range(edges[0][0], edges[1][0] + 1):
				for y in range(edges[0][1], edges[1][1] + 1):
					b = self.session.world.get_building(Point(x, y))
					if b is not None:
						if b not in self._hovering_over:
							self._hovering_over.append(b)
							self._make_surrounding_transparent(b)
							self._remove_object_transparency(Point(x, y))
						if b.tearable and b.owner is not None and b.owner.is_local_player:
							if b not in self.selected:
								self._make_surrounding_transparent(b)
								self.selected.append(b)
								self._remove_object_transparency(Point(x, y))
			for i in self.selected:
				self.session.view.renderer['InstanceRenderer'].addColored(i._instance,
				                                                          *self.tear_selection_color)
		self.log.debug("TearingTool: mark done")

	def _remove_object_transparency(self, coords):
		"""helper function, used to remove transparency from object hovered upon,
		identified through its coordinates"""
		tile = self.session.world.get_tile(coords)
		if tile.object is not None and tile.object.buildable_upon:
			inst = tile.object.fife_instance
			inst.get2dGfxVisual().setTransparency(0)

	def _make_surrounding_transparent(self, building):
		"""Makes the surrounding of building_position transparent"""
		world_contains = self.session.world.map_dimensions.contains_without_border
		for coord in building.position.get_radius_coordinates(self.nearby_objects_radius, include_self=True):
			p = Point(*coord)
			if not world_contains(p):
				continue
			tile = self.session.world.get_tile(p)
			if tile.object is not None and tile.object.buildable_upon:
				inst = tile.object.fife_instance
				inst.get2dGfxVisual().setTransparency(BUILDINGS.TRANSPARENCY_VALUE)
				self._transparent_instances.add(weakref.ref(inst))

	def _restore_transparent_instances(self):
		"""Removes transparency"""
		for inst_weakref in self._transparent_instances:
			fife_instance = inst_weakref()
			if fife_instance:
				# remove transparency only if trees aren't supposed to be transparent as default
				if not hasattr(fife_instance, "keep_translucency") or not fife_instance.keep_translucency:
					fife_instance.get2dGfxVisual().setTransparency(0)
				else:
					# restore regular translucency value, can also be different
					fife_instance.get2dGfxVisual().setTransparency(BUILDINGS.TRANSPARENCY_VALUE)
		self._transparent_instances.clear()

	def _on_object_deleted(self, message):
		self.log.debug("TearingTool: on deletion notification %s", message.worldid)
		if message.sender in self.selected:
			self.log.debug("TearingTool: deleted obj present")
			self.selected.remove(message.sender)
