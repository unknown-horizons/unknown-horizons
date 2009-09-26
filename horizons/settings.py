# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import shutil
import os.path
import ext.simplejson as simplejson

from horizons.constants import PATHS
from horizons.util import ManualConstructionSingleton

class _Setting(object):
	""" Class to store settings
	@param name:
	"""
	def __init__(self, db, name = ''):
		self.__dict__['db'] = db
		self._name = name
		self._categories = []
		self._listener = []
		try:
			import config
			for option in config.__dict__:
				if option.startswith(name) and '.' not in option[len(name):]:
					self.__dict__[option[len(name):]] = getattr(config, option)
		except ImportError:
			pass
		for (option, value) in \
		    self.db("select substr(name, ?, length(name)), value from config.config \
		    where substr(name, 1, ?) = ? and substr(name, ?, length(name)) NOT LIKE '%.%'", \
		                             len(name) + 1, len(name), name, len(name) + 1):
			if not option in self.__dict__:
				self.__dict__[option] = simplejson.loads(value)
				if isinstance(self.__dict__[option], unicode):
					self.__dict__[option] = str(self.__dict__[option])

	def __getattr__(self, name):
		"""
		@param name:
		"""
		assert(not name.startswith('_'))
		return None

	def __setattr__(self, name, value):
		"""
		@param name:
		@param value:
		"""
		self.__dict__[name] = value
		if not name.startswith('_'):
			assert(name not in self._categories)
			self.db("replace into config.config (name, value) values (?, ?)", self._name + name, simplejson.dumps(value))
			for listener in self._listener:
				listener(self, name, value)

	def add_change_listener(self, listener):
		"""
		@param listener:
		"""
		for name in self._categories:
			self.__dict__[name].add_change_listener(listener)
		self._listener.append(listener)
		for name in self.__dict__:
			if not name.startswith('_'):
				listener(self, name, getattr(self, name))

	def delChangeListener(self, listener):
		"""
		@param listener:
		"""
		for name in self._categories:
			self.__dict__[name].delChangeListener(listener)
		self._listener.remove(listener)

	def setDefaults(self, **defaults):
		"""
		@param **defaults:
		"""
		for name in defaults:
			assert(not name.startswith('_'))
			assert(name not in self._categories)
			if not name in self.__dict__:
				self.__dict__[name] = defaults[name]
				for listener in self._listener:
					listener(self, name, defaults[name])

	def addCategories(self, *categories):
		"""Adds one or more setting categories

		The new categories can be accessed via
		settingsObj.NEWCATEGORY
		@param *categories:
		"""
		for category in categories:
			self._categories.append(category)
			inst = _Setting(self.db, self._name + category + '.')
			self.__dict__[category] = inst
			for listener in self._listener:
				inst.add_change_listener(listener)

class Settings(_Setting):
	"""Class that enables access to dynamically created members via dot notation.
	This means, that you can access an added category or value via settings_inst.cat.setting_name
	"""
	__metaclass__ = ManualConstructionSingleton
	VERSION = 2
	"""
	@param config:
	"""
	def __init__(self, db, config = PATHS.USER_CONFIG_FILE):
		self.__dict__['db'] = db # workaround for overloaded __setattr__
		if not os.path.exists(config):
			shutil.copyfile('content/config.sqlite', config)
		self.db("ATTACH ? AS config", config)
		version = self.db("PRAGMA config.user_version")[0][0]
		if version > self.VERSION:
			print _("Error: Config version not supported, creating empty config which wont be saved.")
			self.db("DETACH config")
			self.db("ATTACH ':memory:' AS config")
			self.db("CREATE TABLE config.config (name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")
		elif version < self.VERSION:
			print _("Upgrading Config from Version %d to Version %d ...") % (version, self.VERSION)
			if version == 1:
				self.db("UPDATE config.config SET name = REPLACE(name, '_', '.') WHERE name != 'client_id'")
				version = 2
			self.db("PRAGMA config.user_version = " + str(self.VERSION))
		super(Settings, self).__init__(db)

	def set_defaults(self):
		self.addCategories('sound')
		self.sound.setDefaults(enabled = True)
		self.sound.setDefaults(volume_music = 0.2)
		self.sound.setDefaults(volume_effects = 0.5)
		self.addCategories('network')
		self.network.setDefaults(port = 62666, \
		                         url_servers = 'http://master.unknown-horizons.org/servers', \
		                         url_master = 'master.unknown-horizons.org', \
		                         favorites = [])
		self.addCategories('language')
		self.language.setDefaults(position='po', name='')
		self.addCategories('savegame')
		self.savegame.setDefaults(savedquicksaves = 10, autosaveinterval = 10, savedautosaves = 10)
