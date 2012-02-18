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
import logging

import horizons.main

from horizons.constants import PATHS
from loader import GeneralLoader
from jsondecoder import JsonDecoder

class ActionSetLoader(object):
	"""The ActionSetLoader loads action sets from a directory tree. The directories loaded
	begin with 'as_' to tell tell the loader that they are an action set. directory
	structure is as follows: <action_set>/<action>/<rotation>/<framenumber>.png
	for example that would be: fisher1/work/90/0.png
	Note that all directories except for the rotation dir, all dirs have to be empty and
	must not include additional action sets.
	@param start_dir: directory that is used to begin search in"""

	log = logging.getLogger("util.loaders.actionsetloader")

	action_sets = {}
	_loaded = False

	@classmethod
	def _find_action_sets(cls, dir):
		"""Traverses recursively starting from dir to find action sets.
		It is similar to os.walk, but more optimized for this use case."""
		for entry in os.listdir(dir):
			full_path = os.path.join(dir, entry)
			if entry.startswith("as_"):
				cls.action_sets[entry] = GeneralLoader._load_action(full_path)
			else:
				if os.path.isdir(full_path) and entry != ".svn" and entry != ".DS_Store":
					cls._find_action_sets(full_path)

	@classmethod
	def load(cls):
		if not cls._loaded:
			cls.log.debug("Loading action_sets...")
			if not horizons.main.fife.use_atlases:
				cls._find_action_sets(PATHS.ACTION_SETS_DIRECTORY)
			else:
				cls.action_sets = JsonDecoder.load(PATHS.ACTION_SETS_JSON_FILE)
			cls.log.debug("Done!")
			cls._loaded = True

		#for key, value in cls.action_sets.iteritems():
		#	print "Action_set:" , key
		#	for key1, value1 in value.iteritems():
		#		print "Action:", key1
		#		for key2, value2 in value1.iteritems():
		#			print "Rotation:", key2
		#			for key3, value3 in value2.iteritems():
		#				print "File:", key3, "length:", value3

	@classmethod
	def get_sets(cls):
		if not cls._loaded:
			cls.load()
		return cls.action_sets