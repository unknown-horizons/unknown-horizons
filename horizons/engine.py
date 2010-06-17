# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
from horizons.util import SQLiteAnimationLoader
from horizons.extscheduler import ExtScheduler
from horizons.i18n import update_all_translations
from horizons.i18n.utils import find_available_languages
from horizons.constants import LANGUAGENAMES, PATHS

UH_MODULE="unknownhorizons"

class Fife(ApplicationBase):
	"""
	"""
	def __init__(self):
		self.pump = []

		self._setup_settings()

		self.engine = fife.Engine()
		self.loadSettings()

		self.engine_settings = self.engine.getSettings()
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
		self._setting =  Setting(app_name="unknownhorizons",
		                         settings_file=PATHS.USER_DIR + os.sep + "settings.xml",
		                         settings_gui_xml="content/gui/settings.xml",
		                         changes_gui_xml="content/gui/requirerestart.xml")
		self._setting.setGuiStyle("book")

		#self.createAndAddEntry(self, module, name, widgetname, applyfunction=None, initialdata=None, requiresrestart=False)
		self._setting.createAndAddEntry(UH_MODULE, "AutosaveInterval", "autosaveinterval",
		                                initialdata=range(0, 60, 2))
		self._setting.createAndAddEntry(UH_MODULE, "AutosaveMaxCount", "autosavemaxcount",
		                                initialdata=range(1, 30))
		self._setting.createAndAddEntry(UH_MODULE, "QuicksaveMaxCount", "quicksavemaxcount",
		                                initialdata=range(1, 30))

		languages_map = dict(find_available_languages())
		languages_map[_('System default')] = ''

		self._setting.createAndAddEntry(UH_MODULE, "Language", "language",
		                                applyfunction=self.update_languages,
		                                initialdata= [LANGUAGENAMES[x] for x in sorted(languages_map.keys())])
		self._setting.createAndAddEntry(UH_MODULE, "VolumeMusic", "volume_music",
		                                applyfunction=lambda x: self.set_volume_music(x))
		self._setting.createAndAddEntry(UH_MODULE, "VolumeEffects", "volume_effects",
		                                applyfunction=lambda x: self.set_volume_effects(x))

		self._setting.entries[FIFE_MODULE]['PlaySounds'].applyfunction = lambda x: self.setup_sound()
		self._setting.entries[FIFE_MODULE]['PlaySounds'].requiresrestart = False

	def update_languages(self, data=None):
		if data is None:
			data = self._setting.get(UH_MODULE, "Language")
		languages_map = dict(find_available_languages())
		languages_map['System default'] = ''
		symbol = None
		if data == unicode('System default'):
			symbol = 'System default'
		else:
			for key, value in LANGUAGENAMES.iteritems():
				if value == data:
					symbol = key
		assert symbol is not None, "Something went badly wrong with the translation update!" + \
		       " Searching for: " + str(data) + " in " + str(LANGUAGENAMES)

		index = sorted(languages_map.keys()).index(symbol)
		name, position = sorted(languages_map.items())[index]
		try:
			if name != 'System default':
				trans = gettext.translation('unknownhorizons', position, languages=[name])
				trans.install(unicode=1)
			else:
				gettext.install('unknownhorizons', 'build/mo', unicode=1)
				name = ''

		except IOError:
			print _("Configured language %(lang)s at %(place)s could not be loaded") % {'lang': settings.language.name, 'place': settings.language.position}
			install('unknownhorizons', 'build/mo', unicode=1)
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
		self.menu_music_played = 0

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
		self.default_cursor_image = self.imagepool.addResourceFromFile('content/gui/images/misc/cursor.png')
		self.tearing_cursor_image = self.imagepool.addResourceFromFile('content/gui/images/misc/cursor_tear.png')
		self.cursor.set(fife.CURSOR_IMAGE, self.default_cursor_image)

		#init pychan
		self.pychan.init(self.engine, debugPychan)
		self.pychan.setupModalExecution(self.loop, self.breakLoop)

		from gui.widgets.inventory import Inventory
		from gui.widgets.imagefillstatusbutton import  ImageFillStatusButton
		from gui.widgets.progressbar import ProgressBar
		from gui.widgets.toggleimagebutton import ToggleImageButton
		from gui.widgets.tooltip import TooltipIcon, TooltipButton, TooltipLabel, TooltipProgressBar

		pychan.widgets.registerWidget(Inventory)
		pychan.widgets.registerWidget(ImageFillStatusButton)
		pychan.widgets.registerWidget(ProgressBar)
		pychan.widgets.registerWidget(ToggleImageButton)
		pychan.widgets.registerWidget(TooltipIcon)
		pychan.widgets.registerWidget(TooltipButton)
		pychan.widgets.registerWidget(TooltipLabel)
		pychan.widgets.registerWidget(TooltipProgressBar)

		for name, stylepart in horizons.gui.style.STYLES.iteritems():
			self.pychan.manager.addStyle(name, stylepart)
		self.pychan.loadFonts("content/fonts/libertine.fontdef")

		self._gotInited = True

	def setup_sound(self):
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.enable_sound()
		else:
			self.disable_sound()

	def get_fife_setting(self, settingname):
		return self._setting.get(FIFE_MODULE, settingname)

	def get_uh_setting(self, settingname):
		return self._setting.get(UH_MODULE, settingname)

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
		if self.menu_music_played == 0:
			if self.initial_menu_music_element == self.next_menu_music_element:
				self.ingame_music.extend(self.menu_music)
				self.music = self.ingame_music
				self.music_rand_element = random.randint(0, len(self.ingame_music) - 1)
				self.menu_music_played = 1
			else:
				self.music = self.menu_music

		if hasattr(self, '_bgsound_old_byte_pos') and hasattr(self, '_bgsound_old_sample_pos'):
			if self._bgsound_old_byte_pos == self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS) and self._bgsound_old_sample_pos == self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS):
				self.music_rand_element = self.music_rand_element + 1 if \
					    self.music_rand_element + 1 < len(self.music) else 0
				self.play_sound('bgsound', self.music[self.music_rand_element])
				if self.menu_music_played == 0:
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

	def set_volume_music(self, value):
		"""Sets the volume of the music emitters to 'value'.
		@param value: double - value that's used to set the emitters gain.
		"""
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.emitter['bgsound'].setGain(value)


	def set_volume_effects(self, value):
		"""Sets the volume of effects, speech and ambient emitters.
		@param value: double - value that's used to set the emitters gain.
		"""
		if self._setting.get(FIFE_MODULE, "PlaySounds"):
			self.emitter['effects'].setGain(value)
			self.emitter['speech'].setGain(value)
			for e in self.emitter['ambient']:
				e.setGain(value*2)

	def run(self):
		"""
		"""
		self.init()
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