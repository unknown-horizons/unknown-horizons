# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

	def select_unit(self):
		"""Runs neccesary steps to select a unit."""
		game.main.game.selected_instance.object.say(str(game.main.game.selected_instance.health) + '%', 0) # display health over selected ship
		game.main.game.view.renderer['InstanceRenderer'].addOutlined(game.main.game.selected_instance.object, 255, 255, 255, 1)
		if game.main.game.selected_instance.__class__ is Ship:
			game.main.game.ingame_gui.gui['ship'].show() #show the gui for ships

	def deselect_unit(self):
		"""Runs neccasary steps to deselect a unit."""
		if game.main.game.selected_instance.__class__ is Ship:
			game.main.game.ingame_gui.toggle_visible('ship') # hide the gui for ships
			game.main.game.selected_instance.object.say('') #remove status of last selected unit
			game.main.game.view.renderer['InstanceRenderer'].removeAllOutlines() # FIXME: removeOutlined(self.selected_instance.object) doesn't work

	def mousePressed(self, evt):
		clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
		cam = game.main.game.view.cam
		if (evt.getButton() == fife.MouseEvent.LEFT):
			instances = cam.getMatchingInstances(clickpoint, game.main.game.view.layers[1])
			if instances: #check if clicked point is a unit
				selected = instances[0]
				if game.main.game.selected_instance:
					if game.main.game.selected_instance.object.getFifeId() != selected.getFifeId():
						self.deselect_unit()
				if selected.getFifeId() in game.main.game.instance_to_unit:
					game.main.game.selected_instance = game.main.game.instance_to_unit[selected.getFifeId()]
					self.select_unit()
				else:
					game.main.game.selected_instance = None
			elif game.main.game.selected_instance: # remove unit selection
				self.deselect_unit()
				game.main.game.selected_instance = None

		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			if game.main.game.selected_instance: # move unit
				if game.main.game.selected_instance.type == 'ship':
					target_mapcoord = cam.toMapCoordinates(clickpoint, False)
					target_mapcoord.z = 0
					l = fife.Location(game.main.game.view.layers[1])
					l.setMapCoordinates(target_mapcoord)
					game.main.game.manager.execute(Move(game.main.game.selected_instance.object.getFifeId(), target_mapcoord.x, target_mapcoord.y, 1))
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

	def __del__(self):
		CursorTool.__del__(self)
