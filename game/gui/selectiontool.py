# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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

import time
import math
import fife

import game.main

from game.world.units import UnitClass
from game.world.units.unit import Unit
from game.world.units.ship import Ship
from game.command.unit import Act
from game.util import WeakList
from game.util import WorldObject
from navigationtool import NavigationTool

class SelectionTool(NavigationTool):
	"""The Selectiontool is used to select instances on the game screen.
	@param game: the main game Instance
	"""
	def __init__(self):
		super(SelectionTool, self).__init__()
		game.main.gui.on_escape = game.main.gui.show_pause

	def end(self):
		super(SelectionTool, self).end()

	def mouseDragged(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # ab 3px (3*3 + 1)
			game.main.session.view.renderer['GenericRenderer'].removeAll("select")
			if do_multi:
				a = fife.Point(min(self.select_begin[0], evt.getX()), \
							   min(self.select_begin[1], evt.getY()))
				b = fife.Point(max(self.select_begin[0], evt.getX()), \
							   min(self.select_begin[1], evt.getY()))
				c = fife.Point(max(self.select_begin[0], evt.getX()), \
							   max(self.select_begin[1], evt.getY()))
				d = fife.Point(min(self.select_begin[0], evt.getX()), \
							   max(self.select_begin[1], evt.getY()))
				game.main.session.view.renderer['GenericRenderer'].addLine("select", \
					fife.GenericRendererNode(a), fife.GenericRendererNode(b), 0, 255, 0)
				game.main.session.view.renderer['GenericRenderer'].addLine("select", \
					fife.GenericRendererNode(b), fife.GenericRendererNode(c), 0, 255, 0)
				game.main.session.view.renderer['GenericRenderer'].addLine("select", \
					fife.GenericRendererNode(d), fife.GenericRendererNode(c), 0, 255, 0)
				game.main.session.view.renderer['GenericRenderer'].addLine("select", \
					fife.GenericRendererNode(a), fife.GenericRendererNode(d), 0, 255, 0)
			selectable = []
			instances = game.main.session.view.cam.getMatchingInstances(\
				fife.Rect(min(self.select_begin[0], evt.getX()), \
						  min(self.select_begin[1], evt.getY()), \
						  abs(evt.getX() - self.select_begin[0]), \
						  abs(evt.getY() - self.select_begin[1])) if do_multi else fife.ScreenPoint(evt.getX(), evt.getY()), game.main.session.view.layers[1])
			for i in instances:
				instance = WorldObject.getObjectById(int(i.getId()))
				if hasattr(instance, 'select'):
					selectable.append(instance)
			instances = game.main.session.view.cam.getMatchingInstances(\
				fife.Rect(min(self.select_begin[0], evt.getX()), \
						  min(self.select_begin[1], evt.getY()), \
						  abs(evt.getX() - self.select_begin[0]), \
						  abs(evt.getY() - self.select_begin[1])) if do_multi else fife.ScreenPoint(evt.getX(), evt.getY()), game.main.session.view.layers[2])
			for i in instances:
				instance = WorldObject.getObjectById(int(i.getId()))
				if hasattr(instance, 'select'):
					selectable.append(instance)
			if len(selectable) > 1:
				if do_multi:
					for instance in selectable[:]:
						if isinstance(instance.__class__, game.world.building.BuildingClass):
							selectable.remove(instance)
				else:
					selectable = [selectable.pop(0)]
			if do_multi:
				selectable = set(self.select_old | frozenset(selectable))
			else:
				selectable = set(self.select_old ^ frozenset(selectable))
			for instance in game.main.session.selected_instances - selectable:
				instance.deselect()
			for instance in selectable - game.main.session.selected_instances:
				instance.select()
			game.main.session.selected_instances = selectable
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
			game.main.session.view.renderer['GenericRenderer'].removeAll("select")
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseReleased(evt)
			return
		evt.consume()

	def apply_select(self):
		if len(game.main.session.selected_instances) > 1:
			pass #todo: show multi select menu
		elif len(game.main.session.selected_instances) == 1:
			for i in game.main.session.selected_instances:
				if hasattr(i, 'show_menu'):
					i.show_menu()

	def mousePressed(self, evt):
		if evt.isConsumedByWidgets():
			super(SelectionTool, self).mousePressed(evt)
			return
		elif evt.getButton() == fife.MouseEvent.LEFT:
			selectable = []
			instances = game.main.session.view.cam.getMatchingInstances(\
				fife.ScreenPoint(evt.getX(), evt.getY()), game.main.session.view.layers[1])
			for i in instances:
				instance = WorldObject.getObjectById(int(i.getId()))
				if hasattr(instance, 'select'):
					selectable.append(instance)
			instances = game.main.session.view.cam.getMatchingInstances(\
				fife.ScreenPoint(evt.getX(), evt.getY()), game.main.session.view.layers[2])
			for i in instances:
				instance = WorldObject.getObjectById(int(i.getId()))
				if hasattr(instance, 'select'):
					selectable.append(instance)
			if len(selectable) > 1:
				selectable = selectable[0:0]
			self.select_old = frozenset(game.main.session.selected_instances) if evt.isControlPressed() else frozenset()
			selectable = set(self.select_old ^ frozenset(selectable))
			for instance in game.main.session.selected_instances - selectable:
				instance.deselect()
			for instance in selectable - game.main.session.selected_instances:
				instance.select()
			game.main.session.selected_instances = selectable
			self.select_begin = (evt.getX(), evt.getY())
			game.main.session.ingame_gui.hide_menu()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			if len(game.main.session.selected_instances) == 1 and \
			   any(hasattr(i, 'act') for i in game.main.session.selected_instances):
				target_mapcoord = game.main.session.view.cam.toMapCoordinates(\
					fife.ScreenPoint(evt.getX(), evt.getY()), False)
				for i in game.main.session.selected_instances:
					if isinstance(i, Unit):
						game.main.session.manager.execute(Act(i, target_mapcoord.x, target_mapcoord.y))
		else:
			super(SelectionTool, self).mousePressed(evt)
			return
		evt.consume()
