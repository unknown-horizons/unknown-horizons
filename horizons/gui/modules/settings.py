# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
	change_language, find_available_languages, gettext as _, gettext_lazy as _lazy)
from horizons.network.networkinterface import NetworkInterface
from horizons.util.python import parse_port
from horizons.util.python.callback import Callback


class Setting(object):
	def __init__(self, module, name, widget_name, initial_data=None, restart=False, callback=None):
		self.module = module
		self.name = name
		self.widget_name = widget_name
		self.initial_data = initial_data
		self.restart = restart
		self.callback = callback


class SettingsDialog(PickBeltWidget, Window):
	"""Widget for Options dialog with pickbelt style pages"""

	widget_xml = 'settings.xml'
	sections = (
		('graphics_settings', _lazy('Graphics')),
		('hotkeys_settings', _lazy('Hotkeys')),
		('game_settings', _lazy('Game')),
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
		languages = find_available_languages().keys()
		language_names = [LANGUAGENAMES[x] for x in sorted(languages)]

		fps = {0: _lazy("Disabled"), 30: 30, 45: 45, 60: 60, 90: 90, 120: 120}

		FIFE = SETTINGS.FIFE_MODULE
		UH = SETTINGS.UH_MODULE

		def get_resolutions():
			return get_screen_resolutions(self._settings.get(FIFE, 'ScreenResolution'))

		self._options = [
			# Graphics/Sound/Input
			Setting(FIFE, 'ScreenResolution', 'screen_resolution', get_resolutions, restart=True),
			Setting(FIFE, 'FullScreen', 'enable_fullscreen', restart=True),
			Setting(FIFE, 'FrameLimit', 'fps_rate', fps, restart=True, callback=self._on_FrameLimit_changed),

			Setting(UH, 'VolumeMusic', 'volume_music', callback=self._on_VolumeMusic_changed),
			Setting(UH, 'VolumeEffects', 'volume_effects', callback=self._on_VolumeEffects_changed),
			Setting(FIFE, 'PlaySounds', 'enable_sound', callback=self._on_PlaySounds_changed),
			Setting(UH, 'EdgeScrolling', 'edgescrolling'),
			Setting(UH, 'CursorCenteredZoom', 'cursor_centered_zoom'),
			Setting(UH, 'MiddleMousePan', 'middle_mouse_pan'),
			Setting(FIFE, 'MouseSensitivity', 'mousesensitivity', restart=True),

			# Game
			Setting(UH, 'AutosaveInterval', 'autosaveinterval'),
			Setting(UH, 'AutosaveMaxCount', 'autosavemaxcount'),
			Setting(UH, 'QuicksaveMaxCount', 'quicksavemaxcount'),
			Setting(UH, 'Language', 'uni_language', language_names, callback=self._on_Language_changed),

			Setting(UH, 'MinimapRotation', 'minimaprotation'),
			Setting(UH, 'UninterruptedBuilding', 'uninterrupted_building'),
			Setting(UH, 'AutoUnload', 'auto_unload'),
			Setting(UH, 'DebugLog', 'debug_log', callback=self._on_DebugLog_changed),
			Setting(UH, 'ShowResourceIcons', 'show_resource_icons'),
			Setting(UH, 'ScrollSpeed', 'scrollspeed'),
			Setting(UH, 'QuotesType', 'quotestype', QUOTES_SETTINGS),
			Setting(UH, 'NetworkPort', 'network_port', callback=self._on_NetworkPort_changed),
		]

		self._fill_widgets()

		# key configuration
		self.hotkey_interface = HotkeyConfiguration()
		number = self.sections.index(('hotkeys_settings', _('Hotkeys')))
		self.page_widgets[number].removeAllChildren()
		self.page_widgets[number].addChild(self.hotkey_interface.widget)

	def show(self):
		self._init_settings()
		self.widget.show()

	def hide(self):
		self.widget.hide()

	def restart_promt(self):
		headline = _("Restart required")
		message = _("Some of your changes require a restart of Unknown Horizons. Do you want to restart Unknown Horizons now?")
		if self._windows.open_popup(headline, message, show_cancel_button=True):
			return True

	def set_defaults(self):
		title = _("Restore default settings")
		msg = _("Restoring the default settings will delete all changes to the settings you made so far.") + \
				u" " + _("Do you want to continue?")

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

			if isinstance(entry.initial_data, collections.Callable):
				initial_data = entry.initial_data()
			else:
				initial_data = entry.initial_data

			if isinstance(initial_data, list):
				new_value = initial_data[new_value]
			elif isinstance(initial_data, dict):
				new_value = initial_data.keys()[new_value]

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

			# For sliders, there also is a label showing the current value
			if isinstance(widget, horizons.globals.fife.pychan.widgets.Slider):
				cb = Callback(self.slider_change, widget)
				cb()
				widget.capture(cb)

	def slider_change(self, widget):
		"""Callback for updating value label of a slider after dragging it.

		As the numeric values under the hood often do not represent mental
		models of what the setting achieves very well, depending on the
		setting in question we display a modified value, sometimes with
		a '%' suffix."""
		value_label = self.widget.findChild(name=widget.name + '_value')
		value = {
			'volume_music':      lambda x: u'%s%%' % int(500 * x),
			'volume_effects':    lambda x: u'%s%%' % int(200 * x),
			'mousesensitivity':  lambda x: u'%+.1f%%' % (200 * x),
			'autosaveinterval':  lambda x: u'%d' % x,
			'autosavemaxcount':  lambda x: u'%d' % x,
			'quicksavemaxcount': lambda x: u'%d' % x,
			'scrollspeed':       lambda x: u'%.1f' % x,
		}[widget.name](widget.value)
		value_label.text = value

	# callbacks for changes of settings

	def _on_PlaySounds_changed(self, old, new):
		horizons.globals.fife.sound.setup_sound()

	def _on_VolumeMusic_changed(self, old, new):
		horizons.globals.fife.sound.set_volume_bgmusic(new)

	def _on_VolumeEffects_changed(self, old, new):
		horizons.globals.fife.sound.set_volume_effects(new)

	def _on_FrameLimit_changed(self, old, new):
		# handling value 0 for framelimit to disable limiter
		if new == 0:
			self._settings.set(SETTINGS.FIFE_MODULE, 'FrameLimitEnabled', False)
		else:
			self._settings.set(SETTINGS.FIFE_MODULE, 'FrameLimitEnabled', True)

	def _on_NetworkPort_changed(self, old, new):
		"""Sets a new value for client network port"""
		# port is saved as string due to pychan limitations
		try:
			# 0 is not a valid port, but a valid value here (used for default)
			parse_port(new)
		except ValueError:
			headline = _("Invalid network port")
			descr = _("The port you specified is not valid. It must be a number between 1 and 65535.")
			advice = _("Please check the port you entered and make sure it is in the specified range.")
			self._windows.open_error_popup(headline, descr, advice)
			# reset value and reshow settings dlg
			self._settings.set(SETTINGS.UH_MODULE, 'NetworkPort', u"0")
		else:
			# port is valid
			try:
				if NetworkInterface() is None:
					NetworkInterface.create_instance()
				NetworkInterface().network_data_changed()
			except Exception as e:
				headline = _("Failed to apply new network settings.")
				descr = _("Network features could not be initialized with the current configuration.")
				advice = _("Check the settings you specified in the network section.")
				if 0 < parse_port(new) < 1024:
					#i18n This is advice for players seeing a network error with the current config
					advice += u" " + \
						_("Low port numbers sometimes require special access privileges, try 0 or a number greater than 1024.")
				details = unicode(e)
				self._windows.open_error_popup(headline, descr, advice, details)

	def _on_Language_changed(self, old, new):
		language = LANGUAGENAMES.get_by_value(new)
		change_language(language)

	def _on_DebugLog_changed(self, old, new):
		horizons.main.set_debug_log(new)

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
