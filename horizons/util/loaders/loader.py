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
import glob
import logging

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
	def _load_files(cls, dir, time):
		"""Loads the files for a specific rotation
		@param dir: directory that the files are to loaded from. Example:
		            'content/gfx/units/lumberjack/work/90/'
		@return: dict containing 'file: anim_end' entries
		"""
		fl = {}

		entries = glob.glob(os.path.join(dir, "*.png"))
		entries.sort() # Make sure entries are in the correct order

		i = 1
		for file in entries:
			fl[file] = ((float(time)/1000)/len(entries))*i
			i += 1
		return fl

	@classmethod
	def _load_rotation(cls, dir):
		"""Loads the rotations + files for a specific action
		@param dir: directory that the files are to loaded from. Example:
		            'content/gfx/units/lumberjack/work/'
		@return: dict containing 'rotation: filedict' entries. See _load_files for example.
		"""
		rotations = {}
		time = 500
		dirs = os.listdir(dir)
		try:
			dirs.remove('.svn')
			dirs.remove('.DS_Store')
		except ValueError: pass

		for dirname in dirs:
			if dirname.startswith("tm_"):
				time = dirname.split('_')[1]
				dirs.remove(dirname)
				break
		for dirname in dirs:
			try:
				rotations[int(dirname)] = cls._load_files(os.path.join(dir, dirname),time)
			except Exception as e:
				if dirname != '.DS_Store':
					raise Exception("Failed to load action sets from %s with time %s: %s" % \
				                	(os.path.join(dir, dirname), time, e))

		return rotations


	@classmethod
	def _load_action(cls, dir):
		"""Loads the actions + rotations + files for a specific action
		@param dir: directory that the files are to loaded from. Example:
		            'content/gfx/units/lumberjack/'
		@return: dict containing 'action: rotationdict' entries. See _load_rotation for example.
		"""
		actions = {}
		dirs = os.listdir(dir)
		try:
			dirs.remove('.svn')
			dirs.remove('.DS_Store')
		except ValueError: pass

		for dirname in dirs:
			if dirname != '.DS_Store':
				actions[dirname] = cls._load_rotation(os.path.join(dir, dirname))

		return actions