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
		if (evt.getButton() == fife.MouseEvent.LEFT):
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # ab 3px (3*3 + 1)
			"""if do_multi:
				if not hasattr(self, 'select_rect'):
					self.select_rect = game.main.fife.pychan.widgets.Window(parent = None, size=(100,100))
					self.select_rect.show()
				self.select_rect._setX(min(self.select_begin[0], evt.getX()))
				self.select_rect._setY(min(self.select_begin[1], evt.getY()))
				self.select_rect._setWidth(abs(self.select_begin[0] - evt.getX()))
				self.select_rect._setHeight(abs(self.select_begin[1] - evt.getY()))
			elif hasattr(self, 'select_rect'):
				self.select_rect.hide()
				del self.select_rect"""
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseDragged(evt)
			return
		evt.consume()

	def mouseReleased(self, evt):
		if (evt.getButton() == fife.MouseEvent.LEFT):
			clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
			instances = game.main.session.view.cam.getMatchingInstances(clickpoint, game.main.session.view.layers[1])
			if len(instances) != 0: #something under cursor
				assert(len(instances) == 1)
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
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseDragged(evt)
			return
		evt.consume()

	def mousePressed(self, evt):
		if (evt.getButton() == fife.MouseEvent.LEFT):
			self.select_begin = (evt.getX(), evt.getY())
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
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
