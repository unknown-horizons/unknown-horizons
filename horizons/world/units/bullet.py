# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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
from horizons.constants import LAYERS
from horizons.scheduler import Scheduler
from horizons.util import WorldObject
from horizons.component.componentholder import ComponentHolder

class Bullet(ComponentHolder, WorldObject):
	"""
	Class for Bullet animation.
	Has no components, but has_components is used by some code.
	"""
	_object = None
	owner = None

	def __init__(self, image, source, dest, needed_ticks, session, offset=True, worldid=None):
		"""
		@param image: path to file with bullet image
		@param source: Point with starting position
		@param dest: Point with ending position
		@param speed: Attack speed of the Weapon that fires the canonball
		@param session: Horizons Session
		@param offset: True if image should be offseted from start location
		"""

		super(Bullet, self).__init__(worldid)
		self.session = session
		# get the current position
		self.x = source.x
		self.y = source.y

		# needed for saving the bullet
		self.dest_x = dest.x
		self.dest_y = dest.y
		self.image = image

		# offset the position so it starts from the middle of the firing instance
		if offset:
			self.x += 1
			self.y -= 1

		# needed ticks to go to the destination
		self.needed_ticks = needed_ticks
		self.needed_ticks -= 2

		# the thick that the object is currently at
		self.current_tick = 0

		# calculate the axis ratio that is added per tick to move
		self.x_ratio = float(dest.x - source.x)/self.needed_ticks
		self.y_ratio = float(dest.y - source.y)/self.needed_ticks

		if not Bullet._object:
			Bullet._object = horizons.main.fife.engine.getModel().createObject('cb', 'cannonball')
			fife.ObjectVisual.create(Bullet._object)

			visual = self._object.get2dGfxVisual()
			img = horizons.main.fife.imagemanager.load(str(image))
			for rotation in [45, 135, 225, 315]:
				visual.addStaticImage(rotation, img.getHandle())


		self._instance = session.view.layers[LAYERS.FIELDS].createInstance(
			self._object, fife.ModelCoordinate(int(self.x),int(self.y), 0), str(self.worldid))
		fife.InstanceVisual.create(self._instance)
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.x, self.y, 0))
		self.session.world.bullets.append(self)

		self._move_tick()

	def _move_tick(self):
		if self.current_tick == self.needed_ticks:
			self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
			self._instance = None
			self.session.world.bullets.remove(self)
			self.remove()
			return
		self.current_tick += 1
		self.x += self.x_ratio
		self.y += self.y_ratio
		fife_location = fife.Location(self._instance.getLocationRef().getLayer())
		fife_location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.x, self.y, 0))
		self._instance.setLocation(fife_location)

		Scheduler().add_new_object(self._move_tick, self, 1)

	def save(self, db):
		db("INSERT INTO bullet(worldid, startx, starty, destx, desty, speed, image) VALUES(?, ?, ?, ?, ?, ?, ?)",
			self.worldid, self.x, self.y, self.dest_x, self.dest_y, self.needed_ticks, self.image)
