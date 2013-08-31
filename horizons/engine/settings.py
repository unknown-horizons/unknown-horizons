# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

from fife.extensions.serializers.simplexml import SimpleXMLSerializer

from horizons.constants import LANGUAGENAMES
from horizons.engine import UH_MODULE
from horizons.i18n import change_language

class Settings(object):

	def __init__(self, settings_file, settings_template_file):
		self._module_settings = {}
		self._module_settings_template = {}
		self._settings_file = settings_file
		self._settings_template_file = settings_template_file
		self._settings_serializer = SimpleXMLSerializer()
		self._settings_serializer.load(settings_file)
		self._settings_template_serializer = SimpleXMLSerializer()
		self._settings_template_serializer.load(settings_template_file)

	def get(self, module, name, default=None):
		if default is None:
			default = self._settings_template_serializer.get(module, name)

		v = self._settings_serializer.get(module, name, default)
		getter = getattr(self, 'get_' + module + '_' + name, None)
		if getter:
			return getter(v)
		else:
			return v

	def set(self, module, name, value):
		setter = getattr(self, 'set_' + module + '_' + name, None)
		if setter:
			value = setter(value)

		if module in self._module_settings:
			self._module_settings[module][name] = value

		self._settings_serializer.set(module, name, value, {})

	def get_module_settings(self, module):
		self._module_settings[module] = self._settings_serializer.getAllSettings(module)
		self._module_settings_template[module] = self._settings_template_serializer.getAllSettings(module)
		for name, value in self._module_settings_template[module].iteritems():
			if name not in self._module_settings[module]:
				self._module_settings[module][name] = value
		return self._module_settings[module]

	def get_module_template_settings(self, module):
		return self._settings_template_serializer.getAllSettings(module)

	def save(self):

		self._settings_serializer.save(self._settings_file)

	def apply(self):
		data = self.get(UH_MODULE, "Language")
		language = LANGUAGENAMES.get_by_value(data)
		change_language(language)

	def set_defaults(self):
		for module in self._settings_template_serializer.getModuleName():
			for setting_name in self._settings_template_serializer.getAllSettings(module):
				value = self._settings_template_serializer.get(module, setting_name)
				self.set(module, setting_name, value)
		self.save()

	# settings

	def get_unknownhorizons_Language(self, value):
		if value is None: # the entry is None for empty strings
			value = ""
		return LANGUAGENAMES[value]

	def set_unknownhorizons_Language(self, value):
		return LANGUAGENAMES.get_by_value(value)
