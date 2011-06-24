# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import horizons.main

from fife import fife
from horizons.constants import GAME_SPEED, LAYERS
from horizons.scheduler import Scheduler

class CannonBall(object):
	"""
	Class for a canonball animation
	"""
	def __init__(self, source, dest, speed, session):
		"""
		@param source: Point with starting position
		@param dest: Point with ending position
		@param speed: Attack speed of the Weapon that fires the canonball
		"""
		self.position = source
		# needed ticks to go to the destination
		self.needed_ticks = int(GAME_SPEED.TICKS_PER_SECOND * source.distance(dest) / speed)
		# the thick that the object is currently at
		self.current_tick = 0
		self.session = session
		# get the current position
		self.x = source.x
		self.y = source.y
		# calculate the axis ratio that is added per tick to move
		self.x_ratio = (dest.x - source.x)/self.needed_ticks
		self.y_ratio = (dest.y - source.y)/self.needed_ticks
		print self.x_ratio
		print self.y_ratio
		import random
		self.id = random.randint(1,1000)
		self._move_tick()

	def _move_tick(self):
		self.session.view.renderer['GenericRenderer'].removeAll("ball" + str(self.id))
		if self.current_tick == self.needed_ticks:
			return
		self.current_tick += 1
		self.x += self.x_ratio
		self.y += self.y_ratio
		loc = fife.Location(self.session.view.layers[LAYERS.OBJECTS])
		loc.thisown = 0
		coords = fife.ModelCoordinate(self.x, self.y)
		coords.thisown = 0
		loc.setLayerCoordinates(coords)
		self.session.view.renderer['GenericRenderer'].addAnimation(
			"ball" + str(self.id), fife.GenericRendererNode(loc),
			horizons.main.fife.animationpool.addResourceFromFile("as_cannonball0-idle-45")
		)
		Scheduler().add_new_object(self._move_tick, self, 1)

