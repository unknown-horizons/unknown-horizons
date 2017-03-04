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

import glob
import logging
import os
import os.path
import re
import sqlite3
import tempfile
import time
from collections import defaultdict

import horizons.globals
import horizons.main
from horizons.constants import PATHS, VERSION
from horizons.util.dbreader import DbReader
from horizons.util.yamlcache import YamlCache


class SavegameManager(object):
	"""Controls savegamefiles.

	This class is rather a namespace than a "real" object, since it has no members.
	The instance in horizons.main is nevertheless important, since it creates
	the savegame directories

	The return value usually is a tuple: (list_of_savegame_files, list_of_savegame_names),
	where savegame_names are meant for displaying to the user.

	IMPORTANT:
	Whenever you make a change that breaks compatibility with old savegames,
	increment horizons/constants.py:VERSION.SAVEGAMEREVISION and add an
	upgrade path in horizons/util/savegameupgrader.py.
	"""
	log = logging.getLogger("savegamemanager")

	savegame_dir = os.path.join(PATHS.USER_DIR, "save")
	autosave_dir = os.path.join(savegame_dir, "autosave")
	multiplayersave_dir = os.path.join(savegame_dir, "multiplayer_save")
	quicksave_dir = os.path.join(savegame_dir, "quicksave")
	maps_dir = os.path.join("content", "maps")
	scenario_maps_dir = os.path.join("content", "scenariomaps")
	scenarios_dir = os.path.join("content", "scenarios")

	savegame_extension = "sqlite"
	scenario_extension = "yaml"

	autosave_basename = "autosave-"
	quicksave_basename = "quicksave-"

	multiplayersave_name_regex = r"^[0-9a-zA-Z _.-]+$" # don't just blindly allow everything

	save_filename_timeformat = u"{prefix}%Y-%m-%d--%H-%M-%S"
	autosave_filenamepattern = save_filename_timeformat.format(prefix=autosave_basename)
	quicksave_filenamepattern = save_filename_timeformat.format(prefix=quicksave_basename)

	# Use {{}} because this string is formatted twice and
	# {} is replaced in the second format() call.
	filename = u"{{directory}}{sep}{{name}}.{ext}".format(sep=os.path.sep, ext=savegame_extension)

	savegame_screenshot_width = 290

	# metadata of a savegame with default values
	savegame_metadata = {'timestamp': -1, 'savecounter': 0,
	                     'savegamerev': 0, 'rng_state': ""}
	savegame_metadata_types = {'timestamp': float, 'savecounter': int,
	                           'savegamerev': int, 'rng_state': str}

	@classmethod
	def init(cls):
		# create savegame directory if it does not exist
		for d in cls.autosave_dir, cls.quicksave_dir, cls.multiplayersave_dir:
			if not os.path.isdir(d):
				os.makedirs(d)

	@classmethod
	def __get_displaynames(cls, files):
		"""Returns player-facing names for the savegames *files*.

		@param files: iterable object containing strings.
		@return: list of names to be displayed for each file.
		"""
		displaynames = []
		def get_timestamp_string(savegameinfo):
			if savegameinfo['timestamp'] == -1:
				return u""
			timestamp = time.localtime(savegameinfo['timestamp'])
			try:
				return time.strftime('%c', timestamp).decode('utf-8')
			except UnicodeDecodeError:
				# With non-utf8 system locales this would crash (#2221).
				return u""

		for f in files:
			if f.startswith(cls.autosave_dir):
				name = u"Autosave {date}".format(date=get_timestamp_string(cls.get_metadata(f)))
			elif f.startswith(cls.quicksave_dir):
				name = u"Quicksave {date}".format(date=get_timestamp_string(cls.get_metadata(f)))
			else:
				name = os.path.splitext(os.path.basename(f))[0]

			if not isinstance(name, unicode):
				name = unicode(name, errors='replace') # only use unicode strings, guichan needs them
			displaynames.append(name)
		return displaynames

	@classmethod
	def __get_saves_from_dirs(cls, dirs, include_displaynames, filename_extension, order_by_date):
		"""Returns the savegame files in each directory in *dirs*. Internal method.

		@param include_displaynames: Whether to add player-readable names displayed in gui.
		"""
		if not filename_extension:
			filename_extension = cls.savegame_extension
		files = sorted((-os.path.getmtime(f) if order_by_date else 0, f)
		               for p in dirs for f in glob.glob(p + '/*.' + filename_extension)
		               if os.path.isfile(f))
		files = zip(*files)[1] if files else []
		if include_displaynames:
			return (files, cls.__get_displaynames(files))
		else:
			return (files,)

	@classmethod
	def create_filename(cls, savegamename):
		"""Returns the full path for a regular save of the name *savegamename*."""
		name = cls.filename.format(directory=cls.savegame_dir, name=savegamename)
		cls.log.debug("Savegamemanager: creating save-filename: %s", name)
		return name

	@classmethod
	def create_autosave_filename(cls):
		"""Builds filename for a new autosave."""
		prepared_filename = time.strftime(cls.autosave_filenamepattern)
		name = cls.filename.format(directory=cls.autosave_dir, name=prepared_filename)
		cls.log.debug("Savegamemanager: creating autosave-filename: %s", name)
		return name

	@classmethod
	def create_quicksave_filename(cls):
		"""Returns the filename for a quicksave"""
		prepared_filename = time.strftime(cls.quicksave_filenamepattern)
		name = cls.filename.format(directory=cls.quicksave_dir, name=prepared_filename)
		cls.log.debug("Savegamemanager: creating quicksave-filename: %s", name)
		return name

	@classmethod
	def create_multiplayer_quicksave_name(cls):
		"""Will create a name, not a path"""
		return "quicksave-" + str(time.time())

	@classmethod
	def create_multiplayer_autosave_name(cls):
		"""Will create a name, not a path"""
		return "autosave-" + str(time.time())

	@classmethod
	def create_multiplayersave_filename(cls, name):
		"""Builds filename for a multiplayer savegame *name*."""
		if not re.match(cls.multiplayersave_name_regex, name):
			err = "Smelly multiplayer filename detected: " + name
			cls.log.error(err)
			raise RuntimeError(err)

		name = cls.filename.format(directory=cls.multiplayersave_dir, name=name)
		cls.log.debug("Savegamemanager: creating multiplayersave-filename: %s", name)
		return name

	@classmethod
	def delete_dispensable_savegames(cls, autosaves=False, quicksaves=False):
		"""Delete oldest savegames that are no longer needed.

		This is usually called to make space for new savegames when the limit
		(defined in settings) for that kind of saves is reached.

		@param autosaves: set to True if autosaves should be cleaned.
		@param quicksaves: set to True if quicksaves should be cleaned.
		"""
		def tmp_del(pattern, limit):
			# Casting to int because get_uh_setting below returns floats like
			# 4.0 (the slider stepping is 1.0) but we use this value as index.
			limit = int(limit)
			files = sorted(glob.glob(pattern))
			for filename in files[:-limit]:
				os.unlink(filename)

		if autosaves:
			tmp_del("{}/*.{}".format(cls.autosave_dir, cls.savegame_extension),
			        horizons.globals.fife.get_uh_setting("AutosaveMaxCount"))
		if quicksaves:
			tmp_del("{}/*.{}".format(cls.quicksave_dir, cls.savegame_extension),
			        horizons.globals.fife.get_uh_setting("QuicksaveMaxCount"))

	@classmethod
	def get_recommended_number_of_players(cls, mapfile):
		"""Returns amount of players recommended for a map *mapfile*."""
		dbdata = DbReader(mapfile) \
			("SELECT value FROM properties WHERE name = ?", "players_recommended")
		if dbdata:
			return dbdata[0][0]
		else:
			return "undefined"

	@classmethod
	def get_metadata(cls, savegamefile):
		"""Returns metainfo of a savegame as dict."""
		metadata = cls.savegame_metadata.copy()
		if isinstance(savegamefile, list):
			return metadata
		db = DbReader(savegamefile)

		try:
			for key in metadata.iterkeys():
				result = db("SELECT `value` FROM `metadata` WHERE `name` = ?", key)
				if result:
					assert len(result) == 1
					metadata[key] = cls.savegame_metadata_types[key](result[0][0])
		except sqlite3.OperationalError as e:
			cls.log.warning('Warning: Cannot read savegame {file}: {exception}'
			                ''.format(file=savegamefile, exception=e))
			return metadata

		screenshot_data = None
		try:
			screenshot_data = db("SELECT value FROM metadata_blob where name = ?", "screen")[0][0]
		except IndexError:
			pass
		except sqlite3.OperationalError:
			pass
		metadata['screenshot'] = screenshot_data

		return metadata

	@classmethod
	def _write_screenshot(cls, db):
		# special handling for screenshot (as blob)
		screenshot_fd, screenshot_filename = tempfile.mkstemp()

		width = horizons.globals.fife.engine_settings.getScreenWidth()
		height = horizons.globals.fife.engine_settings.getScreenHeight()

		# hide whatever dialog we have
		dialog_hidden = False
		windows = horizons.main._modules.session.ingame_gui.windows
		if windows.visible:
			dialog_hidden = True
			windows.hide_all()
			# pump twice to make it work on some machines
			horizons.globals.fife.engine.pump()
			horizons.globals.fife.engine.pump()

		# scale to the correct width and adapt height with same factor
		factor = float(cls.savegame_screenshot_width) / width
		new_width = int(float(width) * factor)
		new_height = int(float(height) * factor)
		backend = horizons.globals.fife.engine.getRenderBackend()
		backend.captureScreen(screenshot_filename, new_width, new_height)

		if dialog_hidden:
			windows.show_all()
			horizons.globals.fife.engine.pump()

		screenshot_data = os.fdopen(screenshot_fd, "r").read()
		db("INSERT INTO metadata_blob values(?, ?)", "screen", sqlite3.Binary(screenshot_data))
		os.unlink(screenshot_filename)

	@classmethod
	def write_metadata(cls, db, savecounter, rng_state):
		"""Writes metadata into database *db*.

		@param db: DbReader instance.
		@param savecounter: int, how many times this file has been saved.
		"""
		metadata = cls.savegame_metadata.copy()
		metadata['timestamp'] = time.time()
		metadata['savecounter'] = savecounter
		metadata['savegamerev'] = VERSION.SAVEGAMEREVISION
		metadata['rng_state'] = rng_state

		for key, value in metadata.iteritems():
			db("INSERT INTO metadata(name, value) VALUES(?, ?)", key, value)

		cls._write_screenshot(db)

	@classmethod
	def get_regular_saves(cls, include_displaynames=True):
		"""Returns all savegames that were saved via the ingame save dialog.

		@param include_displaynames: Whether to add player-readable names displayed in gui.
		"""
		where = [cls.savegame_dir]
		cls.log.debug("Savegamemanager: regular saves from: %s", where)
		return cls.__get_saves_from_dirs(where, include_displaynames, None, True)

	@classmethod
	def get_maps(cls, include_displaynames=True):
		"""Returns all maps in content/maps/ and ~/.unknown-horizons/maps/.

		@param include_displaynames: Whether to add player-readable names displayed in gui.
		"""
		where = [cls.maps_dir, PATHS.USER_MAPS_DIR]
		cls.log.debug("Savegamemanager: get maps from %s", where)
		return cls.__get_saves_from_dirs(where, include_displaynames, None, False)

	@classmethod
	def get_map(cls, map_name):
		return os.path.join(cls.maps_dir, map_name + "." + cls.savegame_extension)

	@classmethod
	def get_multiplayersave_map(cls, name):
		return os.path.join(cls.multiplayersave_dir, name + "." + cls.savegame_extension)

	@classmethod
	def get_saves(cls, include_displaynames=True):
		"""Returns all savegames: regular, auto- and quicksaves.

		@param include_displaynames: Whether to add player-readable names displayed in gui.
		"""
		where = [cls.savegame_dir, cls.autosave_dir, cls.quicksave_dir]
		cls.log.debug("Savegamemanager: get saves from %s", where)
		return cls.__get_saves_from_dirs(where, include_displaynames, None, True)

	@classmethod
	def get_multiplayersaves(cls, include_displaynames=True):
		where = [cls.multiplayersave_dir]
		cls.log.debug("Savegamemanager: get saves from %s", where)
		return cls.__get_saves_from_dirs(where, include_displaynames, None, True)

	@classmethod
	def get_quicksaves(cls, include_displaynames=True):
		"""Returns all quicksave savegames."""
		where = [cls.quicksave_dir]
		cls.log.debug("Savegamemanager: quicksaves from: %s", where)
		return cls.__get_saves_from_dirs(where, include_displaynames, None, True)

	@classmethod
	def get_scenarios(cls, include_displaynames=True):
		"""Returns all scenarios"""
		where = [cls.scenarios_dir]
		cls.log.debug("Savegamemanager: scenarios from: %s", where)
		return cls.__get_saves_from_dirs(where, include_displaynames, cls.scenario_extension, False)

	@classmethod
	def get_available_scenarios(cls, include_displaynames=True, locales=False):
		"""Returns available scenarios."""
		translated_scenarios = defaultdict(list)
		scenarios = zip(*cls.get_scenarios(include_displaynames=True))
		for filename, scenario in scenarios:
			if not os.path.exists(filename):
				continue
			if not os.stat(filename).st_size:
				# file seems empty
				continue
			_locale = cls.get_scenario_metadata(scenario=scenario).get('locale', u'en')
			# sort into dictionary by english filename (without language suffix)
			english_name = scenario.split('_' + _locale)[0]
			translated_scenarios[english_name].append((_locale, filename))
		return translated_scenarios

	@classmethod
	def get_scenario_metadata(cls, scenario="", filename=""):
		"""Return the `metadata` dict for a scenario.

		Pass either the scenario name (*scenario*) or a .yaml *filename*.
		"""
		sfiles, snames = cls.get_scenarios(include_displaynames=True)
		if scenario:
			if scenario not in snames:
				cls.log.error("Error: Cannot find scenario '{name}'.".format(name=scenario))
				return {}
			index = snames.index(scenario)
		elif filename:
			if filename not in sfiles:
				cls.log.error("Error: Cannot find scenario '{name}'.".format(name=filename))
				return {}
			index = sfiles.index(filename)
		data = YamlCache.get_file(sfiles[index], game_data=True)
		return data.get('metadata', {})

	@classmethod
	def get_savegamename_from_filename(cls, savegamefile):
		"""Returns a displayable name, extracted from a filename"""
		name = os.path.splitext(os.path.basename(savegamefile))[0]
		cls.log.debug("Savegamemanager: savegamename: %s", name)
		return name

	@classmethod
	def get_filename_from_map_name(cls, map_name):
		for prefix in [cls.scenario_maps_dir, cls.maps_dir, PATHS.USER_MAPS_DIR]:
			path = prefix + os.sep + map_name + '.sqlite'
			if os.path.exists(path):
				return path
		return None
