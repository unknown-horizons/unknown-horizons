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

class Unit(fife.InstanceActionListener):
	def __init__(self, x, y):
		if self._object is None:
			self.__class__._loadObject()
		self.last_unit_position = (x, y)
		self.unit_position = (x, y)
		self.move_target = (x, y)
		self.next_target = (x, y)
		self._instance = game.main.session.view.layers[1].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.session.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)
		self._instance.act('default', self._instance.getLocation(), True)
		super(Unit, self).__init__()
		self._instance.addActionListener(self)
		self.move_callback = None

	def start(self):
		pass

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.unit_position[0] + self.unit_position[0] - self.last_unit_position[0], self.unit_position[1] + self.unit_position[1] - self.last_unit_position[1], 0))
		self._instance.act('default', location, True)
		game.main.session.view.cam.refresh()

	def move(self, x, y, callback = None):
		"""
		@param x: int x coordinate
		@param y: int y coordinate
		"""
		self.move_target = (x, y)
		self.move_callback = callback
		if self.next_target == self.unit_position:
			#calculate next target
			self.next_target = self.unit_position
			if self.move_target[0] > self.unit_position[0]:
				self.next_target = (self.unit_position[0] + 1, self.next_target[1])
			elif self.move_target[0] < self.unit_position[0]:
				self.next_target = (self.unit_position[0] - 1, self.next_target[1])
			if self.move_target[1] > self.unit_position[1]:
				self.next_target = (self.next_target[0], self.unit_position[1] + 1)
			elif self.move_target[1] < self.unit_position[1]:
				self.next_target = (self.next_target[0], self.unit_position[1] - 1)
			#setup movement
			location = fife.Location(self._instance.getLocation().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target[0], self.next_target[1], 0))
			self._instance.move('default', location, 4.0/3.0)
			#setup next timer
			game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target[0] == self.unit_position[0] or self.next_target[1] == self.unit_position[1] else 17)
		elif self.move_callback is not None:
			self.move_callback()

	def move_tick(self):
		"""Called by the schedular, moves the unit one step for this tick.
		"""
		#sync unit_position
		self.last_unit_position = self.unit_position
		self.unit_position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.unit_position[0], self.unit_position[1], 0))
		self._instance.setLocation(location)

		if self.unit_position != self.move_target:
			#calculate next target
			self.next_target = self.unit_position
			if self.move_target[0] > self.unit_position[0]:
				self.next_target = (self.unit_position[0] + 1, self.next_target[1])
			elif self.move_target[0] < self.unit_position[0]:
				self.next_target = (self.unit_position[0] - 1, self.next_target[1])
			if self.move_target[1] > self.unit_position[1]:
				self.next_target = (self.next_target[0], self.unit_position[1] + 1)
			elif self.move_target[1] < self.unit_position[1]:
				self.next_target = (self.next_target[0], self.unit_position[1] - 1)
			#setup movement
			location = fife.Location(self._instance.getLocation().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target[0], self.next_target[1], 0))
			self._instance.move('default', location, 4.0/3.0)
			#setup next timer
			game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target[0] == self.unit_position[0] or self.next_target[1] == self.unit_position[1] else 17)
		elif self.move_callback is not None:
			self.move_callback()
