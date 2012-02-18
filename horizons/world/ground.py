# -*- coding: utf-8 -*-
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

import logging

from fife import fife

import horizons.main

from horizons.constants import LAYERS, GROUND
from horizons.util.loaders import TileSetLoader

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
		self.session = session

		self._instance = session.view.layers[self.layer].createInstance(self._object, \
				                                                        fife.ModelCoordinate(int(x), int(y), 0), "")
		fife.InstanceVisual.create(self._instance)

	def __str__(self):
		return "SurfaceTile(id=%s, x=%s, y=%s, water=%s, obj=%s)" % \
			   (self.id, self.x, self.y, self.is_water, self.object)

	def act(self, action, rotation):
		self._instance.setRotation(rotation)

		facing_loc = fife.Location(self.session.view.layers[self.layer])
		x = self.x
		y = self.y
		layer_coords = list((x, y, 0))

		if rotation == 45:
			layer_coords[0] = x+3
		elif rotation == 135:
			layer_coords[1] = y-3
		elif rotation == 225:
			layer_coords[0] = x-3
		elif rotation == 315:
			layer_coords[1] = y+3
		facing_loc.setLayerCoordinates(fife.ModelCoordinate(*layer_coords))

		self._instance.act(action+"_"+str(self._tile_set_id), facing_loc, True)


class Ground(SurfaceTile):
	"""Default land surface"""
	pass

class Water(SurfaceTile):
	"""Default water surface"""
	is_water = True
	layer = LAYERS.WATER

class WaterDummy(Water):
	def __init__(self, session, x, y):
		# no super call, we don't have an instance
		self.x = x
		self.y = y

		self.settlement = None
		self.blocked = False
		self.object = None


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
		self.classes = ['ground[' + str(id) + ']']
		for (name,) in db("SELECT class FROM ground_class WHERE ground = ?", id):
			self.classes.append(name)
		if id != -1	:
			self._tile_set_id = db.get_random_tile_set(id)[0]
			self._loadObject(db)

	def __new__(self, db, id):
		"""
		@param id: ground id.
		"""
		if id == GROUND.WATER[0]:
			return type.__new__(self, 'Ground[' + str(id) + ']', (Water,), {})
		elif id == -1:
			return type.__new__(self, 'Ground[' + str(id) + ']', (WaterDummy,), {})
		else:
			return type.__new__(self, 'Ground[' + str(id) + ']', (Ground,), {})

	def _loadObject(cls, db):
		""" Loads the ground object from the db (animations, etc)
		"""
		cls.log.debug('Loading ground %s', cls.id)
		try:
			cls._object = horizons.main.fife.engine.getModel().createObject(str(cls.id), 'ground')
		except RuntimeError:
			cls.log.debug('Already loaded ground %s', cls.id)
			cls._object = horizons.main.fife.engine.getModel().getObject(str(cls.id), 'ground')
			return

		fife.ObjectVisual.create(cls._object)

		tile_sets = TileSetLoader.get_sets()
		for (tile_set_id,) in db("SELECT set_id FROM tile_set WHERE ground_id=?", cls.id):
			for action_id in tile_sets[tile_set_id].iterkeys():
				action = cls._object.createAction(action_id+"_"+str(tile_set_id))
				fife.ActionVisual.create(action)
				for rotation in tile_sets[tile_set_id][action_id].iterkeys():
					anim = horizons.main.fife.animationloader.loadResource( \
						str(tile_set_id)+"+"+str(action_id)+"+"+ \
						str(rotation) + ':shift:center+0,bottom+8')
					action.get2dGfxVisual().addAnimation(int(rotation), anim)
					action.setDuration(anim.getDuration())
