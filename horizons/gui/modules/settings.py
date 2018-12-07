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

import os
import sys

from fife import fife

import horizons.globals
from horizons.constants import LANGUAGENAMES, SETTINGS
from horizons.gui.modules.hotkeys_settings import HotkeyConfiguration
from horizons.gui.modules.loadingscreen import QUOTES_SETTINGS
from horizons.gui.widgets.pickbeltwidget import PickBeltWidget
from horizons.gui.windows import Window
from horizons.i18n import (
	change_language, find_available_languages, get_language_translation_stats, gettext as T,
	gettext_lazy as LazyT)
from horizons.network.networkinterface import NetworkInterface
from horizons.util.python import parse_port
from horizons.util.python.callback import Callback


class Setting:
	def __init__(self, module, name, widget_name, initial_data=None, restart=False,
			callback=None, on_change=None):
		self.module = module
		self.name = name
		self.widget_name = widget_name
		self.initial_data = initial_data
		self.restart = restart
		self.callback = callback
		self.on_change = on_change


class SettingsDialog(PickBeltWidget, Window):
	"""Widget for Options dialog with pickbelt style pages"""

	widget_xml = 'settings.xml'
	sections = (
		('graphics_settings', LazyT('Graphics')),
		('hotkeys_settings', LazyT('Hotkeys')),
		('game_settings', LazyT('Game')),
	)

	def __init__(self, windows):
		Window.__init__(self, windows)
		PickBeltWidget.__init__(self)

		self._settings = horizons.globals.fife._setting

		self.widget.mapEvents({
			'okButton': self.apply_settings,
			'defaultButton': self.set_defaults,
			'cancelButton': self._windows.close,
		})

	def _init_settings(self):
		"""Init the settings with the stored values."""
		languages = list(find_available_languages().keys())
		language_names = [LANGUAGENAMES[x] for x in sorted(languages)]

		fps = {0: LazyT("Disabled"), 30: 30, 45: 45, 60: 60, 90: 90, 120: 120}

		FIFE = SETTINGS.FIFE_MODULE
		UH = SETTINGS.UH_MODULE

		def get_resolutions():
			return get_screen_resolutions(self._settings.get(FIFE, 'ScreenResolution'))

		self._options = [
			# Graphics/Sound/Input
			Setting(FIFE, 'ScreenResolution', 'screen_resolution', get_resolutions, restart=True),
			Setting(FIFE, 'FullScreen', 'enable_fullscreen', restart=True),
			Setting(FIFE, 'FrameLimit', 'fps_rate', fps, restart=True, callback=self._apply_FrameLimit),

			Setting(UH, 'VolumeMusic', 'volume_music', callback=self._apply_VolumeMusic,
				on_change=self._on_slider_changed),
			Setting(UH, 'VolumeEffects', 'volume_effects', callback=self._apply_VolumeEffects,
				on_change=self._on_slider_changed),
			Setting(FIFE, 'PlaySounds', 'enable_sound', callback=self._apply_PlaySounds),
			Setting(UH, 'EdgeScrolling', 'edgescrolling'),
			Setting(UH, 'CursorCenteredZoom', 'cursor_centered_zoom'),
			Setting(UH, 'MiddleMousePan', 'middle_mouse_pan'),
			Setting(FIFE, 'MouseSensitivity', 'mousesensitivity', restart=True,
				on_change=self._on_slider_changed),

			# Game
			Setting(UH, 'AutosaveInterval', 'autosaveinterval', on_change=self._on_slider_changed),
			Setting(UH, 'AutosaveMaxCount', 'autosavemaxcount', on_change=self._on_slider_changed),
			Setting(UH, 'QuicksaveMaxCount', 'quicksavemaxcount', on_change=self._on_slider_changed),
			Setting(UH, 'Language', 'uni_language', language_names,
				callback=self._apply_Language, on_change=self._on_Language_changed),

			Setting(UH, 'UninterruptedBuilding', 'uninterrupted_building'),
			Setting(UH, 'AutoUnload', 'auto_unload'),
			Setting(UH, 'DebugLog', 'debug_log', callback=self._apply_DebugLog),
			Setting(UH, 'ShowResourceIcons', 'show_resource_icons'),
			Setting(UH, 'ScrollSpeed', 'scrollspeed', on_change=self._on_slider_changed),
			Setting(UH, 'QuotesType', 'quotestype', QUOTES_SETTINGS),
			Setting(UH, 'NetworkPort', 'network_port', callback=self._apply_NetworkPort),
		]

		self._fill_widgets()

		# key configuration
		self.hotkey_interface = HotkeyConfiguration()
		number = self.sections.index(('hotkeys_settings', T('Hotkeys')))
		self.page_widgets[number].removeAllChildren()
		self.page_widgets[number].addChild(self.hotkey_interface.widget)

	def show(self):
		self._init_settings()
		self.widget.show()

	def hide(self):
		self.widget.hide()

	def restart_promt(self):
		headline = T("Restart required")
		message = T("Some of your changes require a restart of Unknown Horizons. Do you want to restart Unknown Horizons now?")
		if self._windows.open_popup(headline, message, show_cancel_button=True):
			return True

	def set_defaults(self):
		title = T("Restore default settings")
		msg = T("Restoring the default settings will delete all changes to the settings you made so far.") + \
				" " + T("Do you want to continue?")

		if self._windows.open_popup(title, msg, show_cancel_button=True):
			self.hotkey_interface.reset_to_default()
			self._settings.set_defaults()
			self.restart_prompt()
			self._windows.close()

	def apply_settings(self):
		restart_required = False

		for entry in self._options:
			widget = self.widget.findChild(name=entry.widget_name)
			new_value = widget.getData()

			if callable(entry.initial_data):
				initial_data = entry.initial_data()
			else:
				initial_data = entry.initial_data

			if isinstance(initial_data, list):
				new_value = initial_data[new_value]
			elif isinstance(initial_data, dict):
				new_value = list(initial_data.keys())[new_value]

			old_value = self._settings.get(entry.module, entry.name)

			# Store new setting
			self._settings.set(entry.module, entry.name, new_value)

			# If setting changed, allow applying of new value and sanity checks
			if new_value != old_value:
				if entry.restart:
					restart_required = True

				if entry.callback:
					entry.callback(old_value, new_value)

		self.hotkey_interface.save_settings()
		self._settings.apply()
		self._settings.save()

		if restart_required:
			if self.restart_promt():
				horizons.globals.fife.engine.destroy()
				os.execv(sys.executable, [sys.executable] + sys.argv)

		self._windows.close()

	def _fill_widgets(self):
		for entry in self._options:
			value = self._settings.get(entry.module, entry.name)
			widget = self.widget.findChild(name=entry.widget_name)

			if entry.initial_data:
				if callable(entry.initial_data):
					initial_data = entry.initial_data()
				else:
					initial_data = entry.initial_data

				if isinstance(initial_data, dict):
					widget.setInitialData(list(initial_data.values()))
					value = list(initial_data.keys()).index(value)
				elif isinstance(initial_data, list):
					widget.setInitialData(initial_data)
					value = initial_data.index(value)
				else:
					widget.setInitialData(initial_data)

			widget.setData(value)

			if entry.on_change:
				cb = Callback(entry.on_change, widget)
				cb()
				widget.capture(cb)

	def _on_slider_changed(self, widget):
		"""Callback for updating value label of a slider after dragging it.

		As the numeric values under the hood often do not represent mental
		models of what the setting achieves very well, depending on the
		setting in question we display a modified value, sometimes with
		a '%' suffix."""
		value_label = self.widget.findChild(name=widget.name + '_value')
		value = {
			'volume_music': lambda x: '{:d}%'.format(int(500 * x)),
			'volume_effects': lambda x: '{:d}%'.format(int(200 * x)),
			'mousesensitivity': lambda x: '{:.1f}x'.format(10 * x),
			'autosaveinterval': lambda x: '{:.1f}'.format(x),
			'autosavemaxcount': lambda x: '{:d}'.format(int(x)),
			'quicksavemaxcount': lambda x: '{:d}'.format(int(x)),
			'scrollspeed': lambda x: '{:.1f}'.format(x),
		}[widget.name](widget.value)
		value_label.text = value

	# callbacks for changes of settings

	def _apply_PlaySounds(self, old, new):
		horizons.globals.fife.sound.setup_sound()

	def _apply_VolumeMusic(self, old, new):
		horizons.globals.fife.sound.set_volume_bgmusic(new)

	def _apply_VolumeEffects(self, old, new):
		horizons.globals.fife.sound.set_volume_effects(new)

	def _apply_FrameLimit(self, old, new):
		# handling value 0 for framelimit to disable limiter
		if new == 0:
			self._settings.set(SETTINGS.FIFE_MODULE, 'FrameLimitEnabled', False)
		else:
			self._settings.set(SETTINGS.FIFE_MODULE, 'FrameLimitEnabled', True)

	def _apply_NetworkPort(self, old, new):
		"""Sets a new value for client network port"""
		# port is saved as string due to pychan limitations
		try:
			# 0 is not a valid port, but a valid value here (used for default)
			parse_port(new)
		except ValueError:
			headline = T("Invalid network port")
			descr = T("The port you specified is not valid. It must be a number between 1 and 65535.")
			advice = T("Please check the port you entered and make sure it is in the specified range.")
			self._windows.open_error_popup(headline, descr, advice)
			# reset value and reshow settings dlg
			self._settings.set(SETTINGS.UH_MODULE, 'NetworkPort', "0")
		else:
			# port is valid
			try:
				if NetworkInterface() is None:
					NetworkInterface.create_instance()
				NetworkInterface().network_data_changed()
			except Exception as e:
				headline = T("Failed to apply new network settings.")
				descr = T("Network features could not be initialized with the current configuration.")
				advice = T("Check the settings you specified in the network section.")
				if 0 < parse_port(new) < 1024:
					#i18n This is advice for players seeing a network error with the current config
					advice += " " + \
						T("Low port numbers sometimes require special access privileges, try 0 or a number greater than 1024.")
				details = str(e)
				self._windows.open_error_popup(headline, descr, advice, details)

	def _apply_Language(self, old, new):
		language = LANGUAGENAMES.get_by_value(new)
		change_language(language)

	def _on_Language_changed(self, widget):
		value = widget.items[widget.getData()]
		language_code = LANGUAGENAMES.get_by_value(value)

		status_label = self.widget.findChild(name='language_translation_status')
		if not language_code or language_code == 'en':
			status_label.text = ''
		else:
			value = get_language_translation_stats(language_code)
			if value:
				status_label.text = T('Translation {percentage}% completed').format(percentage=value)
			else:
				status_label.text = ''

	def _apply_DebugLog(self, old, new):
		horizons.main.set_debug_log(new)


def get_screen_resolutions(selected_default):
	"""Create an instance of fife.DeviceCaps and compile a list of possible resolutions.

	NOTE: This call only works if the engine is inited.
	"""
	possible_resolutions = {selected_default}

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
