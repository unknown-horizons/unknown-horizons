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

from horizons.util.uhdbaccessor import UhDbAccessor, read_savegame_template, \
	read_island_template
import fife.extensions.savers as mapSavers
import os.path
import re
import scripts.editor
import scripts.plugin
import shutil
import util

TEMPLATE_DATAFORMAT_PATH = os.path.join(util.getUHPath(), 'content', 'savegame_template.sql')

class MapSaver:
	def __init__(self, filepath, engine, map, importList):
		# copy template to save map
		self._filepath = filepath
		self._engine = engine
		self._model = engine.getModel()
		self._map = map
		self._mapDatabase = None

	def _fixRotation(self, rotation):
		"""
		Fixes FIFEs botched handling of rotations.
		Rotations are a) 0, 90, 180 or 270 and b) sometimes
		off by one.
		"""
		rotation = rotation % 360
		if (0 <= rotation and rotation < 45) or (315 <= rotation and rotation < 360):
			rotation = 45
		elif 45 <= rotation and rotation < 135:
			rotation = 135
		elif 135 <= rotation and rotation < 225:
			rotation = 225
		elif 225 <= rotation and rotation < 315:
			rotation = 315
		return rotation

	def _extractPositionRotationFromInstance(self, instance):
		"""Extracts the position and the rotation from an instance and returns it as a tuple"""
		rotation = self._fixRotation(instance.getRotation())
		position = instance.getLocationRef().getExactLayerCoordinates()
		return (position, rotation)

	def _saveBuildings(self):
		"""Saves all objects placed on the building layer"""
		building_layer = self._map.getLayer(util.BUILDING_LAYER_NAME)
		instances = building_layer.getInstances()
		for instance in instances:
			type = util.getBuildingId(instance.getObject().getId())
			(position, rotation) = self._extractPositionRotationFromInstance(instance)
			self._mapDatabase("INSERT INTO building VALUES (?, ?, ?, ?, ?, ?)", type, position.x, position.y, 1, rotation, 0)


	def _saveIslands(self):
		"""Saves all islands by calling _saveIsland on each of them and linking the generated islands to the MapFile"""
		tiles = self._buildGroundTilesLayerArray()
		tiles = self._partitionGroundtilesToIslands(tiles)
		islandsToGroundtiles = self._partitionIslandsFromGroundTiles(tiles)
		for islandName in islandsToGroundtiles:
			island_filename = os.path.basename(self._filepath)
			relative_island_filepath = os.path.join('content', 'islands', island_filename + "_" + islandName + ".sqlite")

			self._saveIsland(islandName, relative_island_filepath, islandsToGroundtiles[islandName])
			self._mapDatabase("INSERT INTO island VALUES (?, ?, ?)", 0, 0, relative_island_filepath)


	def _saveIsland(self, name, relative_island_filepath, tiles):
		"""Writes an SQL file for an island"""
		island_filepath = os.path.join(util.getUHPath(), relative_island_filepath)
		print "Saving island " + island_filepath
		if os.path.exists(island_filepath):
			os.remove(island_filepath)
		island_db = self._create_island_db(island_filepath)
		island_db("BEGIN IMMEDIATE TRANSACTION")

		for instance in tiles:
			type = util.getGroundTileId(instance.getObject().getId())
			# TODO (MMB) "default action id = 0"
			action_id = instance.getObject().getActionIds()[0]
			if instance.getCurrentAction() != None:
				action_id = instance.getCurrentAction().getId()
			# TODO (MMB) a bit of a hack to only get the name without a possible _ts_curved etc. suffix
			action_id = re.sub("_ts.*", "", action_id)
			(position, rotation) = self._extractPositionRotationFromInstance(instance)
			island_db("INSERT INTO ground VALUES (?, ?, ?, ?, ?)", position.x, position.y, type, action_id, rotation)
		island_db("COMMIT TRANSACTION");

		pass

	def _buildGroundTilesLayerArray(self):
		"""Builds a tuple representation of all the ground tiles"""
		# A representation of all the tiles, syntax is tiles(x, y, instance of groundtile)
		tiles = {}

		# Builds an x,y representation of all groundtiles
		ground_layer = self._map.getLayer(util.GROUND_LAYER_NAME)
		instances = ground_layer.getInstances()
		self.x_minimum = 0
		self.x_maximum = 0
		self.y_minimum = 0
		self.y_maximum = 0
		for instance in instances:
			type = util.getGroundTileId(instance.getObject().getId())
			(position, rotation) = self._extractPositionRotationFromInstance(instance)
			x = int(position.x)
			y = int(position.y)
			tiles[(x, y)] = ("island_0", instance)
			if x < self.x_minimum:
				self.x_minimum = x
			elif x > self.x_maximum:
				self.x_maximum = x
			if y > self.y_maximum:
				self.y_maximum = y
			elif y < self.y_minimum:
				self.y_minimum = y
		return tiles

	def _partitionGroundtilesToIslands(self, tiles):
		"""Builds partitions from the ground tiles so that an island consists of all connected groundtiles. Each groundtile is connected to an island"""
		islandCounter = 1
		for x in range(self.x_minimum, self.x_maximum + 1):
			for y in range(self.y_minimum, self.y_maximum + 1):
				try:
					(connectedIsland, instance) = tiles[(x, y)]
					isConnected = False

					try:
						if tiles[(x - 1, y)] != None:
							# Tile not yet connected
							# Left connect of unconnected groundtile to existing island
							(connectedIsland, tmpInstance) = tiles[(x - 1, y)]
							tiles[(x, y)] = (connectedIsland, instance)
							isConnected = True
					except KeyError:
						pass

					try:
						if tiles[(x, y - 1)] != None:
							# Up connect of unconnected groundtile to existing island
							if isConnected == False:
								# Tile not yet connected
								(connectedIsland, tmpInstance) = tiles[(x, y - 1)]
								tiles[(x, y)] = (connectedIsland, instance)
								isConnected = True

							else:
								# Tile already connected to other island this.
								# -> Merge the two islands by replacing references of the first one with the second one.
								(oldIsland, tmpInstance) = tiles[(x, y - 1)]
								if oldIsland != connectedIsland:
									tiles = self._updateExistingIslandName(tiles, oldIsland, connectedIsland)
					except KeyError:
						pass
					if isConnected == False:
						# Tile not yet connected
						# Create new island
						tiles[(x, y)] = ("island_" + str(islandCounter), instance)
						islandCounter += 1
				except KeyError:
					pass
		return tiles


	def _updateExistingIslandName(self, tiles, oldIsland, newIsland):
		"""Replaces occurrences from oldIsland to newIsland"""
		for (x, y) in tiles:
			(name, instance) = tiles[(x, y)]
			if name == oldIsland:
				tiles[(x, y)] = (newIsland, instance)
		return tiles


	def _partitionIslandsFromGroundTiles(self, tiles):
		islandsToGroundtiles = {}
		for (x, y) in tiles:
			(islandName, instance) = tiles[(x, y)]
			try:
				islandsToGroundtiles[islandName].append(instance)
			except KeyError:
				islandsToGroundtiles[islandName] = [instance, ]
		return islandsToGroundtiles

	def saveResource(self):
		try:
			if os.path.exists(self._filepath):
				backuppath = self._filepath + "_backup.sqlite"
				shutil.move(self._filepath, backuppath)
			self._mapDatabase = self._create_map_db(self._filepath)
		except IOError as exception:
			print "Did not save map!"
			raise exception
		else:
			# transaction save operations to gain performance
			self._mapDatabase("BEGIN IMMEDIATE TRANSACTION")
			self._saveBuildings()
			self._saveIslands()
			self._mapDatabase("COMMIT TRANSACTION");

			print "Successfully saved " + self._filepath

	def _create_map_db(self, savepath):
		"""Returns a dbreader instance, that is connected to the main game data dbfiles."""
		horizons.main.PATHS.SAVEGAME_TEMPLATE = os.path.join(util.getUHPath(), horizons.main.PATHS.SAVEGAME_TEMPLATE)

		db = UhDbAccessor(savepath)
		read_savegame_template(db)
		return db

	def _create_island_db(self, savepath):
		"""Returns a dbreader instance for the creation of island dbfiles."""
		horizons.main.PATHS.ISLAND_TEMPLATE = os.path.join(util.getUHPath(), horizons.main.PATHS.ISLAND_TEMPLATE)

		db = UhDbAccessor(savepath)
		read_island_template(db)
		return db

class UHMapSaver(scripts.plugin.Plugin):
	""" The {UHMapSaver} allows to save the UH map format in FIFEdit
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
		mapSavers.addMapSaver('sqlite', MapSaver)

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
		return u"UHMapSaver"

	#--- End plugin functions ---#


