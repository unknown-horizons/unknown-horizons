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

import logging

from fife import fife

import horizons.main

from horizons.constants import LAYERS, GROUND

class SurfaceTile(object):
	is_water = False
	layer = LAYERS.GROUND
	def __init__(self, session, x, y):
		"""
		@param session: Session instance
		@param x: int x position the ground is created.
		@param y: int y position the ground is created.
		"""
		self.x = x
		self.y = y

		self.settlement = None
		self.blocked = False
		self.object = None

		self._instance = session.view.layers[self.layer].createInstance(self._object, \
		                    fife.ModelCoordinate(int(x), int(y), 0), "")
		fife.InstanceVisual.create(self._instance)

	def __str__(self):
		return "SurfaceTile(x=%s, y=%s, water=%s, obj=%s)" % \
		       (self.x, self.y, self.is_water, self.object)

class Ground(SurfaceTile):
	"""Default land surface"""
	pass

class Water(SurfaceTile):
	"""Default water surface"""
	is_water = True
	layer = LAYERS.WATER


class GroundClass(type):
	"""
	@param id: ground id.
	"""
	log = logging.getLogger('world')

	def __init__(self, db, id):
		"""
		@param id: id in db for this specific ground class
		@param db: DbReader instance to get data from
		"""
		self.id = id
		self._object = None
		self.velocity = {}
		for unit, straight, diagonal in db("SELECT unit, time_move_straight, time_move_diagonal FROM data.unit_velocity WHERE ground = ?", self.id):
			self.velocity[unit] = (straight, diagonal)
		self.classes = ['ground[' + str(id) + ']']
		for (name,) in db("SELECT class FROM data.ground_class WHERE ground = ?", id):
			self.classes.append(name)
		self._loadObject(db)

	def __new__(self, db, id):
		"""
		@param id: ground id.
		"""
		if id == GROUND.WATER:
			return type.__new__(self, 'Ground[' + str(id) + ']', (Water,), {})
		else:
			return type.__new__(self, 'Ground[' + str(id) + ']', (Ground,), {})

	def _loadObject(self, db):
		""" Loads the ground object from the db (animations, etc)
		"""
		self.log.debug('Loading ground %s', self.id)
		try:
			self._object = horizons.main.fife.engine.getModel().createObject(str(self.id), 'ground')
		except RuntimeError:
			self.log.debug('Already loaded ground %s', self.id)
			self._object = horizons.main.fife.engine.getModel().getObject(str(self.id), 'ground')
			return
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()

		animation_45, animation_135, animation_225, animation_315 = \
		     db("SELECT \
		     (SELECT file FROM data.animation WHERE animation_id = animation_45 limit 1), \
		     (SELECT file FROM data.animation WHERE animation_id = animation_135 limit 1), \
		     (SELECT file FROM data.animation WHERE animation_id = animation_225 limit 1), \
		     (SELECT file FROM data.animation WHERE animation_id = animation_315 limit 1) \
		     FROM data.ground WHERE id = ?", self.id)[0]
		for rotation, file in [(45, animation_45), (135, animation_135), (225, animation_225), (315, animation_315)]:
			img = horizons.main.fife.imagepool.addResourceFromFile(file)
			visual.addStaticImage(int(rotation), img)
