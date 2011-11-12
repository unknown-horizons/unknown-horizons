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
from horizons.constants import PATHS

import os.path

import fife.extensions.loaders as mapLoaders
import scripts.editor
import scripts.plugin

class MapLoader:

	GRID_TYPE = "square"
	GROUND_LAYER_NAME = "ground"

	def __init__(self, engine, callback, debug, extensions):
		""" Initialize the map loader """
		self._engine = engine
		self._callback = callback
		self._debug = debug

	def loadResource(self, path):
		""" Loads the map from the given sqlite file """
		model = self._engine.getModel()
		map = model.createMap("name") # TODO: get the model name from the db
		grid = map.getCellGrid(GRID_TYPE)

		# add layers
		ground_layer = map.createLayer(GROUND_LAYER_NAME, grid)

		map_db = DBReader(path)
		# TODO: check the map version number

		# load objects catalogue
		self._loadObjects(map_db, model)

		# load all islands
		islands = map_db("SELECT x, y, file FROM islands")
		for island in islands:
			self._loadIsland(ground_layer, *island)

	def _loadObjects(self, map_db, model):
		# get UH path
		def up(path):
			return os.path.split(path)[0]
		uh_path = up(up(os.path.abspath(horizons.main.__file__)))
		tile_set_path = os.path.join(uh_path, PATHS.TILE_SETS_DIRECTORY)

		# load all tiles
		TileSetLoader.load(tile_set_path)
		tiles = TileSetLoader.get_sets()
		print tiles

	def _loadIsland(self, ground_layer, x, y, file):
		""" Loads an island from the given file """
		island_db = DBReader(file)

		# load ground tiles
		ground = island_db("SELECT x, y FROM ground")
		for (x, y) in ground:
			pass # TODO: place ground tile

class UHMapLoader(scripts.plugin.Plugin):
	""" The {UHMapLoader} allows to load the UH map format in FIFEdit
	"""

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
		print("name")
		""" Return plugin name """
		return u"UHMapLoader"

	#--- End plugin functions ---#


