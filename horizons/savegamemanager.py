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

import sqlite3
import tempfile
import logging
import os
import os.path
import glob
import time
import yaml

from horizons.constants import PATHS, VERSION
from horizons.util import DbReader, YamlCache

import horizons.main


class SavegameManager(object):
	"""Controls savegamefiles.

	This class is rather a namespace than a "real" object, since it has no members.
	The instance in horizons.main is nevertheless important, since it creates
	the savegame directories

	The return values is usually a tuple: (list_of_savegame_files, list_of_savegame_names),
	where savegame_names are meant for displaying to the user.


	IMPORTANT:
	Whenever you make a change that breaks compatibility with old savegames, increase
	horizons/constans.py:VERSION.SAVEGAMEREVISION by one !!
	"""
	log = logging.getLogger("savegamemanager")

	savegame_dir = os.path.join(PATHS.USER_DIR, "save")
	autosave_dir = os.path.join(savegame_dir, "autosave")
	quicksave_dir = os.path.join(savegame_dir, "quicksave")
	maps_dir = os.path.join("content", "maps")
	scenario_maps_dir = os.path.join("content", "scenariomaps")
	scenarios_dir = os.path.join("content", "scenarios")
	campaigns_dir = os.path.join("content", "campaign")

	savegame_extension = "sqlite"
	scenario_extension = "yaml"
	campaign_extension = "yaml"

	autosave_basename = "autosave-"
	quicksave_basename = "quicksave-"

	# Use {{}} because this string is formatted twice and
	# {timestamp} is replaced in the second format() call.
	save_filename_timeformat = u"{prefix}{{timestamp:.4f}}--%Y-%m-%d--%H-%M.{ext}"
	autosave_filenamepattern = save_filename_timeformat.format(prefix=autosave_basename, ext=savegame_extension)
	quicksave_filenamepattern = save_filename_timeformat.format(prefix=quicksave_basename, ext=savegame_extension)

	savegame_screenshot_width = 290

	# metadata of a savegame with default values
	savegame_metadata = { 'timestamp' : -1,	'savecounter' : 0, 'savegamerev' : 0, 'rng_state' : "" }
	savegame_metadata_types = { 'timestamp' : float, 'savecounter' : int, 'savegamerev': int, \
	                            'rng_state' : str } # 'screenshot' : NoneType }

	campaign_status_file = os.path.join(savegame_dir, 'campaign_status.yaml')

	@classmethod
	def init(cls):
		# create savegame directory if it does not exist
		if not os.path.isdir(cls.autosave_dir):
			os.makedirs(cls.autosave_dir)
		if not os.path.isdir(cls.quicksave_dir):
			os.makedirs(cls.quicksave_dir)

	@classmethod
	def __get_displaynames(cls, files):
		"""Returns list of names files, that should be displayed to the user.
		@param files: iterable object containing strings"""
		displaynames = []
		def get_timestamp_string(savegameinfo):
			if savegameinfo['timestamp'] == -1:
				return ""
			else:
				return time.strftime('%c', time.localtime(savegameinfo['timestamp']))

		for f in files:
			if f.startswith(cls.autosave_dir):
				name = u"Autosave {date}".format(date=get_timestamp_string(cls.get_metadata(f)))
			elif f.startswith(cls.quicksave_dir):
				name = u"Quicksave {date}".format(date=get_timestamp_string(cls.get_metadata(f)))
			else:
				name = os.path.splitext(os.path.basename(f))[0]

			if not isinstance(name, unicode):
				name = unicode(name, errors='replace') # only use unicode strings, guichan needs them
			displaynames.append( name )
		return displaynames

	@classmethod
	def __get_saves_from_dirs(cls, dirs, include_displaynames, filename_extension, order_by_date):
		"""Internal function, that returns the saves of a dir"""
		if not filename_extension:
			filename_extension = cls.savegame_extension
		files = sorted((-os.path.getmtime(f) if order_by_date else 0, f) for p in dirs for f in glob.glob(p + '/*.' + filename_extension) if os.path.isfile(f))
		files = zip(*files)[1] if files else []
		if include_displaynames:
			return (files, cls.__get_displaynames(files))
		else:
			return (files,)

	@classmethod
	def create_filename(cls, savegamename):
		"""Returns the full path for a regular save of the name savegamename"""
		name = u"{directory}{sep}{name}.{ext}".format(directory=cls.savegame_dir,
		                                         sep=os.sep,
		                                         name=savegamename,
		                                         ext=cls.savegame_extension)
		cls.log.debug("Savegamemanager: creating save-filename: %s", name)
		return name

	@classmethod
	def create_autosave_filename(cls):
		"""Returns the filename for an autosave"""
		prepared_filename = time.strftime(cls.autosave_filenamepattern.format(timestamp=time.time()))
		name = u"{directory}{sep}{name}".format(directory=cls.autosave_dir, sep=os.sep, name=prepared_filename)
		cls.log.debug("Savegamemanager: creating autosave-filename: %s", name)
		return name

	@classmethod
	def create_quicksave_filename(cls):
		"""Returns the filename for a quicksave"""
		prepared_filename = time.strftime(cls.quicksave_filenamepattern.format(timestamp=time.time()))
		name = u"{directory}{sep}{name}".format(directory=cls.quicksave_dir, sep=os.sep, name=prepared_filename)
		cls.log.debug("Savegamemanager: creating quicksave-filename: %s", name)
		return name

	@classmethod
	def delete_dispensable_savegames(cls, autosaves = False, quicksaves = False):
		"""Delete savegames that are no longer needed
		@param autosaves, quicksaves: Bool, set to true if this kind of saves should be cleaned
		"""
		def tmp_del(pattern, limit): # get_uh_setting below returns floats like
			limit = int(limit)       # 4.0 and 42.0 since the slider stepping is 1.0.
			files = glob.glob(pattern)
			if len(files) > limit:
				files.sort()
				for i in xrange(0, len(files) - limit):
					os.unlink(files[i])

		if autosaves:
			tmp_del("%s/*.%s" % (cls.autosave_dir, cls.savegame_extension),
			        horizons.main.fife.get_uh_setting("AutosaveMaxCount"))
		if quicksaves:
			tmp_del("%s/*.%s" % (cls.quicksave_dir, cls.savegame_extension),
			        horizons.main.fife.get_uh_setting("QuicksaveMaxCount"))

	@classmethod
	def get_recommended_number_of_players(cls, savegamefile):
		dbdata = DbReader(savegamefile)\
		        ("SELECT `value` FROM `metadata` WHERE `name` = ?", "recommended_number_of_players")
		if dbdata:
			return dbdata[0][0]
		else:
			return "undefined"

	@classmethod
	def get_metadata(cls, savegamefile):
		"""Returns metainfo of a savegame as dict.
		"""
		db = DbReader(savegamefile)
		metadata = cls.savegame_metadata.copy()

		try:
			for key in metadata.iterkeys():
				result = db("SELECT `value` FROM `metadata` WHERE `name` = ?", key)
				if len(result) > 0:
					assert(len(result) == 1)
					metadata[key] = cls.savegame_metadata_types[key](result[0][0])
		except sqlite3.OperationalError as e:
			print 'Warning: Can\'t read savegame %s: %s' % (savegamefile, e)
			return metadata

		screenshot_data = None
		try:
			screenshot_data = db("SELECT value FROM metadata_blob where name = ?", "screen")[0][0]
		except IndexError: pass
		except sqlite3.OperationalError: pass
		metadata['screenshot'] = screenshot_data

		return metadata

	@classmethod
	def write_metadata(cls, db, savecounter, rng_state):
		"""Writes metadata to db.
		@param db: DbReader
		@param savecounter: int"""
		metadata = cls.savegame_metadata.copy()
		metadata['timestamp'] = time.time()
		metadata['savecounter'] = savecounter
		metadata['savegamerev'] = VERSION.SAVEGAMEREVISION
		metadata['rng_state'] = rng_state

		for key, value in metadata.iteritems():
			db("INSERT INTO metadata(name, value) VALUES(?, ?)", key, value)

		# special handling for screenshot (as blob)
		screenshot_fd, screenshot_filename = tempfile.mkstemp()

		width = horizons.main.fife.engine_settings.getScreenWidth()
		height = horizons.main.fife.engine_settings.getScreenHeight()


		# hide whatever dialog we have
		dialog_hidden = False
		if horizons.main._modules.gui.is_visible():
			dialog_hidden = True
			horizons.main._modules.gui.hide()
			horizons.main.fife.engine.pump()

		# scale to the correct with and adapt height with same factor
		factor = float( cls.savegame_screenshot_width ) / width
		horizons.main.fife.engine.getRenderBackend().captureScreen(screenshot_filename,
		                                                           int(float(width) * factor),
		                                                           int(float(height) * factor))

		if dialog_hidden:
			horizons.main._modules.gui.show()
			horizons.main.fife.engine.pump()

		screenshot_data = os.fdopen(screenshot_fd, "r").read()
		db("INSERT INTO metadata_blob values(?, ?)", "screen", sqlite3.Binary(screenshot_data))
		os.unlink(screenshot_filename)

	@classmethod
	def get_regular_saves(cls, include_displaynames = True):
		"""Returns all savegames, that were saved via the ingame save dialog"""
		cls.log.debug("Savegamemanager: regular saves from: %s", cls.savegame_dir)
		return cls.__get_saves_from_dirs([cls.savegame_dir], include_displaynames, None, True)

	@classmethod
	def get_maps(cls, include_displaynames = True):
		cls.log.debug("Savegamemanager: get maps from %s", cls.maps_dir)
		return cls.__get_saves_from_dirs([cls.maps_dir], include_displaynames, None, False)

	@classmethod
	def get_saves(cls, include_displaynames = True):
		"""Returns all savegames"""
		cls.log.debug("Savegamemanager: get saves from %s, %s, %s", cls.savegame_dir,
		              cls.autosave_dir, cls.quicksave_dir)
		return cls.__get_saves_from_dirs([cls.savegame_dir, cls.autosave_dir, cls.quicksave_dir], include_displaynames, None, True)

	@classmethod
	def get_quicksaves(cls, include_displaynames = True):
		"""Returns all savegames, that were saved via quicksave"""
		cls.log.debug("Savegamemanager: quicksaves from: %s", cls.quicksave_dir)
		return cls.__get_saves_from_dirs([cls.quicksave_dir], include_displaynames, None, True)

	@classmethod
	def get_scenarios(cls, include_displaynames = True):
		"""Returns all scenarios"""
		cls.log.debug("Savegamemanager: scenarios from: %s", cls.scenarios_dir)
		return cls.__get_saves_from_dirs([cls.scenarios_dir], include_displaynames, cls.scenario_extension, False)

	@classmethod
	def get_available_scenarios(cls, include_displaynames = True, locales = None):
		"""Returns available scenarios (depending on the campaign(s) status)"""
		afiles = []
		anames = []
		sfiles, snames = cls.get_scenarios(include_displaynames = True)
		for i, sname in enumerate(snames):
			if cls.check_scenario_availability(sname):
				if locales is None or cls.get_scenario_info(name = sname).get('locale', 'en') in locales:
					anames.append(sname)
					afiles.append(sfiles[i])
		if not include_displaynames:
			return (afiles,)
		return (afiles, anames)

	@classmethod
	def check_scenario_availability(cls, scenario_name):
		"""Read the campaign(s) status and check if this scenario is available for play
		@param scenario_name: codename of the scenario to check
		@return: boolean (is the scenario available or not)
		"""
		# get campaign data
		cfiles, cnames, cscenarios, cdata = cls.get_campaigns(include_scenario_list=True, campaign_data=True)
		# get campaign status
		campaign_status = cls.get_campaign_status()
		seen_in_campaigns = False
		# check every campaign
		for i, scenario_list in enumerate(cscenarios):
			if not scenario_name in scenario_list:
				continue
			seen_in_campaigns = True
			# The first scenario of every campaign is always available
			if scenario_list[0] == scenario_name:
				return True
			# The scenario is in the campaign. Check goals
			# TODO : the [0] have to be removed if we think a scenario can appear multiple times in a campaign
			conditions = [data.get('conditions') for data in cdata[i]['scenarios'] if data.get('level') == scenario_name][0]
			for condition in conditions:
				# all conditions have to be reached
				if condition['type'] != 'goal_reached':
					#xgettext:python-format
					print _("Error: don't know how to handle condition type {condition}").format(condition=condition)
				if not condition['goal'] in campaign_status.get(condition['scenario'], []):
					break
			else:
				# All conditions are met
				return True
		if not seen_in_campaigns:
			# This scenario is not in any campaign, it is available for free play
			return True

	@classmethod
	def get_campaign_status(cls):
		"""Read the campaign status from the saved YAML file"""
		if os.path.exists(cls.campaign_status_file):
			return YamlCache.get_yaml_file(cls.campaign_status_file)
		return {}

	@classmethod
	def get_campaigns(cls, include_displaynames = True, include_scenario_list = False, campaign_data = False):
		"""Returns all campaigns
		@param include_displaynames: should we return the name of the campaign
		@param include_scenario_list: should we return the list of scenarios in the campaign
		@param campaign_data: should we return the full campaign data
		@return: (campaign_files, campaign_names, campaign_scenarios, campaign_data) (depending of the parameters)
		"""
		cls.log.debug("Savegamemanager: campaigns from: %s", cls.campaigns_dir)
		files, names = cls.__get_saves_from_dirs([cls.campaigns_dir], include_displaynames, cls.campaign_extension, False)
		if not include_displaynames:
			return (files,)
		if not include_scenario_list:
			return (files, names)
		scenarios_lists = []
		campaign_datas = []
		for i, f in enumerate(files):
			campaign = YamlCache.get_file(f)
			campaign_datas.append(campaign)
			scenarios_lists.append([sc.get('level') for sc in campaign.get('scenarios',[])])
		if not campaign_data:
			return (files, names, scenarios_lists)
		return (files, names, scenarios_lists, campaign_datas)

	@classmethod
	def get_campaign_info(cls, name = "", filename = ""):
		"""Return this campaign's data"""
		assert (name or filename)
		cfiles, cnames, cscenarios, cdatas = cls.get_campaigns(include_displaynames = True, include_scenario_list = True, campaign_data = True)
		sfiles, snames = cls.get_scenarios(include_displaynames = True)
		if name:
			if not name in cnames:
				#xgettext:python-format
				print _("Error: Cannot find campaign '{name}'.").format(name=name)
				return None
			index = cnames.index(name)
		elif filename:
			if not filename in cfiles:
				#xgettext:python-format
				print _("Error: Cannot find campaign '{name}'.").format(name=filename)
				return None
			index = cfiles.index(filename)
		infos = cdatas[index]
		infos.update({'codename': cnames[index], 'filename': cfiles[index], 'scenario_names' : cscenarios[index]})
		for scenario in cscenarios[index]:
			# find the scenario file
			if not scenario in snames:
				continue
			infos.setdefault('scenario_files', {}).update({scenario: sfiles[snames.index(scenario)]})
		return infos

	@classmethod
	def get_scenario_info(cls, name = "", filename = ""):
		"""Return this scenario data"""
		sfiles, snames = cls.get_scenarios(include_displaynames = True)
		if name:
			if not name in snames:
				#xgettext:python-format
				print _("Error: Cannot find scenario '{name}'.").format(name=name)
				return {}
			index = snames.index(name)
		elif filename:
			if not filename in sfiles:
				#xgettext:python-format
				print _("Error: Cannot find scenario '{name}'.").format(name=filename)
				return {}
			index = sfiles.index(filename)
		data = YamlCache.get_file(sfiles[index])
		return data

	@classmethod
	def mark_scenario_as_won(cls, campaign_data):
		"""Remember that the scenario was won"""
		# Winning a scenario is like winning the "special" goal 'victory'
		return cls.mark_goal_reached(campaign_data, 'victory')

	@classmethod
	def mark_goal_reached(cls, campaign_data, goal_codename):
		"""Remember that this specific goal in the scenario was won"""
		# grab the campaign status
		campaign_status = cls.get_campaign_status()
		# append the goal's codename to the list of reached goal for this scenario
		campaign_status.setdefault(campaign_data['scenario_name'], []).append(goal_codename)
		# save the data back to the file
		yaml.dump(campaign_status, open(cls.campaign_status_file, "w"))
		return campaign_status

	@classmethod
	def load_scenario(cls, campaign_data, scenario_name):
		"""This loads the next scenario by starting a new game"""
		campaign = cls.get_campaign_info(campaign_data['campaign_name'])
		scenarios = [sc.get('level') for sc in campaign.get('scenarios',[])]
		if not scenario_name in scenarios:
			return False
		next_index = scenarios.index(scenario_name)
		campaign_data['scenario_index'] = next_index
		campaign_data['scenario_name'] = scenarios[next_index]
		horizons.main._start_map(scenarios[next_index], is_scenario = True, campaign = campaign_data)

	@classmethod
	def load_next_scenario(cls, campaign_data):
		"""This loads the next scenario by starting a new game"""
		campaign = cls.get_campaign_info(campaign_data['campaign_name'])
		scenarios = [sc.get('level') for sc in campaign.get('scenarios',[])]
		next_index = campaign_data['scenario_index'] + 1
		if next_index == len(scenarios):
			# If no more scenario, do the same thing as in the "old" do_win action
			horizons.main._modules.session.gui.quit_session(force = True)
			return False
		campaign_data['scenario_index'] = next_index
		campaign_data['scenario_name'] = scenarios[next_index]
		horizons.main._start_map(scenarios[next_index], is_scenario = True, campaign = campaign_data)

	@classmethod
	def get_savegamename_from_filename(cls, savegamefile):
		"""Returns a displayable name, extracted from a filename"""
		name = os.path.basename(savegamefile)
		name = name.rsplit(".%s"%cls.savegame_extension, 1)[0]
		cls.log.debug("Savegamemanager: savegamename: %s", name)
		return name
