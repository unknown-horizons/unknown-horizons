# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main
import shutil
import os.path
import simplejson

class Setting(object):
	""" Class to store settings
	@param name:
	"""
	def __init__(self, name = ''):
		self._name = name
		self._categorys = []
		self._listener = []
		try:
			import config
			for option in config.__dict__:
				if option.startswith(name) and '_' not in option[len(name):]:
					self.__dict__[option[len(name):]] = getattr(config, option)
		except ImportError:
			pass
		for (option, value) in game.main.db("select substr(name, ?, length(name)), value from config.config where substr(name, 1, ?) = ? and substr(name, ?, length(name)) NOT LIKE '%#_%' ESCAPE '#'", len(name) + 1, len(name), name, len(name) + 1):
			if not self.__dict__.has_key(option):
				self.__dict__[option] = simplejson.loads(value)

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
			assert(name not in self._categorys)
			game.main.db("replace into config.config (name, value) values (?, ?)", self._name + name, simplejson.dumps(value))
			for listener in self._listener:
				listener(self, name, value)

	def addChangeListener(self, listener):
		"""
		@param listener:
		"""
		for name in self._categorys:
			self.__dict__[name].addChangeListener(listener)
		self._listener.append(listener)
		for name in self.__dict__:
			if not name.startswith('_'):
				listener(self, name, getattr(self, name))

	def delChangeListener(self, listener):
		"""
		@param listener:
		"""
		for name in self._categorys:
			self.__dict__[name].delChangeListener(listener)
		self._listener.remove(listener)

	def setDefaults(self, **defaults):
		"""
		@param **defaults:
		"""
		for name in defaults:
			assert(not name.startswith('_'))
			assert(name not in self._categorys)
			if not self.__dict__.has_key(name):
				self.__dict__[name] = defaults[name]
				for listener in self._listener:
					listener(self, name, defaults[name])

	def addCategorys(self, *categorys):
		"""Adds one or more setting categories

		The new categories can be accessed via 
		settingsObj.NEWCATEGORY
		@param *categorys:
		"""
		for category in categorys:
			self._categorys.append(category)
			inst = Setting(self._name + category + '_')
			self.__dict__[category] = inst
			for listener in self._listener:
				inst.addChangeListener(listener)

class Settings(Setting):
	VERSION = 1
	"""
	@param config:
	"""
	def __init__(self, config = 'config.sqlite'):
		if not os.path.exists(config):
			shutil.copyfile('content/config.sqlite', config)
		game.main.db("attach ? AS config", config)
		version = game.main.db("PRAGMA config.user_version")[0][0]
		if version > Settings.VERSION:
			print "Error: Config version not supported, creating empty config which wont be saved."
			game.main.db("detach config")
			game.main.db("attach ':memory:' AS config")
			game.main.db("CREATE TABLE config.config (name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")
		elif version < Settings.VERSION:
			print "Upgrading Config from Version " + str(version) + " to Version " + str(Settings.VERSION) + "..."
			game.main.db("PRAGMA config.user_version = " + str(Settings.VERSION))
		super(Settings, self).__init__()
