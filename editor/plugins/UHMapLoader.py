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
from horizons.util import SQLiteAnimationLoader, ActionSetLoader, TileSetLoader
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

		# make layer the active layer
		fife.InstanceRenderer.getInstance(cam).addActiveLayer(ground_layer)
		fife.GridRenderer.getInstance(cam).addActiveLayer(ground_layer)
		fife.BlockingInfoRenderer.getInstance(cam).addActiveLayer(ground_layer)
		fife.CoordinateRenderer.getInstance(cam).addActiveLayer(ground_layer)
		fife.CellSelectionRenderer.getInstance(cam).addActiveLayer(ground_layer)
		fife.LightRenderer.getInstance(cam).addActiveLayer(ground_layer)
		fife.GenericRenderer.getInstance(cam).addActiveLayer(ground_layer)

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
			use_atlases = False
			pass
		horizons.main.fife = PatchedFife()
		uh_path = getUHPath()
		horizons.main.PATHS.TILE_SETS_DIRECTORY = os.path.join(uh_path, horizons.main.PATHS.TILE_SETS_DIRECTORY)
		horizons.main.PATHS.ACTION_SETS_DIRECTORY = os.path.join(uh_path, horizons.main.PATHS.ACTION_SETS_DIRECTORY)
		horizons.main.PATHS.DB_FILES = map(lambda file: os.path.join(uh_path, file), horizons.main.PATHS.DB_FILES)

	def _fixupFife(self):
		"""Fixes some FIFE quirks that have to do with VFS"""
		vfs = self._engine.getVFS()
		vfs.addNewSource(getUHPath())
		vfs.addNewSource("/")

	def _loadObjects(self):
		# get fifedit objects
		model = self._engine.getModel()

		# get UH db and loaders
		db = horizons.main._create_db()
		TileSetLoader.load()
		ActionSetLoader.load()
		animationloader = SQLiteAnimationLoader()

		# load all ground tiles
		print("loading UH ground tiles...")
		tile_sets = TileSetLoader.get_sets()

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

		# load all buildings
		print("loading UH buildings...")
		all_action_sets = ActionSetLoader.get_sets()
		for (building_id, building_name) in db("SELECT id, name FROM building"):
			building_action_sets = db("SELECT action_set_id FROM action_set WHERE object_id=?", building_id)
			size_x, size_y = db("SELECT size_x, size_x FROM building WHERE id = ?", building_id)[0]
			object = model.createObject(str(building_name), 'building')
			fife.ObjectVisual.create(object)

			for (action_set_id,) in building_action_sets:
				for action_id in all_action_sets[action_set_id].iterkeys():
					action = object.createAction(action_id+"_"+str(action_set_id))
					fife.ActionVisual.create(action)
					for rotation in all_action_sets[action_set_id][action_id].iterkeys():
						if rotation == 45:
							command = 'left-32,bottom+' + str(size_x * 16)
						elif rotation == 135:
							command = 'left-' + str(size_y * 32) + ',bottom+16'
						elif rotation == 225:
							command = 'left-' + str((size_x + size_y - 1) * 32) + ',bottom+' + str(size_y * 16)
						elif rotation == 315:
							command = 'left-' + str(size_x * 32) + ',bottom+' + str((size_x + size_y - 1) * 16)
						else:
							assert False, "Bad rotation for action_set %(id)s: %(rotation)s for action: %(action_id)s" % \
								   { 'id': action_set_id, 'rotation': rotation, 'action_id': action_id }
						anim = animationloader.loadResource(str(action_set_id)+"+"+str(action_id)+"+"+str(rotation) + ':shift:' + command)
						action.get2dGfxVisual().addAnimation(int(rotation), anim)
						action.setDuration(anim.getDuration())

		print("finished loading UH objects")

