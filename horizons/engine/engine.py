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


import locale
import logging

from fife import fife
from fife.extensions import fifelog, pychan

from horizons.constants import LANGUAGENAMES, PATHS, SETTINGS
from horizons.engine.pychan_util import init_pychan
from horizons.engine.settings import Settings
from horizons.engine.sound import Sound
from horizons.util.loaders.sqliteanimationloader import SQLiteAnimationLoader
from horizons.util.loaders.sqliteatlasloader import SQLiteAtlasLoader


class Fife:
	"""
	Basic initiation of engine. Followed later by init().
	"""
	log = logging.getLogger('engine.engine')

	def __init__(self):
		self.pump = []

		self._setting = Settings(PATHS.USER_CONFIG_FILE, PATHS.SETTINGS_TEMPLATE_FILE)
		self.engine = fife.Engine()
		self.engine_settings = self.engine.getSettings()

		self.init_logging()
		self.load_settings()

		self.pychan = pychan

		self.quit_requested = False
		self.break_requested = False
		self.return_values = None
		self._got_inited = False

	def load_settings(self):
		"""
		Load the settings from a python file and load them into the engine.
		Called in the ApplicationBase constructor.
		"""
		import os
		# get finalSetting (from the xml file, or if absent the default value)
		self._finalSetting = self._setting.get_module_settings("FIFE")

		self.engine_settings = self.engine.getSettings()

		# Font settings - new FontManager API (FIFE 0.5+)
		# Font paths must be set BEFORE engine.init() for FilesystemAssetProvider
		font_paths = self._finalSetting.get('FontPaths', ['content/fonts'])
		# Convert to absolute paths for reliable font loading
		font_paths = [os.path.abspath(p) for p in font_paths]
		self.engine_settings.setFontPaths(font_paths)

		self.engine_settings.setBitsPerPixel(self._finalSetting['BitsPerPixel'])
		self.engine_settings.setInitialVolume(self._finalSetting['InitialVolume'])
		self.engine_settings.setSDLRemoveFakeAlpha(self._finalSetting['SDLRemoveFakeAlpha'])
		self.engine_settings.setGLCompressImages(self._finalSetting['GLCompressImages'])
		self.engine_settings.setGLUseFramebuffer(self._finalSetting['GLUseFramebuffer'])
		self.engine_settings.setGLUseNPOT(self._finalSetting['GLUseNPOT'])

		# introduced in fife 0.4.0
		self.engine_settings.setGLUseMonochrome(self._finalSetting['GLUseMonochrome'])
		self.engine_settings.setGLUseMipmapping(self._finalSetting['GLUseMipmapping'])
		if self._finalSetting['GLTextureFiltering'] == 'None':
			self.engine_settings.setGLTextureFiltering(fife.TEXTURE_FILTER_NONE)
		elif self._finalSetting['GLTextureFiltering'] == 'Bilinear':
			self.engine_settings.setGLTextureFiltering(fife.TEXTURE_FILTER_BILINEAR)
		elif self._finalSetting['GLTextureFiltering'] == 'Trilinear':
			self.engine_settings.setGLTextureFiltering(fife.TEXTURE_FILTER_TRILINEAR)
		elif self._finalSetting['GLTextureFiltering'] == 'Anisotropic':
			self.engine_settings.setGLTextureFiltering(fife.TEXTURE_FILTER_ANISOTROPIC)
		self.engine_settings.setGLUseDepthBuffer(self._finalSetting['GLUseDepthBuffer'])
		self.engine_settings.setGLAlphaTestValue(self._finalSetting['GLAlphaTestValue'])

		(width, height) = self._finalSetting['ScreenResolution'].split('x')
		self.engine_settings.setScreenWidth(int(width))
		self.engine_settings.setScreenHeight(int(height))
		self.engine_settings.setRenderBackend(self._finalSetting['RenderBackend'])
		self.engine_settings.setFullScreen(self._finalSetting['FullScreen'])
		self.engine_settings.setLightingModel(self._finalSetting['Lighting'])

		try:
			self.engine_settings.setColorKeyEnabled(self._finalSetting['ColorKeyEnabled'])
		except:
			pass

		try:
			self.engine_settings.setColorKey(
				self._finalSetting['ColorKey'][0],
				self._finalSetting['ColorKey'][1],
				self._finalSetting['ColorKey'][2])
		except:
			pass

		try:
			self.engine_settings.setWindowTitle(self._finalSetting['WindowTitle'])
			self.engine_settings.setWindowIcon(self._finalSetting['WindowIcon'])
		except:
			pass

		try:
			self.engine_settings.setFrameLimitEnabled(self._finalSetting['FrameLimitEnabled'])
			self.engine_settings.setFrameLimit(self._finalSetting['FrameLimit'])
		except:
			pass

		try:
			self.engine_settings.setMouseSensitivity(self._finalSetting['MouseSensitivity'])
		except:
			pass

		try:
			self.engine_settings.setMouseAccelerationEnabled(self._finalSetting['MouseAcceleration'])
		except:
			pass

	def init_logging(self):
		"""Initialize the LogManager."""

		# If desired, log to the console and/or the log file.
		log_to_prompt = self._setting.get(SETTINGS.FIFE_MODULE, "LogToPrompt", False)
		log_to_file = self._setting.get(SETTINGS.FIFE_MODULE, "LogToFile", False)
		self._log = fifelog.LogManager(self.engine, log_to_prompt, log_to_file)

		log_level = self._setting.get(SETTINGS.FIFE_MODULE, "LogLevelFilter",
		                              fife.LogManager.LEVEL_DEBUG)
		self._log.setLevelFilter(log_level)

		logmodules = self._setting.get(SETTINGS.FIFE_MODULE, "LogModules", ["controller"])
		if logmodules:
			self._log.setVisibleModules(*logmodules)

	def init(self):
		"""Second initialization stage of engine"""
		self.engine.init()

		# Load font manifest for FontManager (FIFE 0.5+)
		self._load_font_manifest()

		# Initialize ExtScheduler early so sound module can use it
		from horizons.extscheduler import ExtScheduler
		ExtScheduler.create_instance(self.pump)

		# Init stuff.
		self.eventmanager = self.engine.getEventManager()
		self.sound = Sound(self)
		self.imagemanager = self.engine.getImageManager()
		self.animationmanager = self.engine.getAnimationManager()
		self.targetrenderer = self.engine.getTargetRenderer()
		self.animationloader = None

		# Set game cursor.
		self.cursor = self.engine.getCursor()
		cursor_images = {
			'default':   'content/gui/images/cursors/cursor.png',
			'tearing':   'content/gui/images/cursors/cursor_tear.png',
			'attacking': 'content/gui/images/cursors/cursor_attack.png',
			'pipette':   'content/gui/images/cursors/cursor_pipette.png',
			'rename':    'content/gui/images/cursors/cursor_rename.png',
		}
		self.cursor_images = {k: self.imagemanager.load(v) for k, v in cursor_images.items()}
		self.cursor.set(self.cursor_images['default'])

		# Init pychan.
		# Enabling pychan's debug mode may have performance impacts.
		# Because of this, the default PychanDebug value is False.
		debug_pychan = self.get_fife_setting('PychanDebug')
		self.pychan.init(self.engine, debug_pychan)

		init_pychan()
		self._setting.apply()

		self._got_inited = True

	def _load_font_manifest(self):
		"""Load font manifest for FontManager (FIFE 0.5+)."""
		import os
		# Get font directory for absolute paths in manifest
		font_dirs = self.engine_settings.getFontPaths()
		if not font_dirs:
			font_dirs = [os.path.abspath('content/fonts')]

		# Use first font directory for manifest paths
		font_dir = font_dirs[0] if font_dirs else os.path.abspath('content/fonts')

		# Get default font ID from settings
		default_font_id = self._finalSetting.get('DefaultFontId', 'LinLibertine')

		# Build comprehensive font manifest with absolute paths
		# Includes base LinLibertine family + all UH named fonts
		# NOTE: FontDefinitionLoader uses family/weight as ID, so each face needs unique weight
		# We use weight variations for style variants (italic/bold) due to loader limitation
		manifest_lines = [
			'<?xml version="1.0"?>',
			'<fonts version="1">',
			# Base LinLibertine family for engine default font
			f'  <family id="{default_font_id}">',
			f'    <face weight="400">{os.path.join(font_dir, "LinLibertine.ttf")}</face>',
			f'    <face weight="700">{os.path.join(font_dir, "LinLibertineB.ttf")}</face>',
			f'    <face weight="500" italic="true">{os.path.join(font_dir, "LinLibertineI.ttf")}</face>',
			f'    <face weight="600" italic="true">{os.path.join(font_dir, "LinLibertineBI.ttf")}</face>',
			f'    <face weight="300" style="caps">{os.path.join(font_dir, "LinLibertineC.ttf")}</face>',
			'  </family>',
			# UH named fonts (from libertine.xml) - each as separate family
			# pickbelt: bold, size 13
			f'  <family id="pickbelt">',
			f'    <face weight="700" size="13">{os.path.join(font_dir, "LinLibertineB.ttf")}</face>',
			'  </family>',
			# default: italic, size 15
			f'  <family id="default">',
			f'    <face weight="500" style="italic" size="15">{os.path.join(font_dir, "LinLibertineI.ttf")}</face>',
			'  </family>',
			# default_bold: bold italic, size 15
			f'  <family id="default_bold">',
			f'    <face weight="600" style="italic" size="15">{os.path.join(font_dir, "LinLibertineBI.ttf")}</face>',
			'  </family>',
			# default_load: bold italic, size 15, different color (handled by widget)
			f'  <family id="default_load">',
			f'    <face weight="600" style="italic" size="15">{os.path.join(font_dir, "LinLibertineBI.ttf")}</face>',
			'  </family>',
			# message: bold, size 15
			f'  <family id="message">',
			f'    <face weight="700" size="15">{os.path.join(font_dir, "LinLibertineB.ttf")}</face>',
			'  </family>',
			# resourcebar: bold italic, size 16
			f'  <family id="resourcebar">',
			f'    <face weight="600" style="italic" size="16">{os.path.join(font_dir, "LinLibertineBI.ttf")}</face>',
			'  </family>',
			# unifont: regular, size 16
			f'  <family id="unifont">',
			f'    <face weight="400" size="16">{os.path.join(font_dir, "Unifont.ttf")}</face>',
			'  </family>',
			# headline: caps, size 18
			f'  <family id="headline">',
			f'    <face weight="400" style="caps" size="18">{os.path.join(font_dir, "LinLibertineC.ttf")}</face>',
			'  </family>',
			# headline_light: caps, size 18, different color
			f'  <family id="headline_light">',
			f'    <face weight="400" style="caps" size="18">{os.path.join(font_dir, "LinLibertineC.ttf")}</face>',
			'  </family>',
			# mainmenu: bold italic, size 22
			f'  <family id="mainmenu">',
			f'    <face weight="600" style="italic" size="22">{os.path.join(font_dir, "LinLibertineBI.ttf")}</face>',
			'  </family>',
			# large_load: bold italic, size 34
			f'  <family id="large_load">',
			f'    <face weight="600" style="italic" size="34">{os.path.join(font_dir, "LinLibertineBI.ttf")}</face>',
			'  </family>',
			'</fonts>'
		]
		manifest = '\n'.join(manifest_lines)

		try:
			self.engine.loadFontManifestFromString(manifest)
			self.log.info(f"Loaded font manifest with {len(manifest_lines)} lines")
		except Exception as e:
			self.log.warning(f"Failed to load font manifest: {e}")

	def init_animation_loader(self, use_atlases):
		# this method should not be called from init to catch any bugs caused by the loader changing after it.
		self.use_atlases = use_atlases
		if self.use_atlases:
			self.animationloader = SQLiteAtlasLoader()
		else:
			self.animationloader = SQLiteAnimationLoader()

	def set_cursor_image(self, which="default"):
		"""Sets a certain cursor image.
		See definition of cursor_images for reference."""
		self.cursor.set(self.cursor_images[which])

	def get_fife_setting(self, settingname):
		return self._setting.get(SETTINGS.FIFE_MODULE, settingname)

	def set_fife_setting(self, settingname, value):
		"""Probably saves setting in memory. Call save_settings() later"""
		return self._setting.set(SETTINGS.FIFE_MODULE, settingname, value)

	def get_uh_setting(self, settingname):
		return self._setting.get(SETTINGS.UH_MODULE, settingname)

	def set_uh_setting(self, settingname, value):
		"""Probably saves setting in memory. Call save_settings() later"""
		self._setting.set(SETTINGS.UH_MODULE, settingname, value)

	def get_hotkey_settings(self):
		return self._setting.get_module_settings(SETTINGS.KEY_MODULE)

	def get_keys_for_action(self, action, default=False):
		"""Returns list of current hotkeys for *action* or its default hotkeys."""
		if default:
			keys = self._setting.get_module_template_settings(SETTINGS.KEY_MODULE).get(action)
		else:
			keys = self._setting.get(SETTINGS.KEY_MODULE, action)
		return keys

	def set_key_for_action(self, action, newkey):
		"""Replaces all existing hotkeys for *action* with *newkey*."""
		self._setting.set(SETTINGS.KEY_MODULE, action, newkey)

	def add_key_for_action(self, action, addkey):
		"""Adds hotkey *addkey* to list of hotkeys for action *action*."""
		old_keys = self._setting.get(SETTINGS.KEY_MODULE, action, [])
		new_keys = set(old_keys + [addkey])
		self.set_key_for_action(action, list(new_keys))

	def remove_key_for_action(self, action, remkey):
		"""Removes hotkey *remkey* from list of hotkeys for action *action*."""
		old_keys = self._setting.get(SETTINGS.KEY_MODULE, action, [])
		if remkey in old_keys:
				old_keys.remove(remkey)
		if not old_keys:
				print('Cannot have no binding for action')
				return
		self.set_key_for_action(action, old_keys)

	def replace_key_for_action(self, action, oldkey, newkey):
		"""Replaces key *oldkey* with key *newkey* for action *action*"""
		old_keys = self._setting.get(SETTINGS.KEY_MODULE, action, [])
		if oldkey not in old_keys:
			return
		index = old_keys.index(oldkey)
		old_keys[index] = newkey
		self.set_key_for_action(action, old_keys)

	def save_settings(self):
		self._setting.save()

	def play_sound(self, emitter, soundfile):
		"""Plays a soundfile on the given emitter.
		@param emitter: string with the emitters name in horizons.globals.fife.sound.emitter that is to play the  sound
		@param soundfile: string containing the path to the soundfile"""
		self.sound.play_sound(emitter, soundfile)

	def get_locale(self):
		langname = self.get_uh_setting('Language')
		locale_code = LANGUAGENAMES.get_by_value(langname)
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
		assert self._got_inited

		self.engine.initializePumping()
		self.loop()
		self.engine.finalizePumping()
		self.__kill_engine()

	def loop(self):
		while not self.quit_requested:
			try:
				self.engine.pump()
			except RuntimeError:
				import sys
				print("Unknown Horizons exited uncleanly via SIGINT")
				self._log.log_warn("Unknown Horizons exited uncleanly via SIGINT")
				sys.exit(1)
			except fife.Exception as e:
				print(e.getMessage())
				break
			for f in self.pump:
				f()
			if self.break_requested:
				self.break_requested = False
				return self.return_values

	def __kill_engine(self):
		"""Called when the engine is quit"""
		# A hack to get the system cursor back:
		self.cursor.set(fife.CURSOR_NATIVE)
		self.engine.destroy()

	def breakLoop(self, returnValue=None):
		self.return_values = returnValue
		self.break_requested = True

	def quit(self):
		"""Quits the engine."""
		self.quit_requested = True

	@classmethod
	def getVersion(cls):
		"""Returns a tuple (Major, Minor, Patch) version of the current running Fife."""
		try:
			return (fife.getMajor(), fife.getMinor(), fife.getPatch())
		except AttributeError:
			return (0, 0, 0)
