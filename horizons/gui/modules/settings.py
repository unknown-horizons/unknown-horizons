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

import collections

from fife import fife

import horizons.globals

from horizons.constants import LANGUAGENAMES
from horizons.engine import UH_MODULE, FIFE_MODULE
from horizons.i18n import _lazy, find_available_languages
from horizons.gui.modules.loadingscreen import QUOTES_SETTINGS
from horizons.gui.widgets.pickbeltwidget import PickBeltWidget
from horizons.gui.windows import Window


class Setting(object):
	def __init__(self, module, name, widget_name, initial_data=None):
		self.module = module
		self.name = name
		self.widget_name = widget_name
		self.initial_data = initial_data


class SettingsDialog(PickBeltWidget, Window):
	"""Widget for Options dialog with pickbelt style pages"""

	widget_xml = 'settings.xml'
	sections = (('graphics_settings', _lazy('Graphics')),
			    ('game_settings', _lazy('Game')))

	def __init__(self, windows):
		Window.__init__(self, windows)
		PickBeltWidget.__init__(self)

		self._settings = horizons.globals.fife._setting

		self.widget.mapEvents({
			'okButton': self.apply_settings,
			'defaultButton': self.set_defaults,
			'cancelButton': self._windows.close,
		})

		languages = find_available_languages().keys()
		language_names = [LANGUAGENAMES[x] for x in sorted(languages)]

		bpp = {0: _lazy("Default"), 16: _lazy("16 bit"), 32: _lazy("32 bit")}

		def get_resolutions():
			return get_screen_resolutions(self._settings.get(FIFE_MODULE, 'ScreenResolution'))

		self._options = [
			# Graphics/Sound/Input
			Setting(FIFE_MODULE, 'ScreenResolution', 'screen_resolution', get_resolutions),
			Setting(FIFE_MODULE, 'BitsPerPixel', 'screen_bpp', bpp),
			Setting(FIFE_MODULE, 'FullScreen', 'enable_fullscreen'),
			Setting(FIFE_MODULE, 'RenderBackend', 'render_backend', ['OpenGL', 'SDL', 'OpenGLe']),
			Setting(FIFE_MODULE, 'FrameLimit', 'fps_rate', [30, 45, 60, 90, 120]),

			Setting(UH_MODULE, 'VolumeMusic', 'volume_music'),
			Setting(UH_MODULE, 'VolumeEffects', 'volume_effects'),
			Setting(FIFE_MODULE, 'PlaySounds', 'enable_sound'),
			Setting(UH_MODULE, 'EdgeScrolling', 'edgescrolling'),
			Setting(UH_MODULE, 'CursorCenteredZoom', 'cursor_centered_zoom'),
			Setting(UH_MODULE, 'MiddleMousePan', 'middle_mouse_pan'),
			Setting(FIFE_MODULE, 'MouseSensitivity', 'mousesensitivity'),

			# Game
			Setting(UH_MODULE, 'AutosaveInterval', 'autosaveinterval'),
			Setting(UH_MODULE, 'AutosaveMaxCount', 'autosavemaxcount'),
			Setting(UH_MODULE, 'QuicksaveMaxCount', 'quicksavemaxcount'),
			Setting(UH_MODULE, 'Language', 'uni_language', language_names),

			Setting(UH_MODULE, 'MinimapRotation', 'minimaprotation'),
			Setting(UH_MODULE, 'UninterruptedBuilding', 'uninterrupted_building'),
			Setting(UH_MODULE, 'AutoUnload', 'auto_unload'),
			Setting(UH_MODULE, 'DebugLog', 'debug_log'),
			Setting(UH_MODULE, 'ShowResourceIcons', 'show_resource_icons'),
			Setting(UH_MODULE, 'ScrollSpeed', 'scrollspeed'),
			Setting(UH_MODULE, 'QuotesType', 'quotestype', QUOTES_SETTINGS),
			Setting(UH_MODULE, 'NetworkPort', 'network_port'),
		]

		self._fill_widgets()

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()

	def set_defaults(self):
		title = _("Restore default settings")
		msg = _("Restoring the default settings will delete all changes to the settings you made so far.") + \
				u" " + _("Do you want to continue?")

		if self._windows.show_popup(title, msg, show_cancel_button=True):
			self._settings.set_defaults()

	def apply_settings(self):
		for entry in self._options:
			widget = self.widget.findChild(name=entry.widget_name)
			data = widget.getData()

			if isinstance(entry.initial_data, list):
				data = entry.initial_data[data]
			elif isinstance(entry.initial_data, dict):
				data = entry.initial_data.keys()[data]

			self._settings.set(entry.module, entry.name, data)

		self._settings.apply()
		self._settings.save()
		self._windows.close()

	def _fill_widgets(self):
		for entry in self._options:
			value = self._settings.get(entry.module, entry.name)
			widget = self.widget.findChild(name=entry.widget_name)

			if entry.initial_data:
				if isinstance(entry.initial_data, collections.Callable):
					initial_data = entry.initial_data()
				else:
					initial_data = entry.initial_data

				if isinstance(initial_data, dict):
					widget.setInitialData(initial_data.values())
					value = initial_data.keys().index(value)
				elif isinstance(initial_data, list):
					widget.setInitialData(initial_data)
					value = initial_data.index(value)
				else:
					widget.setInitialData(initial_data)

			widget.setData(value)


def get_screen_resolutions(selected_default):
	"""Create an instance of fife.DeviceCaps and compile a list of possible resolutions.

	NOTE: This call only works if the engine is inited.
	"""
	possible_resolutions = set([selected_default])

	MIN_X = 800
	MIN_Y = 600

	devicecaps = fife.DeviceCaps()
	devicecaps.fillDeviceCaps()

	for screenmode in devicecaps.getSupportedScreenModes():
		x = screenmode.getWidth()
		y = screenmode.getHeight()
		if x < MIN_X or y < MIN_Y:
			continue
		res = str(x) + 'x' + str(y)
		possible_resolutions.add(res)

	by_width = lambda res: int(res.split('x')[0])
	return sorted(possible_resolutions, key=by_width)
