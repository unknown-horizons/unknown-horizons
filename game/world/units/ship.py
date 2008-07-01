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

import game.main
import fife
from game.world.storage import Storage

class Ship(fife.InstanceActionListener):
	selectable = True
	"""Class representing a ship
		@param x: int x position
		@param y: int y position
	"""
	def __init__(self, x, y):
		if self._object == None:
			self.__class__._loadObject()
		self.last_position = (x, y)
		self.position = (x, y)
		self.target = (x, y)
		self.next_target = (x, y)
		self._instance = game.main.session.view.layers[1].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.session.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)
		self.inventory = Storage(4, 50)
		self.inventory.alter_inventory(6, 15)
		self.inventory.alter_inventory(5, 30)
		self.inventory.alter_inventory(4, 50)
		self.name = str(game.main.db("SELECT name FROM shipnames ORDER BY random() LIMIT 1")[0][0])
		self.health = 100

		self._instance.act('default', self._instance.getLocation(), True)
		super(Ship, self).__init__()
		self._instance.addActionListener(self)

	def select(self):
		"""Runs neccesary steps to select the unit."""
		self._instance.say(str(self.health) + '%', 0) # display health over selected ship
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		game.main.session.ingame_gui.show_ship(game.main.session.selected_instance) #show the gui for ships

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		game.main.session.selected_instance._instance.say('') #remove status of last selected unit
		game.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		game.main.session.ingame_gui.toggle_visible('ship') # hide the gui for ships

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position[0] + self.position[0] - self.last_position[0], self.position[1] + self.position[1] - self.last_position[1], 0))
		self._instance.act('default', location, True)
		game.main.session.view.cam.refresh()

	def start(self):
		pass

	def move(self, x, y):
		"""
		@param x: int x coordinate
		@param y: int y coordinate
		"""
		print "move"
		self.target = (x, y)
		if self.next_target == self.position:
			#calculate next target
			self.next_target = self.position
			if self.target[0] > self.position[0]:
				self.next_target = (self.position[0] + 1, self.next_target[1])
			elif self.target[0] < self.position[0]:
				self.next_target = (self.position[0] - 1, self.next_target[1])
			if self.target[1] > self.position[1]:
				self.next_target = (self.next_target[0], self.position[1] + 1)
			elif self.target[1] < self.position[1]:
				self.next_target = (self.next_target[0], self.position[1] - 1)
			#setup movement
			location = fife.Location(self._instance.getLocation().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target[0], self.next_target[1], 0))
			self._instance.move('default', location, 4.0/3.0)
			#setup next timer
			game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target[0] == self.position[0] or self.next_target[1] == self.position[1] else 17)

	def move_tick(self):
		"""Called by the schedular, moves the unit one step for this tick.
		"""
		#sync position
		self.last_position = self.position
		self.position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position[0], self.position[1], 0))
		self._instance.setLocation(location)

		if self.position != self.target:
			#calculate next target
			self.next_target = self.position
			if self.target[0] > self.position[0]:
				self.next_target = (self.position[0] + 1, self.next_target[1])
			elif self.target[0] < self.position[0]:
				self.next_target = (self.position[0] - 1, self.next_target[1])
			if self.target[1] > self.position[1]:
				self.next_target = (self.next_target[0], self.position[1] + 1)
			elif self.target[1] < self.position[1]:
				self.next_target = (self.next_target[0], self.position[1] - 1)
			#setup movement
			location = fife.Location(self._instance.getLocation().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target[0], self.next_target[1], 0))
			self._instance.move('default', location, 4.0/3.0)
			#setup next timer
			game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target[0] == self.position[0] or self.next_target[1] == self.position[1] else 17)
