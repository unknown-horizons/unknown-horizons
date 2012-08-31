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

import os
import re
import glob
import logging

from horizons.constants import ACTION_SETS

class GeneralLoader(object):
	"""The ActionSetLoader loads action sets from a directory tree. The directories loaded
	begin with 'as_' to tell tell the loader that they are an action set. directory
	structure is as follows: <action_set>/<action>/<rotation>/<framenumber>.png
	for example that would be: fisher1/work/90/0.png
	Note that all directories except for the rotation dir, all dirs have to be empty and
	must not include additional action sets.
	@param start_dir: directory that is used to begin search in
	"""

	log = logging.getLogger("util.loaders.loader")

	@classmethod
	def _load_files(cls, directory, time):
		"""Loads the files for a specific rotation
		@param directory: directory to load files from. Example:
		                 'content/gfx/units/lumberjack/'
		@return: dict of 'file: anim_end' items
		"""
		files = glob.glob(os.path.join(directory, "*.png"))
		# Make sure entries are in the correct order: 'zz1.png' < '2.png' < '09.png'
		files.sort(key=lambda f: int(re.search(r'\d+', os.path.basename(f)).group()))

		anim_length = {} # dict containing 'file: anim_end' items
		for i, filename in enumerate(files, start=1):
			anim_length[filename] = i * (time/1000.0) / len(files)
		return anim_length

	@classmethod
	def _load_rotation(cls, directory):
		"""Loads the rotations + files for a specific action
		@param directory: directory to load files from. Example:
		                 'content/gfx/units/lumberjack/'
		@return: dict of 'rotation: filedict' items. See _load_files for example.
		"""
		dirs = cls._action_set_directories(directory)

		for dirname in dirs:
			if dirname.startswith("tm_"):
				time = int(dirname.split('_')[1])
				dirs.remove(dirname)
				break
		else:
			time = ACTION_SETS.DEFAULT_ANIMATION_LENGTH

		rotations = {}
		for dirname in dirs:
			try:
				rotations[int(dirname)] = cls._load_files(os.path.join(directory, dirname), time)
			except Exception as e:
				raise Exception("Failed to load action sets from %s with time %s: %s" %
							 (os.path.join(directory, dirname), time, e))
		return rotations


	@classmethod
	def _load_action(cls, directory):
		"""Loads the actions + rotations + files for a specific action
		@param directory: directory to load files from. Example:
		                 'content/gfx/units/lumberjack/'
		@return: dict of 'action: rotationdict' items. See _load_rotation for example.
		"""
		dirs = cls._action_set_directories(directory)
		actions = {}
		for dirname in dirs:
			if os.path.isdir(os.path.join(directory, dirname)):
				actions[dirname] = cls._load_rotation(os.path.join(directory, dirname))
		return actions

	@classmethod
	def _action_set_directories(cls, directory):
		"""Returns directories that are important for loading action sets.
		Discards everything else that we found living there in the past.
		"""
		junk = set(['.DS_Store', '.svn'])
		return [d for d in os.listdir(directory)
		          if not d in junk]
