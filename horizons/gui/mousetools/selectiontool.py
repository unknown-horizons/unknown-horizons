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

from fife import fife

from horizons.command.unit import Act
from horizons.util import WorldObject
from navigationtool import NavigationTool
from horizons.constants import LAYERS

class SelectionTool(NavigationTool):
	def __init__(self, session):
		super(SelectionTool, self).__init__(session)
		self.session.gui.on_escape = self.session.gui.show_pause

	def end(self):
		super(SelectionTool, self).end()

	def mouseDragged(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # ab 3px (3*3 + 1)
			self.session.view.renderer['GenericRenderer'].removeAll("select")
			if do_multi:
				a = fife.Point(min(self.select_begin[0], evt.getX()), \
											 min(self.select_begin[1], evt.getY()))
				b = fife.Point(max(self.select_begin[0], evt.getX()), \
											 min(self.select_begin[1], evt.getY()))
				c = fife.Point(max(self.select_begin[0], evt.getX()), \
											 max(self.select_begin[1], evt.getY()))
				d = fife.Point(min(self.select_begin[0], evt.getX()), \
											 max(self.select_begin[1], evt.getY()))
				self.session.view.renderer['GenericRenderer'].addLine("select", \
																																			 fife.GenericRendererNode(a), fife.GenericRendererNode(b), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine("select", \
																																			 fife.GenericRendererNode(b), fife.GenericRendererNode(c), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine("select", \
																																			 fife.GenericRendererNode(d), fife.GenericRendererNode(c), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine("select", \
																																			 fife.GenericRendererNode(a), fife.GenericRendererNode(d), 200, 200, 200)
			selectable = []
			instances = self.session.view.cam.getMatchingInstances(\
				fife.Rect(min(self.select_begin[0], evt.getX()), \
									min(self.select_begin[1], evt.getY()), \
									abs(evt.getX() - self.select_begin[0]), \
									abs(evt.getY() - self.select_begin[1])) if do_multi else fife.ScreenPoint(evt.getX(), evt.getY()), self.session.view.layers[LAYERS.OBJECTS])
			for i in instances:
				instance = WorldObject.get_object_by_id(int(i.getId()))
				if hasattr(instance, 'select'):
					selectable.append(instance)
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
			self.session.view.renderer['GenericRenderer'].removeAll("select")
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseReleased(evt)
			return
		evt.consume()

	def apply_select(self):
		"""Called when selected instances changes. (Shows their menu)"""
		if len(self.session.selected_instances) > 1:
			pass
		elif len(self.session.selected_instances) == 1:
			for i in self.session.selected_instances:
				if self.session.world.player == i.owner:
					i.show_menu()

	def mousePressed(self, evt):
		if evt.isConsumedByWidgets():
			super(SelectionTool, self).mousePressed(evt)
			return
		elif evt.getButton() == fife.MouseEvent.LEFT:
			selectable = []
			instances = self.session.view.cam.getMatchingInstances(\
				fife.ScreenPoint(evt.getX(), evt.getY()), self.session.view.layers[LAYERS.OBJECTS])
			for i in instances:
				instance = WorldObject.get_object_by_id(int(i.getId()))
				if hasattr(instance, 'select'):
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
