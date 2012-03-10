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

import horizons.main # necessary so the correct load order of all modules is guaranteed
from horizons.util.dbreader import DbReader
from horizons.util import SQLiteAnimationLoader, ActionSetLoader, TileSetLoader
from horizons.constants import PATHS, VIEW

import os.path

from fife import fife
import fife.extensions.loaders as mapLoaders
import scripts.editor
import scripts.plugin

import util

class MapLoader:

	GRID_TYPE = "square"

	time_to_load = 0

	def __init__(self, engine, callback, debug, extensions):
		""" Initialize the map loader """
		self._engine = engine
		self._callback = callback
		self._debug = debug
		self._cam = None

	def isLoadable(self, path):
		return True

	def loadResource(self, path):
		""" Loads the map from the given sqlite file """
		# creates absolute path to mapfile
		path = os.path.join(util.getUHPath(), path)
		model = self._engine.getModel()
		map = model.createMap(path)
		map.setFilename(path)
		
		grid = model.getCellGrid(self.GRID_TYPE)

		# add layers
		ground_layer = map.createLayer(util.GROUND_LAYER_NAME, grid)
		building_layer = map.createLayer(util.BUILDING_LAYER_NAME, grid)

		# add camera
		self._createCamera(building_layer, map)

		map_db = DbReader(path)
		# TODO: check the map version number

		# load all islands
		islands = map_db("SELECT x, y, file FROM island")
		for island in islands:
			name = island[2]
			if name[0:6] == "random":
				raise RuntimeError("Map contains random generated islands. Cannot load that")

		for island in islands:
			self._loadIsland(ground_layer, model, *island)

		# load all buildings
		self._loadBuildings(building_layer, model, map_db)

		return map

	def _createCamera(self, layer, map):
		# add camera
		cam = map.addCamera("main", layer, fife.Rect(0, 0, 640, 480))
		cam.setCellImageDimensions(*VIEW.CELL_IMAGE_DIMENSIONS)
		cam.setRotation(VIEW.ROTATION)
		cam.setTilt(VIEW.TILT)
		cam.setZoom(VIEW.ZOOM)

		# make layer the active layer
		fife.InstanceRenderer.getInstance(cam).activateAllLayers(map)
		fife.GridRenderer.getInstance(cam).activateAllLayers(map)
		fife.BlockingInfoRenderer.getInstance(cam).activateAllLayers(map)
		fife.CoordinateRenderer.getInstance(cam).activateAllLayers(map)
		fife.CellSelectionRenderer.getInstance(cam).activateAllLayers(map)
		fife.LightRenderer.getInstance(cam).activateAllLayers(map)
		fife.GenericRenderer.getInstance(cam).activateAllLayers(map)
		
	def act(self, action, rotation, instance, layer, x, y):
		instance.setRotation(rotation)

		facing_loc = fife.Location(layer)
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

		instance.act(action, facing_loc, True)

	def _loadIsland(self, ground_layer, model, ix, iy, file):
		""" Loads an island from the given file """
		island_db = DbReader(os.path.join(util.getUHPath(), file))

		# load ground tiles
		ground = island_db("SELECT x, y, ground_id, action_id, rotation FROM ground")
		for (x, y, ground_id, action_id, rotation) in ground:
			groundTileName = util.getGroundTileName(ground_id)
			ground_tile = model.getObject(groundTileName, util.GROUND_NAMESPACE)
			x = ix + x
			y = iy + y
			position = fife.ModelCoordinate(x, y, 0)
			inst = ground_layer.createInstance(ground_tile, position)
			self.act(action_id+"_"+str(groundTileName), rotation, inst, ground_layer, x, y)
			fife.InstanceVisual.create(inst)

	def _loadBuildings(self, building_layer, model, db):
		""" Loads all buildings from the given db and places them on the map """
		buildings = db("SELECT type, x, y, rotation FROM building")
		for (id, x, y, rotation) in buildings:
			name = util.getBuildingName(id)
			object = model.getObject(name, util.BUILDING_NAMESPACE)
			action_id = util.getBuildingActionId(id)
			
			facing_loc = fife.Location(building_layer)
			instance_coords = list((x, y, 0))
			layer_coords = list((x, y, 0))
	
			# NOTE:
			# nobody actually knows how the code below works.
			# it's for adapting the facing location and instance coords in
			# different rotations, and works with all quadratic buildings (tested up to 4x4)
			# for the first unquadratic building (2x4), a hack fix was put into it.
			# the plan for fixing this code in general is to wait until there are more
			# unquadratic buildings, and figure out a pattern of the placement error,
			# then fix that generally.
			
			size = (3, 3)
	
			if rotation == 45:
				layer_coords[0] = x+size[0]+3
	
				if size[0] == 2 and size[1] == 4:
					# HACK: fix for 4x2 buildings
					instance_coords[0] -= 1
					instance_coords[1] += 1
	
			elif rotation == 135:
				instance_coords[1] = y + size[1] - 1
				layer_coords[1] = y-size[1]-3
	
				if size[0] == 2 and size[1] == 4:
					# HACK: fix for 4x2 buildings
					instance_coords[0] += 1
					instance_coords[1] -= 1
	
			elif rotation == 225:
				instance_coords = list(( x + size[0] - 1, y + size[1] - 1, 0))
				layer_coords[0] = x-size[0]-3
	
				if size[0] == 2 and size[1] == 4:
					# HACK: fix for 4x2 buildings
					instance_coords[0] += 1
					instance_coords[1] -= 1
	
			elif rotation == 315:
				instance_coords[0] = x + size[0] - 1
				layer_coords[1] = y+size[1]+3
	
				if size[0] == 2 and size[1] == 4:
					# HACK: fix for 4x2 buildings
					instance_coords[0] += 1
					instance_coords[1] -= 1
	
			else:
				return None
			
			inst = building_layer.createInstance(object, fife.ModelCoordinate(*instance_coords))
			inst.setRotation(rotation)
			facing_loc.setLayerCoordinates(fife.ModelCoordinate(*layer_coords))
			fife.InstanceVisual.create(inst)
			inst.act(action_id, facing_loc, True)

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

		mapLoaders.addMapLoader('sqlite', MapLoader)

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

