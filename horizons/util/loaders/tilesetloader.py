# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import logging
import os
from typing import Dict, List

import horizons.globals
from horizons.constants import PATHS
from horizons.util.loaders.jsondecoder import JsonDecoder
from horizons.util.loaders.loader import GeneralLoader


class TileSetLoader:
	"""The TileSetLoader loads tile sets from a directory tree. The directories loaded
	begin with 'ts_' to tell tell the loader that they are an action set. directory
	structure is as follows: <tile_set>/<rotation>/<framenumber>.png
	for example that would be: ts_shallow/90/0.png
	Note that all directories except for the rotation dir, all dirs have to be empty and
	must not include additional tile sets.
	"""

	log = logging.getLogger("util.loaders.tilesetloader")

	tile_sets = {} # type: Dict[str, Dict[str, Dict[int, Dict[str, List[float]]]]]
	_loaded = False

	@classmethod
	def _find_tile_sets(cls, dir):
		"""Traverses recursively starting from dir to find action sets.
		It is similar to os.walk, but more optimized for this use case."""
		for entry in sorted(os.listdir(dir)):
			full_path = os.path.join(dir, entry)
			if entry.startswith("ts_"):
				cls.tile_sets[entry] = GeneralLoader._load_action(full_path)
			else:
				if os.path.isdir(full_path) and entry != ".DS_Store":
					cls._find_tile_sets(full_path)

	@classmethod
	def load(cls):
		if not cls._loaded:
			cls.log.debug("Loading tile_sets...")
			if not horizons.globals.fife.use_atlases:
				cls._find_tile_sets(PATHS.TILE_SETS_DIRECTORY)
			else:
				cls.tile_sets = JsonDecoder.load(PATHS.TILE_SETS_JSON_FILE)
			cls.log.debug("Done!")
			cls._loaded = True

	@classmethod
	def get_sets(cls):
		if not cls._loaded:
			cls.load()
		return cls.tile_sets
