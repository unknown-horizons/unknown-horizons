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

import fife.extensions.savers as mapSavers
from horizons.util.dbreader import DbReader
import horizons.main # necessary so the correct load order of all modules is guaranteed

import scripts.editor
import scripts.plugin

import os.path
import shutil

import util

TEMPLATE_DATAFORMAT_PATH = os.path.join(util.getUHPath(),'content','savegame_template.sqlite')

class MapSaver:
	def __init__(self, filepath, engine, map, importList):
		# copy template to save map
		self._filepath = filepath
		self._engine = engine
		self._model = engine.getModel()
		self._map = map
		self._mapDatabase = None
		pass
			
	def _saveBuildings(self):
		building_layer = self._map.getLayer(util.BUILDING_LAYER_NAME)
		instances = building_layer.getInstances()
		for instance in instances:
			type = util.getBuildingId(instance.getObject().getId())
			rotation = instance.getRotation()
			position = instance.getLocationRef().getExactLayerCoordinates()
			self._mapDatabase("INSERT INTO building VALUES (?, ?, ?, ?, ?, ?, ?)", type, position.x, position.y, 100, 1, rotation, 0)

	def saveResource(self):
		try:
			savepath = self._filepath + '.saved.sqlite'
			shutil.copy(TEMPLATE_DATAFORMAT_PATH, savepath)
		except IOError as exception:
			print "Did not save map!"
			raise exception
		else:	
			self._mapDatabase = DbReader(savepath)
			# transaction save operations to gain performance
			self._mapDatabase("BEGIN IMMEDIATE TRANSACTION")
			self._saveBuildings()
			self._mapDatabase("COMMIT TRANSACTION");
			
			print "Successfully saved " + savepath 
	
class UHMapSaver(scripts.plugin.Plugin):
	""" The {UHMapSaver} allows to load the UH map format in FIFEdit
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


