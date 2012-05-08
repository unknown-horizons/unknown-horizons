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

import horizons.main # this must be the first import, so the correct load order of all modules is guaranteed
from horizons.util.yamlcache import YamlCache
from horizons.util import SQLiteAnimationLoader, ActionSetLoader, TileSetLoader
from horizons.constants import PATHS, VIEW

import os
import yaml
import fnmatch

from fife import fife
import fife.extensions.loaders as mapLoaders
import scripts.editor
import scripts.plugin

import util

YamlCache.sync_scheduled = True

class UHObjectLoader(scripts.plugin.Plugin):
	""" The B{UHObjectLoader} allows to load the UH objects into the FIFEdit object selector """

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

	def disable(self):
		""" Disable plugin """
		if self._enabled is False:
			return

	def isEnabled(self):
		""" Returns True if plugin is enabled """
		return self._enabled;

	def getName(self):
		""" Return plugin name """
		return u"UHObjectLoader"

	#--- End plugin functions ---#

	def _fixupHorizons(self):
		"""Fixes some UH quirks that have to do with globals"""
		class PatchedFife:
			imagemanager = self._engine.getImageManager()
			use_atlases = False
			pass
		horizons.main.fife = PatchedFife()
		uh_path = util.getUHPath()
		horizons.main.PATHS.TILE_SETS_DIRECTORY = os.path.join(uh_path, horizons.main.PATHS.TILE_SETS_DIRECTORY)
		horizons.main.PATHS.ACTION_SETS_DIRECTORY = os.path.join(uh_path, horizons.main.PATHS.ACTION_SETS_DIRECTORY)
		horizons.main.PATHS.DB_FILES = map(lambda file: os.path.join(uh_path, file), horizons.main.PATHS.DB_FILES)

	def _fixupFife(self):
		"""Fixes some FIFE quirks that have to do with VFS"""
		vfs = self._engine.getVFS()
		vfs.addNewSource(util.getUHPath())
		vfs.addNewSource("/")

	def _loadObjects(self):
		# get fifedit objects
		self.model = self._engine.getModel()
		self.all_action_sets = ActionSetLoader.get_sets()

		TileSetLoader.load()
		ActionSetLoader.load()
		self.animationloader = SQLiteAnimationLoader()

		self._loadGroundTiles()
		self._loadBuildings()

	def _loadGroundTiles(self):
		print("loading UH ground tiles...")
		tile_sets = TileSetLoader.get_sets()

		for tile_set_id in tile_sets:
			tile_set = tile_sets[tile_set_id]
			object = self.model.createObject(str(tile_set_id), util.GROUND_NAMESPACE)
			fife.ObjectVisual.create(object)

			# load animations
			for action_id in tile_sets[tile_set_id].iterkeys():
				action = object.createAction(action_id+"_"+str(tile_set_id))
				fife.ActionVisual.create(action)
				for rotation in tile_sets[tile_set_id][action_id].iterkeys():
					anim = self.animationloader.loadResource( \
						str(tile_set_id)+"+"+str(action_id)+"+"+ \
						str(rotation) + ':shift:center+0,bottom+8')
					action.get2dGfxVisual().addAnimation(int(rotation), anim)
					action.setDuration(anim.getDuration())

	def _loadBuildings(self):
		print("loading UH buildings...")
		for root, dirnames, filenames in os.walk(util.getUHPath() + '/content/objects/buildings'):
			for filename in fnmatch.filter(filenames, '*.yaml'):
				# This is needed for dict lookups! Do not convert to os.join!
				full_file = root + "/" + filename
				result = YamlCache.get_file(full_file, game_data=True)
				result['yaml_file'] = full_file
				self._loadBuilding(result)

		print("finished loading UH objects")

	def _loadBuilding(self, yaml):
		id = int(yaml['id'])
		name_data = yaml['name']
		if isinstance(name_data, dict): # level-sensitive names as dict
			name_data = sorted(name_data.iteritems())[0][1]
		name = name_data[2:] # drop translation mark
		size_x = yaml['size_x']
		size_y = yaml['size_y']
		action_sets = yaml['actionsets']
		object = self.model.createObject(str(name), util.BUILDING_NAMESPACE)
		fife.ObjectVisual.create(object)

		main_action = 'idle'
		for action_set_list in action_sets.itervalues():
			for action_set_id in action_set_list.iterkeys():
				for action_id in self.all_action_sets[action_set_id].iterkeys():
					main_action = action_id+"_"+str(action_set_id)
					action = object.createAction(main_action)
					fife.ActionVisual.create(action)
					for rotation in self.all_action_sets[action_set_id][action_id].iterkeys():
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
						anim = self.animationloader.loadResource(str(action_set_id)+"+"+str(action_id)+"+"+str(rotation) + ':shift:' + command)
						action.get2dGfxVisual().addAnimation(int(rotation), anim)
						action.setDuration(anim.getDuration())

		util.addBuilding(id, name, main_action)

