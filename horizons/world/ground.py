# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import horizons.globals
from horizons.constants import GROUND, LAYERS
from horizons.util.loaders.tilesetloader import TileSetLoader


class SurfaceTile:
	is_water = False
	layer = LAYERS.GROUND

	__slots__ = ('x', 'y', 'settlement', 'blocked', 'object', 'session', '_instance', '_tile_set_id')

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
		self._tile_set_id = horizons.globals.db.get_random_tile_set(self.id)

		layer = session.view.layers[self.layer]
		# actualy this should be x + 0.5, y + 0.5, since that's the center of the tile area
		# however, other code depends on the current alignment.
		# it this is changed, it should also be changed for buildings and units
		self._instance = layer.createInstance(self._fife_objects[self._tile_set_id],
		                                      fife.ExactModelCoordinate(x, y, 0),
		                                      "")
		fife.InstanceVisual.create(self._instance)

	def __str__(self):
		return ("SurfaceTile(id={}, shape={}, x={}, y={}, water={}, obj={})"
		       .format(self.id, self.shape, self.x, self.y, self.is_water, self.object))

	def act(self, rotation):
		self._instance.setRotation(rotation)

	@property
	def rotation(self):
		# workaround for FIFE's inconsistent rotation rounding
		return int(round(self._instance.getRotation() / 45.0)) * 45


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

	def __init__(self, db, id, shape):
		"""
		@param id: id in db for this specific ground class
		@param db: DbReader instance to get data from
		"""
		self.id = id
		self.shape = shape
		self._fife_objects = None
		self.velocity = {}
		self.classes = ['ground[' + str(id) + ']']
		for (name,) in db("SELECT class FROM ground_class WHERE ground = ?", id):
			self.classes.append(name)
		if id != -1	:
			self._loadObject(db)

	def __new__(self, db, id, shape):
		"""
		@param id: ground id.
		@param shape: ground shape (straight, curve_in, curve_out).
		"""
		if id == GROUND.WATER[0]:
			return type.__new__(self, 'Ground[{:d}-{}]'.format(id, shape), (Water,), {})
		elif id == -1:
			return type.__new__(self, 'Ground[{:d}-{}]'.format(id, shape), (WaterDummy,), {})
		else:
			return type.__new__(self, 'Ground[{:d}-{}]'.format(id, shape), (Ground,), {})

	def _loadObject(cls, db):
		"""Loads the ground object from the db (animations, etc)"""
		cls._fife_objects = {}
		tile_sets = TileSetLoader.get_sets()
		model = horizons.globals.fife.engine.getModel()
		load_image = horizons.globals.fife.animationloader.load_image
		tile_set_data = db("SELECT set_id FROM tile_set WHERE ground_id=?", cls.id)
		for tile_set_row in tile_set_data:
			tile_set_id = str(tile_set_row[0])
			cls_name = '{:d}-{}'.format(cls.id, cls.shape)
			cls.log.debug('Loading ground %s', cls_name)
			fife_object = None
			try:
				fife_object = model.createObject(cls_name, 'ground_' + tile_set_id)
			except fife.NameClash:
				cls.log.debug('Already loaded ground %d-%s', cls.id, cls.shape)
				fife_object = model.getObject(cls_name, 'ground_' + tile_set_id)
				return

			fife.ObjectVisual.create(fife_object)
			visual = fife_object.get2dGfxVisual()
			for rotation, data in tile_sets[tile_set_id][cls.shape].items():
				if not data:
					raise KeyError('No data found for tile set `{}` in rotation `{}`. '
						'Most likely the shape `{}` is missing.'
						.format(tile_set_id, rotation, cls.shape))
				if len(data) > 1:
					raise ValueError('Currently only static tiles are supported. '
						'Found this data for tile set `{}` in rotation `{}`: '
						'{}'.format(tile_set_id, rotation, data))
				img = load_image(list(data.keys())[0], tile_set_id, cls.shape, str(rotation))
				# make the drawing origin correspond with the center of the groundpart of the image
				# (instead of the center of the image)
				img.setYShift(int(img.getWidth() / 4 - img.getHeight() / 2))
				visual.addStaticImage(rotation, img.getHandle())

			# Save the object
			cls._fife_objects[tile_set_id] = fife_object


class MapPreviewTile:
	"""This class provides the minimal tile implementation for map preview."""

	def __init__(self, x, y, id):
		super().__init__() # TODO: check if this call is needed
		self.x = x
		self.y = y
		self.id = id
		self.classes = ()
		self.settlement = None
