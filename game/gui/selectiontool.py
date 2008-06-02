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

from cursortool import CursorTool
from game.world.units import UnitClass
from game.world.units.ship import Ship
from game.command.unit import Move
import time
import fife
import math
import game.main

class SelectionTool(CursorTool):
	"""The Selectiontool is used to select instances on the game screen.
	@var game: the main game Instance
	"""
	def __init__(self):
		super(SelectionTool, self).__init__()
		self.lastScroll = [0, 0]

	def __del__(self):
		super(SelectionTool, self).__del__()
		print 'deconstruct',self

	def select_unit(self):
		"""Runs neccesary steps to select a unit."""
		game.main.game.selected_instance._instance.say(str(game.main.game.selected_instance.health) + '%', 0) # display health over selected ship
		game.main.game.view.renderer['InstanceRenderer'].addOutlined(game.main.game.selected_instance._instance, 255, 255, 255, 1)
		if isinstance(game.main.game.selected_instance, Ship):
			game.main.game.ingame_gui.gui['ship'].show() #show the gui for ships

	def deselect_unit(self):
		"""Runs neccasary steps to deselect a unit."""
		game.main.game.selected_instance._instance.say('') #remove status of last selected unit
		game.main.game.view.renderer['InstanceRenderer'].removeAllOutlines() # FIXME: removeOutlined(self.selected_instance.object) doesn't work
		if isinstance(game.main.game.selected_instance, Ship):
			game.main.game.ingame_gui.toggle_visible('ship') # hide the gui for ships

	def mousePressed(self, evt):
		clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
		cam = game.main.game.view.cam
		if (evt.getButton() == fife.MouseEvent.LEFT):
			instances = cam.getMatchingInstances(clickpoint, game.main.game.view.layers[1])
			if instances: #something under cursor
				print instances[0].getId()
				instance = game.main.game.entities.getInstance(instances[0].getId())
				if game.main.game.selected_instance and game.main.game.selected_instance != instance:
					self.deselect_unit()
				game.main.game.selected_instance = instance
				self.select_unit()
			elif game.main.game.selected_instance: #nothing under cursor
				self.deselect_unit()
				game.main.game.selected_instance = None
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			if game.main.game.selected_instance and isinstance(game.main.game.selected_instance, Ship):
				target_mapcoord = cam.toMapCoordinates(clickpoint, False)
				target_mapcoord.z = 0
				l = fife.Location(game.main.game.view.layers[1])
				l.setMapCoordinates(target_mapcoord)
				game.main.game.manager.execute(Move(game.main.game.selected_instance, target_mapcoord.x, target_mapcoord.y))
		evt.consume()

	def mouseMoved(self, evt):
		# Mouse scrolling
		mousepoint = fife.ScreenPoint(evt.getX(), evt.getY())
		old = self.lastScroll
		new = [0, 0]
		if mousepoint.x < 50:
			new[0] -= 50 - mousepoint.x
		elif mousepoint.x >= (game.main.game.view.cam.getViewPort().right()-50):
			new[0] += 51 + mousepoint.x - game.main.game.view.cam.getViewPort().right()
		if mousepoint.y < 50:
			new[1] -= 50 - mousepoint.y
		elif mousepoint.y >= (game.main.game.view.cam.getViewPort().bottom()-50):
			new[1] += 51 + mousepoint.y - game.main.game.view.cam.getViewPort().bottom()
		if new[0] != old[0] or new[1] != old[1]:
			game.main.game.view.autoscroll(new[0]-old[0], new[1]-old[1])
			self.lastScroll = new

	def mouseWheelMovedUp(self, evt):
		game.main.game.view.zoom_in()
		evt.consume()

	def mouseWheelMovedDown(self, evt):
		game.main.game.view.zoom_out()
		evt.consume()
