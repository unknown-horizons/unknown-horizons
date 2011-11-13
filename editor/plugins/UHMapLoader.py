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

import horizons.main # necessary so the correct load order of all modules is guaranteed
from horizons.util.dbreader import DbReader
from horizons.util.loaders import TileSetLoader
from horizons.util import SQLiteAnimationLoader
from horizons.constants import PATHS, VIEW

import os.path

from fife import fife
import fife.extensions.loaders as mapLoaders
import scripts.editor
import scripts.plugin

def getUHPath():
	"""Stores the UH path"""
	def up(path):
		return os.path.split(path)[0]
	return up(up(os.path.abspath(horizons.main.__file__)))

class MapLoader:

	GRID_TYPE = "square"
	GROUND_LAYER_NAME = "ground"

	time_to_load = 0

	def __init__(self, engine, callback, debug, extensions):
		""" Initialize the map loader """
		self._engine = engine
		self._callback = callback
		self._debug = debug

	def isLoadable(self, path):
		return True

	def loadResource(self, path):

		""" Loads the map from the given sqlite file """
		model = self._engine.getModel()
		map = model.createMap(path)
		grid = model.getCellGrid(self.GRID_TYPE)

		# add layers
		ground_layer = map.createLayer(self.GROUND_LAYER_NAME, grid)

		# add camera
		cam = map.addCamera("main", ground_layer, fife.Rect(0, 0, 640, 480))
		cam.setCellImageDimensions(*VIEW.CELL_IMAGE_DIMENSIONS)
		cam.setRotation(VIEW.ROTATION)
		cam.setTilt(VIEW.TILT)
		cam.setZoom(VIEW.ZOOM)

		map_db = DbReader(os.path.join(getUHPath(), path))
		# TODO: check the map version number

		# load all islands
		islands = map_db("SELECT x, y, file FROM island")
		for island in islands:
			self._loadIsland(ground_layer, model, *island)

		return map

	def _loadIsland(self, ground_layer, model, ix, iy, file):
		""" Loads an island from the given file """
		island_db = DbReader(os.path.join(getUHPath(), file))

		ground_tile = model.getObject('ts_beach0', 'ground')

		# load ground tiles
		ground = island_db("SELECT x, y FROM ground")
		for (x, y) in ground:
			position = fife.ModelCoordinate(ix + x, iy + y, 0)
			inst = ground_layer.createInstance(ground_tile, position)
			fife.InstanceVisual.create(inst)

class UHMapLoader(scripts.plugin.Plugin):
	""" The B{UHMapLoader} allows to load the UH map format in FIFEdit """

	def __init__(self):
		# Editor instance
		self._editor = None

		# Plugin variables
		self._enabled = False

		# Current mapview
		self._mapview = None


	#--- Plugin functions ---#
	def enable(self):
		""" Enable plugin """
		if self._enabled is True:
			return

		# Fifedit plugin data
		self._editor = scripts.editor.getEditor()
		self._engine = self._editor.getEngine()

		# load UH objects
		self._fixupFife()
		self._fixupHorizons()
		self._loadObjects()

		mapLoaders.addMapLoader('sqlite', MapLoader)
		exts = list(mapLoaders.fileExtensions)
		exts.append('sqlite')
		mapLoaders.fileExtensions = tuple(exts)

	def disable(self):
		""" Disable plugin """
		if self._enabled is False:
			return

	def isEnabled(self):
		""" Returns True if plugin is enabled """
		return self._enabled;

	def getName(self):
		""" Return plugin name """
		return u"UHMapLoader"

	#--- End plugin functions ---#

	def _fixupHorizons(self):
		"""Fixes some UH quirks that have to do with globals"""
		class PatchedFife:
			imagemanager = self._engine.getImageManager()
			pass
		horizons.main.fife = PatchedFife()

	def _fixupFife(self):
		"""Fixes some FIFE quirks that have to do with VFS"""
		vfs = self._engine.getVFS()
		vfs.addNewSource(getUHPath())
		vfs.addNewSource("/")

	def _loadObjects(self):
		# get fifedit objects
		model = self._engine.getModel()
		tile_set_path = os.path.join(getUHPath(), PATHS.TILE_SETS_DIRECTORY)

		# load all tiles
		TileSetLoader.load(tile_set_path)
		tile_sets = TileSetLoader.get_sets()
		animationloader = SQLiteAnimationLoader()

		for tile_set_id in tile_sets:
			tile_set = tile_sets[tile_set_id]
			object = model.createObject(str(tile_set_id), 'ground')
			fife.ObjectVisual.create(object)

			# load animations
			for action_id in tile_sets[tile_set_id].iterkeys():
				action = object.createAction(action_id+"_"+str(tile_set_id))
				fife.ActionVisual.create(action)
				for rotation in tile_sets[tile_set_id][action_id].iterkeys():
					anim = animationloader.loadResource( \
						str(tile_set_id)+"+"+str(action_id)+"+"+ \
						str(rotation) + ':shift:center+0,bottom+8')
					action.get2dGfxVisual().addAnimation(int(rotation), anim)
					action.setDuration(anim.getDuration())

