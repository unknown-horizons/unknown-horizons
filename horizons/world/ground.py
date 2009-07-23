# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import fife

import horizons.main

from horizons.util import WorldObject
from horizons.constants import LAYERS

class Ground(WorldObject):
	def __init__(self, x, y):
		"""
		@param x: int x position the ground is created.
		@param y: int y position the ground is created.
		"""
		super(Ground, self).__init__()
		if self._object is None:
			self.__class__._loadObject()
		self.x = x
		self.y = y
		self._instance = horizons.main.session.view.layers[LAYERS.GROUND].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), "")
		fife.InstanceVisual.create(self._instance)

class Water(WorldObject):
	def __init__(self, x ,y):
		"""
		@param x: int x position the water is created.
		@param y: int y position the water is created.
		"""
		super(Water, self).__init__()
		if self._object is None:
			self.__class__._loadObject()
		self.x = x
		self.y = y
		self._instance = horizons.main.session.view.layers[LAYERS.WATER].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), "")
		fife.InstanceVisual.create(self._instance)

class GroundClass(type):
	"""
	@param id: ground id.
	"""
	def __init__(self, id):
		self.id = id
		self._object = None
		self.velocity = {}
		for unit, straight, diagonal in horizons.main.db("SELECT unit, time_move_straight, time_move_diagonal FROM data.unit_velocity WHERE ground = ?", self.id):
			self.velocity[unit] = (straight, diagonal)
		self.classes = ['ground[' + str(id) + ']']
		for (name,) in horizons.main.db("SELECT class FROM data.ground_class WHERE ground = ?", id):
			self.classes.append(name)

	def __new__(self, id):
		"""
		@param id: ground id.
		"""
		if id == 4:
			return type.__new__(self, 'Ground[' + str(id) + ']', (Water,), {})
		else:
			return type.__new__(self, 'Ground[' + str(id) + ']', (Ground,), {})

	def _loadObject(self):
		""" Loads the ground object from the db (animations, etc)
		"""
		#print 'Loading ground #' + str(self.id) + '...'
		try:
			self._object = horizons.main.session.view.model.createObject(str(self.id), 'ground')
		except RuntimeError:
			#print 'already loaded...'
			self._object = horizons.main.session.view.model.getObject(str(self.id), 'ground')
			return
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()

		animation_45, animation_135, animation_225, animation_315 = horizons.main.db("SELECT (select file from data.animation where animation_id = animation_45 limit 1), (select file from data.animation where animation_id = animation_135 limit 1), (select file from data.animation where animation_id = animation_225 limit 1), (select file from data.animation where animation_id = animation_315 limit 1) FROM data.ground WHERE rowid = ?", self.id)[0]
		for rotation, file in [(45, animation_45), (135, animation_135), (225, animation_225), (315, animation_315)]:
			img = horizons.main.fife.imagepool.addResourceFromFile(file)
			visual.addStaticImage(int(rotation), img)
			# Get Image call unecessarily triggers loading of the actual image.
			#img = horizons.main.fife.imagepool.getImage(img)
			#img.setXShift(0)
			#img.setYShift(0)
