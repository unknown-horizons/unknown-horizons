# -*- coding: utf-8 -*-
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

import logging

from fife import fife
from fife.extensions.fife_settings import FIFE_MODULE
from horizons.gui.quotes import QUOTES_SETTINGS

import horizons.main

from horizons.i18n import change_language, find_available_languages
from horizons.util import Callback, parse_port
from horizons.extscheduler import ExtScheduler
from horizons.constants import LANGUAGENAMES, PATHS
from horizons.network.networkinterface import NetworkInterface
from horizons.engine import UH_MODULE

class SettingsHandler(object):
	"""Handles settings-related boilerplate code as well as gui."""

	def __init__(self, engine):
		self.engine = engine

	@property
	def _setting(self):
		return self.engine._setting

	def add_settings(self):

		# TODO: find a way to apply changing to a running game in a clean fashion
		#       possibility: use signaling via changelistener
		def update_minimap(*args):
			try: horizons.main._modules.session.ingame_gui.minimap.draw()
			except AttributeError: pass # session or gui not yet initialised

		def update_autosave_interval(*args):
			try: horizons.main._modules.session.reset_autosave()
			except AttributeError: pass # session or gui not yet initialised


		#self.createAndAddEntry(self, module, name, widgetname, applyfunction=None, initialdata=None, requiresrestart=False)
		self._setting.createAndAddEntry(UH_MODULE, "AutosaveInterval", "autosaveinterval",
				                        applyfunction=update_autosave_interval)
		self._setting.createAndAddEntry(UH_MODULE, "AutosaveMaxCount", "autosavemaxcount")
		self._setting.createAndAddEntry(UH_MODULE, "QuicksaveMaxCount", "quicksavemaxcount")
		self._setting.createAndAddEntry(UH_MODULE, "EdgeScrolling", "edgescrolling")
		self._setting.createAndAddEntry(UH_MODULE, "CursorCenteredZoom", "cursor_centered_zoom")
		self._setting.createAndAddEntry(UH_MODULE, "UninterruptedBuilding", "uninterrupted_building")
		self._setting.createAndAddEntry(UH_MODULE, "AutoUnload", "auto_unload")
		self._setting.createAndAddEntry(UH_MODULE, "MinimapRotation", "minimaprotation",
				                        applyfunction=update_minimap)

		self._setting.createAndAddEntry(UH_MODULE, "QuotesType", "quotestype",
		                                initialdata=QUOTES_SETTINGS,
		                                applyfunction=self.set_quotestype)
		self._setting.createAndAddEntry(UH_MODULE, "ShowResourceIcons", "show_resource_icons")

		self._setting.createAndAddEntry(FIFE_MODULE, "BitsPerPixel", "screen_bpp",
				                        initialdata=[0, 16, 32], requiresrestart=True)

		languages = find_available_languages().keys()

		self._setting.createAndAddEntry(UH_MODULE, "Language", "uni_language",
				                        applyfunction=self.update_languages,
				                        initialdata= [LANGUAGENAMES[x] for x in sorted(languages)])
		self._setting.createAndAddEntry(UH_MODULE, "VolumeMusic", "volume_music",
				                        applyfunction=self.set_volume_music)
		self._setting.createAndAddEntry(UH_MODULE, "VolumeEffects", "volume_effects",
				                        applyfunction=self.set_volume_effects)

		self._setting.createAndAddEntry(UH_MODULE, "NetworkPort", "network_port",
				                        applyfunction=self.set_network_port)

		self._setting.createAndAddEntry(UH_MODULE, "DebugLog", "debug_log",
				                        applyfunction=self.set_debug_log)


		self._setting.entries[FIFE_MODULE]['PlaySounds'].applyfunction = lambda x: self.engine.sound.setup_sound()
		self._setting.entries[FIFE_MODULE]['PlaySounds'].requiresrestart = False

		self._setting.entries[FIFE_MODULE]['RenderBackend'].applyfunction = lambda x: self._show_renderbackend_warning()

		self._setting.createAndAddEntry(FIFE_MODULE, "FrameLimit", "fps_rate",
				                        initialdata=[30, 45, 60, 90, 120], requiresrestart=True)

		self._setting.createAndAddEntry(FIFE_MODULE, "MouseSensitivity", "mousesensitivity",
				                        #read comment in set_mouse_sensitivity function about this
				                        #applyfunction=self.set_mouse_sensitivity, \
				                        requiresrestart=True)

	def apply_settings(self):
		"""Called on startup to apply the effects of settings"""
		self.update_languages()
		if self.engine.get_uh_setting("DebugLog"):
			self.set_debug_log(True, startup=True)

	def setup_setting_extras(self):
		"""Some kind of setting gui initalisation"""
		#slider_initial_data exposes initial data when menu settings opened
		slider_initial_data = {}
		#slider_event_map should contain slider name as key and function
		#which will update slider as value
		#read fife-extension-pychan-Widget-widget.py if u want know how it works
		slider_event_map = {}
		self.settings_dialog = self._setting.loadSettingsDialog()
		self.settings_dialog.position_technique = "automatic" # "center:center"
		slider_dict = {'AutosaveInterval' : 'autosaveinterval',
				       'AutosaveMaxCount' : 'autosavemaxcount',
				       'QuicksaveMaxCount' : 'quicksavemaxcount'}

		for x in slider_dict.keys():
			slider_initial_data[slider_dict[x]+'_value'] = unicode(int(self._setting.get(UH_MODULE, x)))
		slider_initial_data['volume_music_value'] = unicode(int(self._setting.get(UH_MODULE, "VolumeMusic") * 500)) + '%'
		slider_initial_data['volume_effects_value'] = unicode(int(self._setting.get(UH_MODULE, "VolumeEffects") * 200)) + '%'
		slider_initial_data['mousesensitivity_value'] = unicode("%.1f" % float(self._setting.get(FIFE_MODULE, "MouseSensitivity") * 100)) + '%'

		self.settings_dialog.distributeInitialData(slider_initial_data)

		for x in slider_dict.values():
			slider_event_map[x] = Callback(self.update_slider_values, x)
		slider_event_map['volume_music'] = self.set_volume_music
		slider_event_map['volume_effects'] = self.set_volume_effects
		slider_event_map['mousesensitivity'] = self.set_mouse_sensitivity

		self.settings_dialog.mapEvents(slider_event_map)

	def _show_renderbackend_warning(self):
		backend = self.engine.get_fife_setting("RenderBackend")
		if backend == 'SDL':
			headline = _("Warning")
			#i18n Warning popup shown in settings when SDL is selected as renderer.
			message = _("The SDL renderer is meant as a fallback solution only and has serious graphical glitches. \n\nUse at own risk!")
			horizons.main._modules.gui.show_popup(headline, message)

	def set_quotestype(self, *args):
		type = 0
		if args:
			type = int(args[0])
		self._setting.set(UH_MODULE, "QuotesType", type)

	def update_slider_values(self, slider, factor=1, unit=''):
		"""
		slider - slider name
		factor - value will be multiplied by factor
		unit - this string will be added to the end
		"""
		if slider == "mousesensitivity":
			#for floating wanted
			self.settings_dialog.findChild(name=slider + '_value').text = \
				u"%.2f%s" % (float(self.settings_dialog.findChild(name=slider).value * factor), unit)
		else:
			self.settings_dialog.findChild(name=slider + '_value').text = \
				u"%s%s" % (int(self.settings_dialog.findChild(name=slider).value * factor), unit)


	# Handlers for setting interaction

	def set_mouse_sensitivity(self, value=None):
		"""
		Use this function for update slider value(and label) and change mouse sensitivity.
		uncomment "else" with func below and "applyfunction=self.set_mouse_sensitivity" above
		 if u know how to change sensitivity values in runtime
		"""
		if not value:
			#value=None means function called not for saving(and changing)
			#sensitivity, just for slider update in this version value=None everytime
			value = self.settings_dialog.findChild(name="mousesensitivity").value
		#else:
		#    self.engine_settings.setMouseSensitivity(value)
		self.update_slider_values('mousesensitivity', factor=100, unit='%')


	def set_volume_effects(self, value=None):
		"""Sets the volume of effects, speech and ambient emitters.
		@param value: double - value that's used to set the emitters gain.
		"""
		if not value:
			value = self.settings_dialog.findChild(name="volume_effects").value
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.engine.sound.emitter['effects'].setGain(value)
			self.engine.sound.emitter['speech'].setGain(value)
			for e in self.engine.sound.emitter['ambient']:
				e.setGain(value*2)
		self.update_slider_values('volume_effects', factor=200, unit='%')

	def set_volume(self, emitter_name, value):
		"""Sets the volume on the emitter specified by emitter_name.
		@param emitter_name: string with the emitters name, used as key for the self.emitter dict
		@param value: double which value the emitter is to be set to range[0, 1]
		"""
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.engine.sound.emitter[emitter_name].setGain(value)

	def set_volume_music(self, value=None):
		"""Sets the volume of the music emitters to 'value'.
		@param value: double - value that's used to set the emitters gain.
		"""
		if not value:
			value = self.settings_dialog.findChild(name="volume_music").value
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.engine.sound.emitter['bgsound'].setGain(value)
		self.update_slider_values('volume_music', factor=500, unit='%')


	def set_network_port(self, port):
		"""Sets a new value for client network port"""
		# port is saved as string due to pychan limitations
		try:
			# 0 is not a valid port, but a valid value here (used for default)
			parse_port(port, allow_zero=True)
		except ValueError:
			headline = _("Invalid network port")
			descr = _("The port you specified is not valid. It must be a number between 1 and 65535.")
			advice = _("Please check the port you entered and make sure it is in the specified range.")
			horizons.main._modules.gui.show_error_popup(headline, descr, advice)
			# reset value and reshow settings dlg
			self.engine.set_uh_setting("NetworkPort", u"0")
			ExtScheduler().add_new_object(self._setting.onOptionsPress, self.engine, 0)
		else:
			# port is valid
			try:
				if NetworkInterface() is None:
					NetworkInterface.create_instance()
				NetworkInterface().network_data_changed(connect=False)
			except Exception as e:
				headline = _(u"Failed to apply new network settings.")
				descr = _("Network features could not be initialized with the current configuration.")
				advice = _("Check the settings you specified in the network section.")
				if 0 < parse_port(port, allow_zero=True) < 1024:
					#i18n This is advice for players seeing a network error with the current config
					advice += u" " + \
						_("Low port numbers sometimes require special access privileges, try 0 or a number greater than 1024.")
				details = unicode(e)
				horizons.main._modules.gui.show_error_popup(headline, descr, advice, details)
				ExtScheduler().add_new_object(self._setting.onOptionsPress, self.engine, 0)


	def update_languages(self, data=None):
		if data is None:
			data = self._setting.get(UH_MODULE, "Language")

		language = LANGUAGENAMES.get_by_value(data)
		change_language(language)

	def set_debug_log(self, data, startup=False):
		"""
		@param data: boolean
		@param startup: True if on startup to apply settings. Won't show popup
		"""
		options = horizons.main.command_line_arguments

		if data: # enable logging
			if options.debug:
				# log file is already set up, just make sure everything is logged
				logging.getLogger().setLevel( logging.DEBUG )
			else: # set up all anew
				class Data(object):
					debug = False
					debug_log_only = True
					logfile = None
					debug_module = []
				# use setup call reference, see run_uh.py
				options.setup_debugging(Data)
				options.debug = True

			if not startup:
				headline = _("Logging enabled")
				#xgettext:python-format
				msg = _("Logs are written to {directory}.").format(directory=PATHS.LOG_DIR)
				horizons.main._modules.gui.show_popup(headline, msg)

		else: #disable logging
			logging.getLogger().setLevel( logging.WARNING )
			# keep debug flag in options so to not reenable it fully twice
			# on reenable, onyl the level will be reset

# misc utility

def get_screen_resolutions():
	"""Create an instance of fife.DeviceCaps and compile a list of possible resolutions.

			NOTE:
				- This call only works if the engine is inited (self.run())
	"""
	possible_resolutions = []

	_MIN_X = 800
	_MIN_Y = 600

	devicecaps = fife.DeviceCaps()
	devicecaps.fillDeviceCaps()

	for screenmode in devicecaps.getSupportedScreenModes():
		x = screenmode.getWidth()
		y = screenmode.getHeight()
		if x < _MIN_X or y < _MIN_Y:
			continue
		res = str(x) + 'x' + str(y)
		if res not in possible_resolutions:
			possible_resolutions.append(res)

	possible_resolutions.sort()

	return possible_resolutions
