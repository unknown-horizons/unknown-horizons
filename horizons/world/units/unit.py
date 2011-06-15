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

import math
import logging
from fife import fife

import horizons.main

from horizons.world.units.movingobject import MovingObject
from horizons.util import Point, WorldObject, WeakMethod, Circle, decorators
from horizons.constants import LAYERS
from horizons.ambientsound import AmbientSound

class Unit(AmbientSound, MovingObject):
	log = logging.getLogger("world.units")
	is_unit = True
	is_ship = False
	health_bar_y = -30
	is_selectable = False

	def __init__(self, x, y, owner=None, **kwargs):
		super(Unit, self).__init__(x=x, y=y, **kwargs)
		self.__init(x, y, owner)

	def __init(self, x, y, owner, health = 100.0):
		self.owner = owner
		class Tmp(fife.InstanceActionListener): pass
		self.InstanceActionListener = Tmp()
		self.InstanceActionListener.onInstanceActionFinished = \
				WeakMethod(self.onInstanceActionFinished)
		self.InstanceActionListener.thisown = 0 # fife will claim ownership of this
		if self._object is None:
			self.__class__._loadObject()

		self._instance = self.session.view.layers[LAYERS.OBJECTS].createInstance( \
			self._object, fife.ModelCoordinate(int(x), int(y), 0), str(self.worldid))
		fife.InstanceVisual.create(self._instance)
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(x + x, y + y, 0))
		self.act(self._action, location, True)
		self._instance.addActionListener(self.InstanceActionListener)

		self.health = health
		self.max_health = 100.0

		self.loading_area = self.position

	def remove(self):
		self.log.debug("Unit.remove for %s started", self)
		self._instance.removeActionListener(self.InstanceActionListener)
		super(Unit, self).remove()

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate( \
			self.position.x + self.position.x - self.last_position.x, \
			self.position.y + self.position.y - self.last_position.y, 0))
		self.act(self._action, location, True)
		self.session.view.cam.refresh()

	def draw_health(self):
		"""Draws the units current health as a healthbar over the unit."""
		renderer = self.session.view.renderer['GenericRenderer']
		renderer.removeAll("health_" + str(self.worldid))
		zoom = self.session.view.get_zoom()
		height = int(5 * zoom)
		width = int(50 * zoom)
		y_pos = int(self.health_bar_y * zoom)
		mid_node_up = fife.GenericRendererNode(self._instance, \
									fife.Point(-width/2+int(((self.health/self.max_health)*width)),\
		                                       y_pos-height)
		                            )
		mid_node_down = fife.GenericRendererNode(self._instance, \
		                                         fife.Point(
		                                             -width/2+int(((self.health/self.max_health)*width))
		                                             ,y_pos)
		                                         )
		if self.health != 0:
			renderer.addQuad("health_" + str(self.worldid), \
			                fife.GenericRendererNode(self._instance, \
			                                         fife.Point(-width/2, y_pos-height)), \
			                mid_node_up, \
			                mid_node_down, \
			                fife.GenericRendererNode(self._instance, fife.Point(-width/2, y_pos)), \
			                0, 255, 0)
		if self.health != self.max_health:
			renderer.addQuad("health_" + str(self.worldid), mid_node_up, \
			                 fife.GenericRendererNode(self._instance, fife.Point(width/2, y_pos-height)), \
			                 fife.GenericRendererNode(self._instance, fife.Point(width/2, y_pos)), \
			                 mid_node_down, 255, 0, 0)

	def hide(self):
		"""Hides the unit."""
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(False)

	def show(self):
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(True)

	def save(self, db):
		super(Unit, self).save(db)

		owner_id = 0 if self.owner is None else self.owner.worldid
		db("INSERT INTO unit (rowid, type, x, y, health, owner) VALUES(?, ?, ?, ?, ?, ?)",
			self.worldid, self.__class__.id, self.position.x, self.position.y, \
					self.health, owner_id)

	def load(self, db, worldid):
		super(Unit, self).load(db, worldid)

		x, y, health, owner_id = db("SELECT x, y, health, owner FROM unit WHERE rowid = ?", worldid)[0]
		if (owner_id == 0):
			owner = None
		else:
			owner = WorldObject.get_object_by_id(owner_id)
		self.__init(x, y, owner, health)

		return self

	def get_random_location(self, in_range):
		"""Returns a random location in walking_range, that we can find a path to
		Does not check every point, only a few samples are tried.
		@param in_range: int, max distance to returned point from current position
		@return: Instance of Point or None"""
		range_squared = in_range * in_range
		randint = self.session.random.randint
		# pick a sample, try tries times
		tries = int(range_squared / 2)
		for i in xrange(tries):
			# choose x-difference, then y-difference so that the distance is in the range.
			x_diff = randint(1, in_range) # always go at least 1 field
			y_max_diff = int( math.sqrt(range_squared - x_diff*x_diff) )
			y_diff = randint(0, y_max_diff)
			# use randomness of x/y_diff below, randint calls are expensive
			# this results in a higher chance for x > y than y < x, so equalize
			if (x_diff + y_diff) % 2 == 0:
				x_diff, y_diff = y_diff, x_diff
			# direction
			if x_diff % 2 == 0:
				y_diff = -y_diff
			if y_diff % 2 == 0:
				x_diff = -x_diff
			# check this target
			possible_target = Point(self.position.x + x_diff, self.position.y + y_diff)
			if self.check_move(possible_target):
				return possible_target
		return None

	def __str__(self): # debug
		classname = horizons.main.db.cached_query("SELECT name FROM unit where id = ?", self.id)[0][0]
		return '%s(id=%s;worldid=%s)' % (classname, self.id, \
																		 self.worldid)


decorators.bind_all(Unit)