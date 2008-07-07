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
from game.world.units import UnitClass
from game.world.units.ship import Ship
from game.command.unit import Move
import time
import fife
import math
import game.main

class SelectionTool(NavigationTool):
	"""The Selectiontool is used to select instances on the game screen.
	@param game: the main game Instance
	"""
	def begin(self):
		super(SelectionTool, self).begin()
		game.main.onEscape = game.main.showPause

	def end(self):
		game.main.onEscape = lambda : None
		super(SelectionTool, self).end()

	def mouseDragged(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # ab 3px (3*3 + 1)
			game.main.session.view.renderer['GeometricRenderer'].removeAllLines()
			if do_multi:
				a = fife.Point(min(self.select_begin[0], evt.getX()), min(self.select_begin[1], evt.getY()))
				b = fife.Point(max(self.select_begin[0], evt.getX()), min(self.select_begin[1], evt.getY()))
				c = fife.Point(max(self.select_begin[0], evt.getX()), max(self.select_begin[1], evt.getY()))
				d = fife.Point(min(self.select_begin[0], evt.getX()), max(self.select_begin[1], evt.getY()))
				game.main.session.view.renderer['GeometricRenderer'].addLine(a, b, 0, 255, 0)
				game.main.session.view.renderer['GeometricRenderer'].addLine(b, c, 0, 255, 0)
				game.main.session.view.renderer['GeometricRenderer'].addLine(d, c, 0, 255, 0)
				game.main.session.view.renderer['GeometricRenderer'].addLine(a, d, 0, 255, 0)
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseDragged(evt)
			return
		evt.consume()

	def mouseReleased(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # ab 3px (3*3 + 1)
			instances = game.main.session.view.cam.getMatchingInstances(fife.Rect(min(self.select_begin[0], evt.getX()), min(self.select_begin[1], evt.getY()), abs(evt.getX() - self.select_begin[0]), abs(evt.getY() - self.select_begin[1])) if do_multi else clickpoint, game.main.session.view.layers[1])
			if len(instances) > 0: #something under cursor
				print len(instances)
				instance = game.main.session.entities.getInstance(instances[0].getId())
				if not hasattr(instance, 'select'):
					instance = None
			else:
				instance = None
			if game.main.session.selected_instance != instance:
				if game.main.session.selected_instance is not None:
					game.main.session.selected_instance.deselect()
				game.main.session.selected_instance = instance
				if instance is not None:
					game.main.session.selected_instance.select()
			del self.select_begin
			game.main.session.view.renderer['GeometricRenderer'].removeAllLines()
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseReleased(evt)
			return
		evt.consume()

	def mousePressed(self, evt):
		if evt.isConsumedByWidgets():
			super(SelectionTool, self).mousePressed(evt)
			return
		elif evt.getButton() == fife.MouseEvent.LEFT:
			self.select_begin = (evt.getX(), evt.getY())
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
			if game.main.session.selected_instance is not None and isinstance(game.main.session.selected_instance, Ship):
				target_mapcoord = game.main.session.view.cam.toMapCoordinates(clickpoint, False)
				target_mapcoord.z = 0
				l = fife.Location(game.main.session.view.layers[1])
				l.setMapCoordinates(target_mapcoord)
				game.main.session.manager.execute(Move(game.main.session.selected_instance, target_mapcoord.x, target_mapcoord.y))
		else:
			super(SelectionTool, self).mousePressed(evt)
			return
		evt.consume()
