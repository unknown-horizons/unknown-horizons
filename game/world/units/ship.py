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
		self.x = x
		self.y = y
		self._instance = game.main.game.view.layers[1].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.game.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)

		self.name = ""
		self.state = _STATE_NONE

		self.health = 100

	def start(self):
		pass

	def move(self, location):
		"""Moves the ship to a certain location
		@var location: fife.Location to which the unit should move
		"""
		self.state = _STATE_MOVE
		#self.object.move('move', location, 2)
		facing_location = fife.Location(location)
		facing_location.setExactLayerCoordinates(self._instance.getFacingLocation().getExactLayerCoordinates() - self._instance.getLocation().getExactLayerCoordinates() + location.getExactLayerCoordinates())
		self._instance.setLocation(location)
		self._instance.setFacingLocation(facing_location)
