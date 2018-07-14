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

import json
import logging
import os
import os.path
import shutil
import tempfile
from collections import defaultdict
from sqlite3 import OperationalError
from typing import Any, DefaultDict, List, Optional, Tuple

from yaml.parser import ParserError

from horizons.constants import BUILDINGS, UNITS, VERSION
from horizons.entities import Entities
from horizons.util.dbreader import DbReader
from horizons.util.shapes import Rect
from horizons.util.yamlcache import YamlCache


class SavegameTooOld(Exception):
	def __init__(self, msg=None, revision=None):
		if msg is None:
			msg = "The savegame is too old!"
		if revision is not None:
			msg += " Revision: " + str(revision)
		super().__init__(msg)


class SavegameUpgrader:
	"""The class that prepares saved games to be loaded by the current version."""

	log = logging.getLogger("util.savegameupgrader")

	def __init__(self, path):
		super().__init__() # TODO: check if this call is needed
		self.original_path = path
		self.using_temp = False
		self.final_path = None # type: Optional[str]

	def _upgrade_to_rev77(self, db):
		#placeholder for future upgrade methods
		pass

	def _upgrade(self):
		# fix import loop
		from horizons.savegamemanager import SavegameManager
		metadata = SavegameManager.get_metadata(self.original_path)
		rev = metadata['savegamerev']

		if rev < VERSION.SAVEGAMEREVISION:
			if not SavegameUpgrader.can_upgrade(rev):
				raise SavegameTooOld(revision=rev)

			self.log.warning('Discovered old savegame file, auto-upgrading: {} -> {}'
						     .format(rev, VERSION.SAVEGAMEREVISION))
			db = DbReader(self.final_path)
			db('BEGIN TRANSACTION')

			# placeholder for future upgrade calls
			if rev < 77:
				self._upgrade_to_rev77(db)

			db('COMMIT')
			db.close()

	@classmethod
	def can_upgrade(cls, from_savegame_version):
		"""Checks whether a savegame can be upgraded from the current version"""
		if from_savegame_version >= VERSION.SAVEGAME_LEAST_UPGRADABLE_REVISION:
			return True
		else:
			return False

	def get_path(self):
		"""Return the path to the up-to-date version of the saved game."""
		if self.final_path is None:
			self.using_temp = True
			handle, self.final_path = tempfile.mkstemp(prefix='uh-savegame.' + os.path.basename(os.path.splitext(self.original_path)[0]) + '.', suffix='.sqlite')
			os.close(handle)
			shutil.copyfile(self.original_path, self.final_path)
			self._upgrade()
		return self.final_path

	def close(self):
		if self.using_temp:
			self.using_temp = False
			os.unlink(self.final_path)
		self.final_path = None
