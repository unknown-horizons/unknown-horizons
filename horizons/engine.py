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

import glob
import random
import gettext
import os
import locale
import platform
import shutil

from fife import fife
from fife.extensions.basicapplication import ApplicationBase
from fife.extensions import fifelog
from fife.extensions import pychan
from fife.extensions.serializers.simplexml import SimpleXMLSerializer

from fife.extensions.fife_settings import Setting, FIFE_MODULE

import horizons.main

import horizons.gui.style
from horizons.util import SQLiteAnimationLoader, SQLiteAtlasLoader, Callback, parse_port
from horizons.extscheduler import ExtScheduler
from horizons.i18n import update_all_translations
from horizons.util.gui import load_uh_widget
from horizons.i18n.utils import find_available_languages
from horizons.constants import LANGUAGENAMES, PATHS
from horizons.network.networkinterface import NetworkInterface

UH_MODULE = "unknownhorizons"

class LocalizedSetting(Setting):
	"""
	Localized settings dialog by using load_uh_widget() instead of
	plain load_xml().
	"""
	def _loadWidget(self, dialog):
		wdg = load_uh_widget(dialog, style="book")
		# HACK: fife settings call stylize, which breaks our styling on widget load
		no_restyle_str = "do_not_restyle_this"
		self.setGuiStyle(no_restyle_str)
		def no_restyle(style):
			if style != no_restyle_str:
				wdg.stylize(style)
		wdg.stylize = no_restyle
		return wdg

	def _showChangeRequireRestartDialog(self):
		"""Overwrites FIFE dialog call to use no xml file but a show_popup."""
		headline = _("Restart required")
		message = _("Some of your changes require a restart of Unknown Horizons.")
		horizons.main._modules.gui.show_popup(headline, message)

	def setDefaults(self):
		title = _("Restore default settings")
		msg = _("This will delete all changes to the settings you made so far.") + \
		      u" " + _("Do you want to continue?")
		try:
			confirmed = horizons.main._modules.gui.show_popup(title, msg, \
			                                                  show_cancel_button=True)
		except AttributeError: #no gui available, called by e.g. cmd line param
			confirmed = True
		if confirmed:
			try:
				super(LocalizedSetting, self).setDefaults()
			except AttributeError, err: #weird stuff happens in settings module reset
				print "A problem occured while updating: %s" % err + "\n" + \
				      "Please contact the developers if this happens more than once."

class Fife(ApplicationBase):
	"""
	"""
	def __init__(self):
		self.pump = []

		self._setup_settings()

		self.engine = fife.Engine()
		self.engine_settings = self.engine.getSettings()

		logToPrompt, logToFile, debugPychan = True, True, False
		self._log = fifelog.LogManager(self.engine, 1 if logToPrompt else 0, 1 if logToFile else 0)

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


	# existing settings not part of this gui or the fife defaults
	# (required for preserving values when upgrading settings file)
	UNREFERENCED_SETTINGS = {UH_MODULE: ["Nickname", "AIPlayers"] }

	def _setup_settings(self, check_file_version=True):
		_user_config_file = os.path.join( os.getcwd(), PATHS.USER_CONFIG_FILE )
		if not os.path.exists(_user_config_file):
			check_file_version = False
		if check_file_version:
			# check if user settings file is the current one

			# NOTE: SimpleXMLSerializer can't handle relative paths, it fails silently
			# (although the doc states otherwise) - thus translate paths to absolute ones
			user_config_parser = SimpleXMLSerializer( _user_config_file )
			user_settings_version = user_config_parser.get("meta", "SettingsVersion", -1)
			_template_config_file = os.path.join( os.getcwd(), PATHS.CONFIG_TEMPLATE_FILE )
			template_config_parser = SimpleXMLSerializer( _template_config_file )
			template_settings_version = template_config_parser.get("meta", "SettingsVersion")

			if template_settings_version > user_settings_version: # we have to update the file
				# create settings so we have a list of all settings
				self._setup_settings(check_file_version=False)

				# save settings here
				entries = []
				def update_value(modulename, entryname):
					# retrieve values from loaded settings file
					try:
						value = self._setting.get(modulename, entryname)
					except UnicodeEncodeError: # this can happen when unicode data is saved as str
						value = "default"
					entries.append( (modulename, entryname, value ) )

				# update known settings and unreferenced settings
				for modulename, module in self._setting.entries.iteritems():
					for entryname in module.iterkeys():
						update_value(modulename, entryname)
				for modulename, entry_list in self.UNREFERENCED_SETTINGS.iteritems():
					for entryname in entry_list:
						update_value(modulename, entryname)

				# write actual new file
				shutil.copy( PATHS.CONFIG_TEMPLATE_FILE, PATHS.USER_CONFIG_FILE )
				user_config_parser = SimpleXMLSerializer( _user_config_file )
				for modulename, entryname, value in entries:
					user_config_parser.set(modulename, entryname, value)
				user_config_parser.save()

		self._setting = LocalizedSetting(app_name=UH_MODULE,
		                                 settings_file=PATHS.USER_CONFIG_FILE,
		                                 settings_gui_xml="settings.xml",
		                                 changes_gui_xml="requirerestart.xml",
		                                 default_settings_file=PATHS.CONFIG_TEMPLATE_FILE)

		# TODO: find a way to apply changing to a running game in a clean fashion
		#       possibility: use singaling via changelistener
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
		self._setting.createAndAddEntry(UH_MODULE, "UninterruptedBuilding", "uninterrupted_building")

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
			#i18n Warning popup shown in settings when SDL is selected as renderer.
			message = _("The SDL renderer is meant as a fallback solution only and has serious graphical glitches. \n\nUse at own risk!")
			horizons.main._modules.gui.show_popup(headline, message)

	def __setup_screen_resolutions(self):
		""" create an instance of fife.DeviceCaps and compile a list of possible resolutions

			NOTE:
				- This call only works if the engine is inited (self.run())
		"""
		possible_resolutions = []

		_MIN_X = 1024
		_MIN_Y = 768

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
				if platform.system() == "Windows": # win doesn't set the language variable by default
					os.environ[ 'LANGUAGE' ] = locale.getdefaultlocale()[0]
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
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		self.setup_sound()
		self.imagemanager = self.engine.getImageManager()
		self.targetrenderer = self.engine.getTargetRenderer()
		self.use_atlases = False
		if self.use_atlases: self.animationloader = SQLiteAtlasLoader()
		else: self.animationloader =  SQLiteAnimationLoader()

		#Set game cursor
		self.cursor = self.engine.getCursor()
		self.default_cursor_image = self.imagemanager.load('content/gui/images/cursors/cursor.png')
		self.tearing_cursor_image = self.imagemanager.load('content/gui/images/cursors/cursor_tear.png')
		self.attacking_cursor_image = self.imagemanager.load('content/gui/images/cursors/cursor_attack.png')
		self.cursor.set(self.default_cursor_image)

		#init pychan
		self.pychan.init(self.engine, debugPychan)
		self.pychan.setupModalExecution(self.loop, self.breakLoop)
		self.console = self.pychan.manager.hook.guimanager.getConsole()

		from horizons.gui.widgets.inventory import Inventory
		from horizons.gui.widgets.buysellinventory import BuySellInventory
		from horizons.gui.widgets.imagefillstatusbutton import  ImageFillStatusButton
		from horizons.gui.widgets.progressbar import ProgressBar
		from horizons.gui.widgets.toggleimagebutton import ToggleImageButton
		from horizons.gui.widgets.tooltip import TooltipIcon, TooltipButton, TooltipLabel, TooltipProgressBar
		from horizons.gui.widgets.imagebutton import CancelButton, DeleteButton, OkButton
		from horizons.gui.widgets.icongroup import TabBG
		from horizons.gui.widgets.stepslider import StepSlider
		from horizons.gui.widgets.unitoverview import HealthWidget, StanceWidget, WeaponStorageWidget

		widgets = [OkButton, CancelButton, DeleteButton,
		           Inventory, BuySellInventory, ImageFillStatusButton,
		           ProgressBar, StepSlider, TabBG, ToggleImageButton,
		           TooltipIcon, TooltipButton, TooltipLabel, TooltipProgressBar,
		           HealthWidget, StanceWidget, WeaponStorageWidget]
		map(pychan.widgets.registerWidget, widgets)

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

	def update_slider_values(self, slider, factor = 1, unit = ''):
		self.OptionsDlg.findChild(name=slider+'_value').text = \
		     u"%s%s" % (int(self.OptionsDlg.findChild(name=slider).getValue() * factor), unit)

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
			self.soundclipmanager = self.engine.getSoundClipManager()
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
			if self._bgsound_old_byte_pos == self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS) and \
			   self._bgsound_old_sample_pos == self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS):
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
			emitter.setSoundClip(horizons.main.fife.soundclipmanager.load(soundfile))
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
		self.update_slider_values('volume_music', factor = 500, unit = '%')

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
		self.update_slider_values('volume_effects', factor = 200, unit = '%')

	def get_locale(self):
		for locale_code, langname in LANGUAGENAMES.items():
			if langname == self.get_uh_setting('Language'):
				return locale_code
		# TODO : better way to find 'System default' ?
		try:
			default_locale, default_encoding = locale.getdefaultlocale()
			return default_locale.split('_')[0]
		except:
			# If default locale could not be detected use 'EN' as fallback
			return "en"

	def set_network_port(self, port):
		"""Sets a new value for client network port"""
		# port is saved as string due to pychan limitations
		try:
			# 0 is not a valid port, but a valid value here (used for default)
			parse_port(port, allow_zero=True)
		except ValueError:
			headline = _("Invalid network port")
			descr = _("The port you specified is not valid. It must be a number between 1 and 65535.")
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
					#i18n This is advice for players seeing a network error with the current config
					advice += u" " + \
					       _("Low port numbers sometimes require special privileges, try one greater than 1024 or 0.")
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
		self.__kill_engine()
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
