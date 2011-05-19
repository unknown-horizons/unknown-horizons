# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import glob, random
import gettext
import os

from fife import fife
from fife.extensions.basicapplication import ApplicationBase
from fife.extensions import fifelog
from fife.extensions import pychan
from fife.extensions.fife_settings import Setting, FIFE_MODULE

import horizons.main

import horizons.gui.style
from horizons.util import SQLiteAnimationLoader, Callback, parse_port
from horizons.extscheduler import ExtScheduler
from horizons.i18n import update_all_translations, load_xml_translated
from horizons.i18n.utils import find_available_languages
from horizons.constants import LANGUAGENAMES, PATHS, NETWORK
from horizons.network.networkinterface import NetworkInterface

UH_MODULE="unknownhorizons"

class LocalizedSetting(Setting):
	"""
	Localized settings dialog by using load_xml_translated() instead of
	plain load_xml().
	"""
	def _loadWidget(self, dialog):
		return load_xml_translated(dialog)

	def _showChangeRequireRestartDialog(self):
		"""Overwrites FIFE dialog call to use no xml file but a show_popup."""
		headline = _("Restart required")
		message = _("Some of your changes require a restart of Unknown Horizons.")
		horizons.main._modules.gui.show_popup(headline, message)

class Fife(ApplicationBase):
	"""
	"""
	def __init__(self):
		self.pump = []

		self._setup_settings()

		self.engine = fife.Engine()
		self.engine_settings = self.engine.getSettings()

		self.loadSettings()

		self.pychan = pychan

		self._doQuit = False
		self._doBreak = False
		self._doReturn = None
		self._gotInited = False

		self.emitter = {}
		self.emitter['bgsound'] = None
		self.emitter['effects'] = None
		self.emitter['speech'] = None


	def _setup_settings(self):
		self._setting = LocalizedSetting(app_name="unknownhorizons",
		                                 settings_file=PATHS.USER_CONFIG_FILE,
		                                 settings_gui_xml="settings.xml",
		                                 changes_gui_xml="requirerestart.xml")
		self._setting.setGuiStyle("book")

		#self.createAndAddEntry(self, module, name, widgetname, applyfunction=None, initialdata=None, requiresrestart=False)
		self._setting.createAndAddEntry(UH_MODULE, "AutosaveInterval", "autosaveinterval")
		self._setting.createAndAddEntry(UH_MODULE, "AutosaveMaxCount", "autosavemaxcount")
		self._setting.createAndAddEntry(UH_MODULE, "QuicksaveMaxCount", "quicksavemaxcount")
		self._setting.createAndAddEntry(UH_MODULE, "EdgeScrolling", "edgescrolling")

		def update_minimap(*args):
			# sry for this gross violation of the encapsulation principle
			try: horizons.main._modules.session.ingame_gui.minimap.draw()
			except AttributeError: pass # session or gui not yet initialised
		self._setting.createAndAddEntry(UH_MODULE, "MinimapRotation", "minimaprotation", \
		                                applyfunction=update_minimap)

		self._setting.createAndAddEntry(FIFE_MODULE, "BitsPerPixel", "screen_bpp",
		                                initialdata=[0, 16, 32], requiresrestart=True)

		languages_map = dict(find_available_languages())
		languages_map[_('System default')] = ''
		# English is not shipped as .mo file.
		languages_map['en'] = ''

		self._setting.createAndAddEntry(UH_MODULE, "Language", "language",
		                                applyfunction=self.update_languages,
		                                initialdata= [LANGUAGENAMES[x] for x in sorted(languages_map.keys())])
		self._setting.createAndAddEntry(UH_MODULE, "VolumeMusic", "volume_music",
		                                applyfunction=self.set_volume_music)
		self._setting.createAndAddEntry(UH_MODULE, "VolumeEffects", "volume_effects",
		                                applyfunction=self.set_volume_effects)

		self._setting.createAndAddEntry(UH_MODULE, "NetworkPort", "network_port",
		                                applyfunction=self.set_network_port)


		self._setting.entries[FIFE_MODULE]['PlaySounds'].applyfunction = lambda x: self.setup_sound()
		self._setting.entries[FIFE_MODULE]['PlaySounds'].requiresrestart = False

		self._setting.entries[FIFE_MODULE]['RenderBackend'].applyfunction = lambda x: self._show_renderbackend_warning()

	def _show_renderbackend_warning(self):
		backend = self.get_fife_setting("RenderBackend")
		if backend == 'SDL':
			headline = _("Warning")
			message = _("The SDL renderer is meant as a fallback solution only and has serious graphical glitches. \n\nUse at own risk!")
			horizons.main._modules.gui.show_popup(headline, message)

	def __setup_screen_resolutions(self):
		# Note: This call only works if the engine is inited (self.run())
		# Note: Seems that getPossibleResolutions() needs Fullscreen set ##HACK##
		possible_resolutions = ["1024x768", "1280x800", "1280x960", "1280x1024",
		                        "1366x768", "1440x900", "1600x900", "1600x1200",
		                        "1680x1050","1920x1080","1920x1200",] # Add more supported resolutions here.
		current_state = self.engine_settings.isFullScreen()
		self.engine_settings.setFullScreen(1)
		for x,y in self.engine_settings.getPossibleResolutions():
			if x >= 1024 and y >= 768 and str(x) + "x" + str(y) not in possible_resolutions:
				possible_resolutions.append(str(x) + "x" + str(y))
		self.engine_settings.setFullScreen(current_state)
		self._setting.entries[FIFE_MODULE]['ScreenResolution'].initialdata = possible_resolutions

	def update_languages(self, data=None):
		"""
		Load/Change language of Unknown Horizons. Called on startup
		and when changing the language.

		data is used when changing the language in the settings menu.
		"""

		if data is None:
			data = self._setting.get(UH_MODULE, "Language")
		languages_map = dict(find_available_languages())
		languages_map['System default'] = ''
		# English is not shipped as .mo file.
		languages_map['en'] = ''
		symbol = None
		if data == unicode('System default'):
			symbol = 'System default'
		else:
			for key, value in LANGUAGENAMES.iteritems():
				if value == data:
					symbol = key
		assert symbol is not None, "Something went badly wrong with the translation update!" + \
		       " Searching for: " + str(data) + " in " + str(LANGUAGENAMES)

		try:
			index = sorted(languages_map.keys()).index(symbol)
		# This only happens on startup when the language is not available
		# (either from the settings file or $LANG).
		except ValueError:
			print "Language %s is not available!" % data
			index = sorted(languages_map.keys()).index('System default')
			# Reset the language or the settings crashes.
			self._setting.set(UH_MODULE, "Language", 'System default')

		name, position = sorted(languages_map.items())[index]
		try:
			if name != 'System default':
				# English is not shipped as .mo file, thus if English is
				# selected we use NullTranslations to get English output.
				fallback = name == 'en'
				trans = gettext.translation('unknown-horizons', position, languages=[name], fallback=fallback)
				trans.install(unicode=True, names=['ngettext',])
			else:
				gettext.install('unknown-horizons', 'content/lang', unicode=True, names=['ngettext',])
				name = ''

		except IOError:
			print _("Configured language %(lang)s at %(place)s could not be loaded") % {'lang': name, 'place': position}
			gettext.install('unknown-horizons', 'content/lang', unicode=True, names=['ngettext',])
			self._setting.set(UH_MODULE, "Language", 'System default')
		update_all_translations()


	def init(self):
		"""
		"""
		logToPrompt, logToFile, debugPychan = True, True, False
		if self._gotInited:
			return
		#start modules
		self.log = fifelog.LogManager(self.engine, 1 if logToPrompt else 0, 1 if logToFile else 0)
		#self.log.setVisibleModules('all')

		self.engine.init()

		#temporarily select a random music file to play. TODO: Replace with proper playlist
		self.ingame_music = glob.glob('content/audio/music/*.ogg')
		self.menu_music = glob.glob('content/audio/music/menu/*.ogg')
		self.initial_menu_music_element = None
		self.next_menu_music_element = None
		self.menu_music_played = False

		#init stuff
		self.eventmanager = self.engine.getEventManager()
		#self.eventmanager.setNonConsumableKeys([fife.Key.ESCAPE, fife.Key.F10])
		self.guimanager = self.engine.getGuiManager()
		self.console = self.guimanager.getConsole()
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		self.setup_sound()
		self.imagepool = self.engine.getImagePool()
		self.animationpool = self.engine.getAnimationPool()
		self.animationloader = SQLiteAnimationLoader()
		self.animationpool.addResourceLoader(self.animationloader)

		#Set game cursor
		self.cursor = self.engine.getCursor()
		self.default_cursor_image = self.imagepool.addResourceFromFile('content/gui/images/cursors/cursor.png')
		self.tearing_cursor_image = self.imagepool.addResourceFromFile('content/gui/images/cursors/cursor_tear.png')
		self.cursor.set(fife.CURSOR_IMAGE, self.default_cursor_image)

		#init pychan
		self.pychan.init(self.engine, debugPychan)
		self.pychan.setupModalExecution(self.loop, self.breakLoop)

		from gui.widgets.inventory import Inventory
		from gui.widgets.imagefillstatusbutton import  ImageFillStatusButton
		from gui.widgets.progressbar import ProgressBar
		from gui.widgets.toggleimagebutton import ToggleImageButton
		from gui.widgets.tooltip import TooltipIcon, TooltipButton, TooltipLabel, TooltipProgressBar
		from gui.widgets.imagebutton import CancelButton, DeleteButton, OkButton
		from gui.widgets.icongroup import TabBG
		from gui.widgets.stepslider import StepSlider

		pychan.widgets.registerWidget(CancelButton)
		pychan.widgets.registerWidget(DeleteButton)
		pychan.widgets.registerWidget(Inventory)
		pychan.widgets.registerWidget(ImageFillStatusButton)
		pychan.widgets.registerWidget(OkButton)
		pychan.widgets.registerWidget(ProgressBar)
		pychan.widgets.registerWidget(TabBG)
		pychan.widgets.registerWidget(ToggleImageButton)
		pychan.widgets.registerWidget(TooltipIcon)
		pychan.widgets.registerWidget(TooltipButton)
		pychan.widgets.registerWidget(TooltipLabel)
		pychan.widgets.registerWidget(TooltipProgressBar)
		pychan.widgets.registerWidget(StepSlider)

		for name, stylepart in horizons.gui.style.STYLES.iteritems():
			self.pychan.manager.addStyle(name, stylepart)
		self.pychan.loadFonts("content/fonts/libertine.fontdef")

		self._gotInited = True
		self.setup_setting_extras()

	def setup_setting_extras(self):
		slider_initial_data = {}
		slider_event_map = {}
		self.OptionsDlg = self._setting.loadSettingsDialog()
		self.OptionsDlg.position_technique = "automatic" # "center:center"
		slider_dict = {'AutosaveInterval' : 'autosaveinterval',
						'AutosaveMaxCount' : 'autosavemaxcount',
						'QuicksaveMaxCount' : 'quicksavemaxcount'}

		for x in slider_dict.keys():
			slider_initial_data[slider_dict[x]+'_value'] = unicode(int(self._setting.get(UH_MODULE, x)))
		slider_initial_data['volume_music_value'] = unicode(int(self._setting.get(UH_MODULE, "VolumeMusic") * 500)) + '%'
		slider_initial_data['volume_effects_value'] = unicode(int(self._setting.get(UH_MODULE, "VolumeEffects") * 200)) + '%'
		self.OptionsDlg.distributeInitialData(slider_initial_data)

		for x in slider_dict.values():
			slider_event_map[x] = Callback(self.update_slider_values, x)
		slider_event_map['volume_music'] = self.set_volume_music
		slider_event_map['volume_effects'] = self.set_volume_effects
		self.OptionsDlg.mapEvents(slider_event_map)

	def update_slider_values(self, slider, factor = 1, percent = False):
		self.OptionsDlg.findChild(name=slider+'_value').text = \
		     unicode(int(self.OptionsDlg.findChild(name=slider).getValue() * factor)) \
		     + ('%' if percent else '')

	def setup_sound(self):
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.enable_sound()
		else:
			self.disable_sound()

	def get_fife_setting(self, settingname):
		return self._setting.get(FIFE_MODULE, settingname)

	def get_uh_setting(self, settingname):
		return self._setting.get(UH_MODULE, settingname)

	def set_uh_setting(self, settingname, value):
		self._setting.set(UH_MODULE, settingname, value)

	def save_settings(self):
		self._setting.saveSettings()


	def enable_sound(self):
		"""Enable all sound and start playing music."""
		if self._setting.get(FIFE_MODULE, "PlaySounds"): # Set up sound if it is enabled
			self.soundclippool = self.engine.getSoundClipPool()
			self.emitter['bgsound'] = self.soundmanager.createEmitter()
			self.emitter['bgsound'].setGain(self._setting.get(UH_MODULE, "VolumeMusic"))
			self.emitter['bgsound'].setLooping(False)
			self.emitter['effects'] = self.soundmanager.createEmitter()
			self.emitter['effects'].setGain(self._setting.get(UH_MODULE, "VolumeEffects"))
			self.emitter['effects'].setLooping(False)
			self.emitter['speech'] = self.soundmanager.createEmitter()
			self.emitter['speech'].setGain(self._setting.get(UH_MODULE, "VolumeEffects"))
			self.emitter['speech'].setLooping(False)
			self.emitter['ambient'] = []
			self.music_rand_element = random.randint(0, len(self.menu_music) - 1)
			self.initial_menu_music_element = self.music_rand_element

			self.check_music() # Start background music
			ExtScheduler().add_new_object(self.check_music, self, loops=-1)

	def disable_sound(self):
		"""Disable all sound outputs."""
		if self.emitter['bgsound'] is not None:
			self.emitter['bgsound'].reset()
		if self.emitter['effects'] is not None:
			self.emitter['effects'].reset()
		if self.emitter['speech'] is not None:
			self.emitter['speech'].reset()
		ExtScheduler().rem_call(self, self.check_music)

	def check_music(self):
		"""Used as callback to check if music is still running or if we have
		to load the next song."""
		if self.menu_music_played == False:
			if self.initial_menu_music_element == self.next_menu_music_element:
				self.ingame_music.extend(self.menu_music)
				self.music = self.ingame_music
				self.music_rand_element = random.randint(0, len(self.ingame_music) - 1)
				self.menu_music_played = True
			else:
				self.music = self.menu_music

		if hasattr(self, '_bgsound_old_byte_pos') and hasattr(self, '_bgsound_old_sample_pos'):
			if self._bgsound_old_byte_pos == self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS) and self._bgsound_old_sample_pos == self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS):
				# last track has finished (TODO: find cleaner way to check for this)
				skip = 0 if len(self.music) == 1 else random.randint(1, len(self.music)-1)
				self.music_rand_element = (self.music_rand_element + skip) % len(self.music)
				self.play_sound('bgsound', self.music[self.music_rand_element])
				if self.menu_music_played == False:
					self.next_menu_music_element = self.music_rand_element

		self._bgsound_old_byte_pos, self._bgsound_old_sample_pos = \
			    self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS), \
			    self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS)

	def play_sound(self, emitter, soundfile):
		"""Plays a soundfile on the given emitter.
		@param emitter: string with the emitters name in horizons.main.fife.emitter that is to play the  sound
		@param soundfile: string containing the path to the soundfile"""
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			emitter = self.emitter[emitter]
			assert emitter is not None, "You need to supply a initialised emitter"
			assert soundfile is not None, "You need to supply a soundfile"
			emitter.reset()
			emitter.setSoundClip(horizons.main.fife.soundclippool.addResourceFromFile(soundfile))
			emitter.play()

	def set_volume(self, emitter_name, value):
		"""Sets the volume on the emitter specified by emitter_name.
		@param emitter_name: string with the emitters name, used as key for the self.emitter dict
		@param value: double which value the emitter is to be set to range[0, 1]
		"""
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.emitter[emitter_name].setGain(value)

	def set_volume_music(self, value=None):
		"""Sets the volume of the music emitters to 'value'.
		@param value: double - value that's used to set the emitters gain.
		"""
		if not value:
			value = self.OptionsDlg.findChild(name="volume_music").getValue()
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.emitter['bgsound'].setGain(value)
		self.update_slider_values('volume_music', factor = 500, percent = True)

	def set_volume_effects(self, value=None):
		"""Sets the volume of effects, speech and ambient emitters.
		@param value: double - value that's used to set the emitters gain.
		"""
		if not value:
			value = self.OptionsDlg.findChild(name="volume_effects").getValue()
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.emitter['effects'].setGain(value)
			self.emitter['speech'].setGain(value)
			for e in self.emitter['ambient']:
				e.setGain(value*2)
		self.update_slider_values('volume_effects', factor = 200, percent = True)

	def set_network_port(self, port):
		"""Sets a new value for client network port"""
		# port is saved as string due to pychan limitations
		try:
			# 0 is not a valid port, but a valid value here (used for default)
			parse_port(port, allow_zero=True)
		except ValueError:
			headline = _("Invalid network port")
			descr = _("The port you specified is not valid. It must be  a number between 1 and 65535.")
			advice = _("Please check the port you entered and make sure it's in the specified range.")
			horizons.main._modules.gui.show_error_popup(headline, descr, advice)
			# reset value and reshow settings dlg
			self.set_uh_setting("NetworkPort", u"0")
			ExtScheduler().add_new_object(self._setting.onOptionsPress, self, 0)
		else:
			# port is valid
			try:
				if NetworkInterface() is None:
					NetworkInterface.create_instance()
				NetworkInterface().network_data_changed(connect=False)
			except Exception, e:
				headline = _(u"Failed to apply new network data.")
				descr = _(u"Networking couldn't be initialised with the current configuration.")
				advice = _(u"Check the data you entered in the Network section.")
				if 0 < parse_port(port, allow_zero=True) < 1024:
					advice += u" " + \
					       _("Low port numbers sometimes require special priviledges, try one greater than 1024 or 0.")
				details = unicode(e)
				horizons.main._modules.gui.show_error_popup(headline, descr, advice, details)
				ExtScheduler().add_new_object(self._setting.onOptionsPress, self, 0)

	def run(self):
		"""
		"""
		self.init()
		self.__setup_screen_resolutions()
		self.engine.initializePumping()
		self.loop()
		self.engine.finalizePumping()

	def loop(self):
		"""
		"""
		while not self._doQuit:
			try:
				self.engine.pump()
			except fife.Exception, e:
				print e.getMessage()
				break
			for f in self.pump:
				f()
			if self._doBreak:
				self._doBreak = False
				return self._doReturn

		self.__kill_engine()

	def __kill_engine(self):
		"""Called when the engine is quit"""
		self.cursor.set(fife.CURSOR_NATIVE) #hack to get system cursor back
		self.engine.destroy()

	def breakLoop(self, returnValue = None):
		"""
		@param returnValue:
		"""
		self._doReturn = returnValue
		self._doBreak = True

	def quit(self):
		""" Quits the engine.
		"""
		self._doQuit = True

	def _get_setting(self):
		return self._setting

	settings = property(_get_setting)
