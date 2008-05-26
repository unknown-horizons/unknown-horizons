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

import game.main
import fife

_STATE_NONE, _STATE_IDLE, _STATE_MOVE = xrange(3)

class Ship(object):
	"""Class representing a ship"""

	def __init__(self, x, y):
		if self._object == None:
			self.__class__._loadObject()
		self.position = (x, y)
		self.target = (x, y)
		self.next_target = (x, y)
		self._instance = game.main.game.view.layers[1].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.game.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)
		self._instance.act('default', self._instance.getLocation(), True)

		self.name = ""
		self.state = _STATE_NONE

		self.health = 100

	def start(self):
		pass

	def move(self, x, y):
		if self.target[0] == self.position[0] and self.target[1] == self.position[1]:
			#calculate next target
			if self.target[0] > self.position[0]:
				self.next_target = (self.position[0] + 1, self.next_target[1])
			elif self.target[0] < self.position[0]:
				self.next_target = (self.position[0] - 1, self.next_target[1])
			if self.target[1] > self.position[1]:
				self.next_target = (self.position[0], self.next_target[1] + 1)
			elif self.target[1] < self.position[1]:
				self.next_target = (self.position[0], self.next_target[1] - 1)
			time = 12 if self.next_target[0] == self.position[0] or self.next_target[1] == self.position[1] else 17
			#setup movement
			location = fife.Location(self._instance.getLocation().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target[0], self.next_target[1], 0))
			#self._instance.move('default', location, time)
			#setup next timer
			game.main.game.scheduler.add_new_object(self.move_tick, self, time)
		self.target = (x, y)

	def move_tick(self):
		print 'tick'
		#sync position
		self.position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position[0], self.position[1], 0))
		self._instance.setLocation(location)

		if self.position != self.target:
			#calculate next target
			if self.target[0] > self.position[0]:
				self.next_target = (self.position[0] + 1, self.next_target[1])
			elif self.target[0] < self.position[0]:
				self.next_target = (self.position[0] - 1, self.next_target[1])
			if self.target[1] > self.position[1]:
				self.next_target = (self.position[0], self.next_target[1] + 1)
			elif self.target[1] < self.position[1]:
				self.next_target = (self.position[0], self.next_target[1] - 1)
			time = 12 if self.next_target[0] == self.position[0] or self.next_target[1] == self.position[1] else 17
			#setup movement
			location = fife.Location(self._instance.getLocationRef().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target[0], self.next_target[1], 0))
			#self._instance.move('default', location, time)
			#setup next timer
			game.main.game.scheduler.add_new_object(self.move_tick, self, time)
