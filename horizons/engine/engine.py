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

import os
import shutil
import locale

from fife import fife
from fife.extensions.basicapplication import ApplicationBase
from fife.extensions import pychan
from fife.extensions.serializers.simplexml import SimpleXMLSerializer

from fife.extensions.fife_settings import FIFE_MODULE

from horizons.util import SQLiteAnimationLoader, SQLiteAtlasLoader
from horizons.constants import LANGUAGENAMES, PATHS, GFX
from horizons.engine.settingshandler import SettingsHandler, get_screen_resolutions
from horizons.engine.sound import Sound
from horizons.engine.settingsdialog import SettingsDialog
from horizons.engine.pychan_util import init_pychan
from horizons.engine import UH_MODULE


class Fife(ApplicationBase):
	"""
	Basic initiation of engine. Followed later by init().
	"""
	def __init__(self):
		self.pump = []

		self._setting_handler = SettingsHandler(self)
		self._setup_settings()

		self.engine = fife.Engine()
		self.engine_settings = self.engine.getSettings()

		super(Fife, self).initLogging()

		self.loadSettings()

		self.pychan = pychan

		self.quit_requested = False
		self.break_requested = False
		self.return_values = None
		self._got_inited = False


	# existing settings not part of this gui or the fife defaults
	# (required for preserving values when upgrading settings file)
	UNREFERENCED_SETTINGS = {UH_MODULE: ["Nickname", "AIPlayers", "ClientID"] }

	def _setup_settings(self, check_file_version=True):
		_user_config_file = os.path.join( os.getcwd(), PATHS.USER_CONFIG_FILE )
		if check_file_version and os.path.exists(_user_config_file):
			# check if user settings file is the current one

			# NOTE: SimpleXMLSerializer can't handle relative paths, it fails silently
			# (although the doc states otherwise) - thus translate paths to absolute ones
			user_config_parser = SimpleXMLSerializer( _user_config_file )
			user_settings_version = user_config_parser.get("meta", "SettingsVersion", -1)
			_template_config_file = os.path.join( os.getcwd(), PATHS.CONFIG_TEMPLATE_FILE )
			template_config_parser = SimpleXMLSerializer( _template_config_file )
			template_settings_version = template_config_parser.get("meta", "SettingsVersion")

			if template_settings_version > user_settings_version: # we have to update the file
				print 'Discovered old settings file, auto-upgrading: %s -> %s' % \
				      (user_settings_version, template_settings_version)
				# create settings so we have a list of all settings
				self._setup_settings(check_file_version=False)

				# save settings here
				entries = []

				# need safe default value
				default_value = object()

				def update_value(modulename, entryname):
					# retrieve values from loaded settings file
					try:
						value = self._setting.get(modulename, entryname, default_value)
					except UnicodeEncodeError: # this can happen when unicode data is saved as str
						value = "default"
					if value is not default_value:
						entries.append( (modulename, entryname, value ) )

				# collect values from known settings and unreferenced settings
				for modulename, module in self._setting.entries.iteritems():
					for entryname in module.iterkeys():
						update_value(modulename, entryname)
				for modulename, entry_list in self.UNREFERENCED_SETTINGS.iteritems():
					for entryname in entry_list:
						update_value(modulename, entryname)

				# patch old values
				if user_settings_version <= 10:
					old_entries = entries
					entries = []
					for i in old_entries:
						if i[0] == UH_MODULE and i[1] == "Language":
							entries.append( (i[0], i[1], LANGUAGENAMES.get_by_value(i[2])) )
						else:
							entries.append(i)

				# write actual new file
				shutil.copy( PATHS.CONFIG_TEMPLATE_FILE, PATHS.USER_CONFIG_FILE )
				user_config_parser = SimpleXMLSerializer( _user_config_file )
				for modulename, entryname, value in entries:
					user_config_parser.set(modulename, entryname, value)
				user_config_parser.save()

		self._setting = SettingsDialog(app_name=UH_MODULE,
				                         settings_file=PATHS.USER_CONFIG_FILE,
				                         settings_gui_xml="settings.xml",
				                         changes_gui_xml="requirerestart.xml",
				                         default_settings_file=PATHS.CONFIG_TEMPLATE_FILE)

		self._setting_handler.add_settings()

	def init(self):
		"""Second initialisation stage of engine
		"""
		self.engine.init()

		#init stuff
		self.eventmanager = self.engine.getEventManager()
		#self.eventmanager.setNonConsumableKeys([fife.Key.ESCAPE, fife.Key.F10])
		self.sound = Sound(self)
		self.imagemanager = self.engine.getImageManager()
		self.targetrenderer = self.engine.getTargetRenderer()
		self.use_atlases = GFX.USE_ATLASES
		if self.use_atlases:
			self.animationloader = SQLiteAtlasLoader()
		else:
			self.animationloader = SQLiteAnimationLoader()

		#Set game cursor
		self.cursor = self.engine.getCursor()
		cursor_images = {
			'default':   'content/gui/images/cursors/cursor.png',
			'tearing':   'content/gui/images/cursors/cursor_tear.png',
			'attacking': 'content/gui/images/cursors/cursor_attack.png',
			'pipette':   'content/gui/images/cursors/cursor_pipette.png',
			'rename':    'content/gui/images/cursors/cursor_rename.png',
		}
		self.cursor_images = dict( (k, self.imagemanager.load(v)) for k, v in  cursor_images.iteritems() )
		self.cursor.set( self.cursor_images['default'] )

		#init pychan
		debug_pychan = self.get_fife_setting('PychanDebug') # default is False
		self.pychan.init(self.engine, debug_pychan) # pychan debug mode may have performance impacts
		self.pychan.setupModalExecution(self.loop, self.breakLoop)
		self.console = self.pychan.manager.hook.guimanager.getConsole()

		init_pychan()
		self.pychanmanager = pychan.internal.get_manager()

		self._setting_handler.apply_settings()

		self._gotInited = True

	def show_settings(self):
		"""Show fife settings gui"""
		if not hasattr(self, "_settings_extra_inited "):
			self._setting_handler.setup_setting_extras()
			self._settings_extra_inited = True
		self._setting.onOptionsPress()

	def set_cursor_image(self, which="default"):
		"""Sets a certain cursor image.
		See definition of cursor_images for reference."""
		self.cursor.set( self.cursor_images[which] )

	def get_fife_setting(self, settingname):
		return self._setting.get(FIFE_MODULE, settingname)

	def set_fife_setting(self, settingname, value):
		"""Probably saves setting in memory. Call save_settings() later"""
		return self._setting.set(FIFE_MODULE, settingname, value)

	def get_uh_setting(self, settingname):
		return self._setting.get(UH_MODULE, settingname)

	def set_uh_setting(self, settingname, value):
		"""Probably saves setting in memory. Call save_settings() later"""
		self._setting.set(UH_MODULE, settingname, value)

	def save_settings(self):
		self._setting.saveSettings()

	def play_sound(self, emitter, soundfile):
		"""Plays a soundfile on the given emitter.
		@param emitter: string with the emitters name in horizons.main.fife.sound.emitter that is to play the  sound
		@param soundfile: string containing the path to the soundfile"""
		self.sound.play_sound(emitter, soundfile)

	def get_locale(self):
		for locale_code, langname in LANGUAGENAMES.items():
			if langname == self.get_uh_setting('Language'):
				if not langname == 'System default':
					return locale_code
		try:
			default_locale, default_encoding = locale.getdefaultlocale()
			return default_locale.split('_')[0]
		except (ValueError, AttributeError):
			# OS X sometimes returns 'UTF-8' as locale, which is a ValueError.
			# If no locale is set at all, the split will fail, which is an AttributeError.
			# Use 'EN' as fallback in both cases since we cannot reasonably detect the locale.
			return "en"

	def run(self):
		"""
		"""
		assert self._gotInited

		self._setting.setAvailableScreenResolutions(get_screen_resolutions())

		self.engine.initializePumping()
		self.loop()
		self.engine.finalizePumping()
		self.__kill_engine()

	def loop(self):
		"""
		"""
		while not self.quit_requested:
			try:
				self.engine.pump()
			except fife.Exception as e:
				print e.getMessage()
				break
			for f in self.pump:
				f()
			if self.break_requested:
				self.break_requested = False
				return self.return_values

	def __kill_engine(self):
		"""Called when the engine is quit"""
		self.cursor.set(fife.CURSOR_NATIVE) #hack to get system cursor back
		self.engine.destroy()

	def breakLoop(self, returnValue=None):
		"""
		@param returnValue:
		"""
		self.return_values = returnValue
		self.break_requested = True

	def quit(self):
		""" Quits the engine.
		"""
		self.quit_requested = True
