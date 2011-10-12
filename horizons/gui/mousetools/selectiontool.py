# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.command.unit import Act
from horizons.util import WorldObject
from horizons.util.worldobject import WorldObjectNotFound
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.constants import LAYERS

class SelectionTool(NavigationTool):
	_SELECTION_RECTANGLE_NAME = "_select" # GenericRenderer objects are sorted by name, so first char is important

	def __init__(self, session):
		super(SelectionTool, self).__init__(session)
		self.session.gui.on_escape = self.session.gui.toggle_pause

	def end(self):
		super(SelectionTool, self).end()

	def mouseDragged(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # ab 3px (3*3 + 1)
			self.session.view.renderer['GenericRenderer'].removeAll(self.__class__._SELECTION_RECTANGLE_NAME)
			if do_multi:
				# draw a rectangle
				a = fife.Point(min(self.select_begin[0], evt.getX()), \
											 min(self.select_begin[1], evt.getY()))
				b = fife.Point(max(self.select_begin[0], evt.getX()), \
											 min(self.select_begin[1], evt.getY()))
				c = fife.Point(max(self.select_begin[0], evt.getX()), \
											 max(self.select_begin[1], evt.getY()))
				d = fife.Point(min(self.select_begin[0], evt.getX()), \
											 max(self.select_begin[1], evt.getY()))
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(a), fife.RendererNode(b), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(b), fife.RendererNode(c), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(d), fife.RendererNode(c), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(a), fife.RendererNode(d), 200, 200, 200)
			selectable = []

			instances = self.session.view.cam.getMatchingInstances(\
				fife.Rect(min(self.select_begin[0], evt.getX()), \
									min(self.select_begin[1], evt.getY()), \
									abs(evt.getX() - self.select_begin[0]), \
									abs(evt.getY() - self.select_begin[1])) if do_multi else fife.ScreenPoint(evt.getX(), evt.getY()), self.session.view.layers[LAYERS.OBJECTS])
			layer_instances = [i.this for i in self.session.view.layers[LAYERS.OBJECTS].getInstances()]
			instances = [i for i in instances if i.this in layer_instances]
			# Only one unit, select anyway
			if len(instances) == 1:
				try:
					i_id = instances[0].getId()
					if i_id != '':
						instance = WorldObject.get_object_by_id(int(i_id))
						if instance.is_selectable:
							selectable.append(instance)
				except WorldObjectNotFound:
					pass
			else:
				for i in instances:
					try:
						i_id = i.getId()
						if i_id == '':
							continue
						instance = WorldObject.get_object_by_id(int(i_id))
						if instance.is_selectable and instance.owner == self.session.world.player:
							selectable.append(instance)
					except WorldObjectNotFound:
						pass

			if len(selectable) > 1:
				if do_multi:
					for instance in selectable[:]: # iterate through copy for safe removal
						if instance.is_building:
							selectable.remove(instance)
				else:
					selectable = [selectable.pop(0)]

			if do_multi:
				selectable = set(self.select_old | frozenset(selectable))
			else:
				selectable = set(self.select_old ^ frozenset(selectable))
			for instance in self.session.selected_instances - selectable:
				instance.deselect()
			for instance in selectable - self.session.selected_instances:
				instance.select()
			self.session.selected_instances = selectable
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseDragged(evt)
			return
		evt.consume()

	def mouseReleased(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			self.apply_select()
			del self.select_begin, self.select_old
			self.session.view.renderer['GenericRenderer'].removeAll(self.__class__._SELECTION_RECTANGLE_NAME)
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseReleased(evt)
			return
		evt.consume()

	def apply_select(self):
		"""
		Called when selected instances changes. (Shows their menu)
		If one of the selected instances can attack, switch mousetool to AttackingTool
		"""
		selected = self.session.selected_instances
		if len(selected) > 1 and all( i.is_unit for i in selected ):
			self.session.ingame_gui.show_multi_select_tab()
		elif len(selected) == 1:
			for i in selected:
				i.show_menu()

		#change session cursor to attacking tool if selected instances can attack
		from attackingtool import AttackingTool
		attacking_unit_found = False
		for i in selected:
			if hasattr(i, 'attack') and i.owner == self.session.world.player:
				attacking_unit_found = True
				break

		if attacking_unit_found and not isinstance(self.session.cursor, AttackingTool):
			self.session.cursor = AttackingTool(self.session)
		if not attacking_unit_found and isinstance(self.session.cursor, AttackingTool):
			self.session.cursor = SelectionTool(self.session)
			horizons.main.fife.cursor.set(horizons.main.fife.default_cursor_image)

	def mousePressed(self, evt):
		if evt.isConsumedByWidgets():
			super(SelectionTool, self).mousePressed(evt)
			return
		elif evt.getButton() == fife.MouseEvent.LEFT:
			selectable = []
			instances = self.get_hover_instances(evt)
			for instance in instances:
				if instance.is_selectable:
					selectable.append(instance)
			if len(selectable) > 1:
				selectable = selectable[0:0]
			self.select_old = frozenset(self.session.selected_instances) if evt.isControlPressed() else frozenset()
			selectable = set(self.select_old ^ frozenset(selectable))
			for instance in self.session.selected_instances - selectable:
				instance.deselect()
			for instance in selectable - self.session.selected_instances:
				instance.select()
			self.session.selected_instances = selectable
			self.select_begin = (evt.getX(), evt.getY())
			self.session.ingame_gui.hide_menu()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			target_mapcoord = self.session.view.cam.toMapCoordinates(\
				fife.ScreenPoint(evt.getX(), evt.getY()), False)
			for i in self.session.selected_instances:
				if i.movable:
					Act(i, target_mapcoord.x, target_mapcoord.y).execute(self.session)
		else:
			super(SelectionTool, self).mousePressed(evt)
			return
		evt.consume()
