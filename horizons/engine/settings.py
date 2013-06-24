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
		'FullScreen': False,
		'PychanDebug': False,
		'ProfilingOn': False,
		'SDLRemoveFakeAlpha': False,
		'ScreenResolution': '1024x768',
		'BitsPerPixel': 0,
		'FrameLimitEnabled': False,
		'FrameLimit': 60,

		'RenderBackend': 'OpenGL',
		'GLCompressImages': False,
		'GLUseFramebuffer': True,
		'GLUseNPOT': True,

		'InitialVolume': 5.0,
		'PlaySounds': True,

		'WindowTitle': '',
		'WindowIcon': '',

		'Font': '',

		'Lighting': 0,
		'ColorKeyEnabled': False,
		'ColorKey': [255, 0, 255],

		'LogToFile': False,
		'LogToPrompt': False,
		'LogLevelFilter': [0],
		'LogModules': ['controller','script'],

		'MouseSensitivity': 0.0,
		'MouseAcceleration': False,

		'UsePsyco': False,
	}
}


class Settings(object):

	def __init__(self, settings_file):
		self._module_settings = {}
		self._settings_file = settings_file
		self._serializer = SimpleXMLSerializer()
		self._serializer.load(settings_file)

	def get(self, module, name, default=None):
		if default is None:
			default = DEFAULT_SETTINGS.get(module, {}).get(name)

		v = self._serializer.get(module, name, default)
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

		self._serializer.set(module, name, value, {})

	def get_module_settings(self, module):
		self._module_settings[module] = self._serializer.getAllSettings(module)

		for name, value in DEFAULT_SETTINGS.get(module, {}).iteritems():
			if name not in self._module_settings[module]:
				self._module_settings[module][name] = value

		return self._module_settings[module]

	def save(self):
		self._serializer.save(self._settings_file)

	def apply(self):
		data = self.get(UH_MODULE, "Language")
		language = LANGUAGENAMES.get_by_value(data)
		change_language(language)

	def set_defaults(self):
		pass

	# settings

	def get_unknownhorizons_Language(self, value):
		if value is None: # the entry is None for empty strings
			value = ""
		return LANGUAGENAMES[value]

	def set_unknownhorizons_Language(self, value):
		return LANGUAGENAMES.get_by_value(value)
