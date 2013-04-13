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


DEFAULT_SETTINGS = {
	'FIFE': {
		'VideoDriver': '',
	}
}


class Settings(object):

	def __init__(self, settings_file):
		self._module_settings = {}
		self._serializer = SimpleXMLSerializer()
		self._serializer.load(settings_file)

	def get(self, module, name, default=None):
		return self._serializer.get(module, name, default)

	def set(self, module, name, value):
		pass

	def get_module_settings(self, module):
		self._module_settings[module] = self._serializer.getAllSettings(module)

		for name, value in DEFAULT_SETTINGS.get(module, {}).iteritems():
			if name not in self._module_settings[module]:
				self._module_settings[module][name] = value

		return self._module_settings[module]

	def save(self):
		pass

	def apply(self):
		data = self.get(UH_MODULE, "Language")
		language = LANGUAGENAMES.get_by_value(data)
		change_language(language)

	def set_defaults(self):
		pass
