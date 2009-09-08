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

import fife
import fifelog
import pychan

import gui.style
import horizons.main

from horizons.util import ActionSetLoader
from gui.widgets.inventory import Inventory, ImageFillStatusButton
from gui.widgets.progressbar import ProgressBar
from gui.widgets.toggleimagebutton import ToggleImageButton
from gui.widgets.tooltip import TooltipIcon, TooltipButton
from horizons.extscheduler import ExtScheduler

class SQLiteAnimationLoader(fife.ResourceLoader):
	"""Loads animations from a SQLite database.
	"""
	def __init__(self):
		super(SQLiteAnimationLoader, self).__init__()
		self.thisown = 0

	def loadResource(self, location):
		"""
		@param location: String with the location. See below for details:
		Location format: <animation_id>:<command>:<params> (e.g.: "123:shift:left-16, bottom-8)
		Available commands:
		- shift:
		Shift the image using the params left, right, center, middle for x shifting and
		y-shifting with the params: top, bottom, center, middle.
		A param looks like this: "param_x(+/-)value, param_y(+/-)value" (e.g.: left-16, bottom+8)
		- cut:
		#TODO: complete documentation
		"""
		commands = location.getFilename().split(':')
		id = commands.pop(0)
		actionset, action, rotation = id.split('-')
		if ',' in id:
			id, shift_x, shift_y = id.split(',')
		else:
			shift_x, shift_y = None, None
		commands = zip(commands[0::2], commands[1::2])

		ani = fife.Animation()
		frame_start, frame_end = 0.0, 0.0
		for file, frame_end in sorted(ActionSetLoader.get_action_sets()[actionset][action][int(rotation)].iteritems()):
			idx = horizons.main.fife.imagepool.addResourceFromFile(file)
			img = horizons.main.fife.imagepool.getImage(idx)
			for command, arg in commands:
				if command == 'shift':
					x, y = arg.split(',')
					if x.startswith('left'):
						x = int(x[4:]) + int(img.getWidth() / 2)
					elif x.startswith('right'):
						x = int(x[5:]) - int(img.getWidth() / 2)
					elif x.startswith(('center', 'middle')):
						x = int(x[6:])
					else:
						x = int(x)

					if y.startswith('top'):
						y = int(y[3:]) + int(img.getHeight() / 2)
					elif y.startswith('bottom'):
						y = int(y[6:]) - int(img.getHeight() / 2)
					elif y.startswith(('center', 'middle')):
						y = int(y[6:])
					else:
						y = int(y)

					img.setXShift(x)
					img.setYShift(y)
				elif command == 'cut':
					loc = fife.ImageLocation('asdf')
					loc.setParentSource(img)
					x, y, w, h = arg.split(',')

					if x.startswith('left'):
						x = int(x[4:])
					elif x.startswith('right'):
						x = int(x[5:]) + img.getWidth()
					elif x.startswith(('center', 'middle')):
						x = int(x[6:]) + int(img.getWidth() / 2)
					else:
						x = int(x)

					if y.startswith('top'):
						y = int(y[3:])
					elif y.startswith('bottom'):
						y = int(y[6:]) - img.getHeight()
					elif y.startswith(('center', 'middle')):
						y = int(y[6:]) + int(img.getHeight() / 2)
					else:
						y = int(y)

					if w.startswith('left'):
						w = int(w[4:]) - x
					elif w.startswith('right'):
						w = int(w[5:]) + img.getWidth() - x
					elif w.startswith(('center', 'middle')):
						w = int(w[6:]) + int(img.getWidth() / 2) - x
					else:
						w = int(w)

					if h.startswith('top'):
						h = int(h[3:]) - y
					elif h.startswith('bottom'):
						h = int(h[6:]) + img.getHeight() - y
					elif h.startswith(('center', 'middle')):
						h = int(h[6:]) + int(img.getHeight() / 2) - y
					else:
						h = int(h)

					loc.setXShift(x)
					loc.setYShift(y)
					loc.setWidth(w)
					loc.setHeight(h)

					idx = horizons.main.fife.imagepool.addResourceFromLocation(loc)
					#img = horizons.main.fife.imagepool.getImage(idx)
			ani.addFrame(fife.ResourcePtr(horizons.main.fife.imagepool, idx), max(1, int((float(frame_end) - frame_start)*1000)))
			frame_start = float(frame_end)
		ani.setActionFrame(0)
		ani.thisown = 0
		return ani

class Fife(object):
	"""
	"""
	def __init__(self):
		self.pump = []

		self.engine = fife.Engine()
		self.settings = self.engine.getSettings()
		self.pychan = pychan

		self._doQuit = False
		self._doBreak = False
		self._doReturn = None
		self._gotInited = False

		#init settings
		settings = horizons.main.settings
		settings.addCategories('fife')
		settings.fife.add_change_listener(self._setSetting)
		settings.fife.addCategories('defaultFont', 'sound', 'renderer', 'screen')

		settings.fife.defaultFont.setDefaults(
			path = 'content/fonts/LinLibertine_Re-4.4.1.ttf',
			size = 15,
			glyphs = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?-+/():;%&`'*#=[]\""
		)

		settings.fife.sound.setDefaults(
			initialVolume = self.settings.getMaxVolume()
		)

		settings.fife.renderer.setDefaults(
			backend = 'OpenGL',
			SDLRemoveFakeAlpha = False,
			imageChunkingSize = 256
		)

		settings.fife.screen.setDefaults(
			fullscreen = False,
			width = 1024,
			height = 768,
			bpp = 0,
			title = 'Unknown Horizons',
			icon = 'content/gui/images/icon.png'
		)

	def _setSetting(self, settingObject, settingName, value):
		"""
		@param settingObject:
		@param settingName:
		@param value:
		"""
		setting = settingObject._name + settingName
		if setting == 'fife.defaultFont.path':
			self.settings.setDefaultFontPath(value)
		elif setting == 'fife.defaultFont.size':
			self.settings.setDefaultFontSize(value)
		elif setting == 'fife.defaultFont.glyphs':
			self.settings.setDefaultFontGlyphs(value)
		elif setting == 'fife.screen.fullscreen':
			self.settings.setFullScreen(1 if value else 0)
		elif setting == 'fife.screen.width':
			self.settings.setScreenWidth(value)
		elif setting == 'fife.screen.height':
			self.settings.setScreenHeight(value)
		elif setting == 'fife.screen.bpp':
			self.settings.setBitsPerPixel(value)
		elif setting == 'fife.renderer.backend':
			self.settings.setRenderBackend(value)
		elif setting == 'fife.renderer.SDLRemoveFakeAlpha':
			self.settings.setSDLRemoveFakeAlpha(value)
		elif setting == 'fife.renderer.imageChunkingSize':
			self.settings.setImageChunkingSize(value)
		elif setting == 'fife.sound.initialVolume':
			self.settings.setInitialVolume(value)
		elif setting == 'fife.screen.title':
			self.settings.setWindowTitle(value)
		elif setting == 'fife.screen.icon':
			self.settings.setWindowIcon(value)

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
		self.emitter = {}
		if horizons.main.settings.sound.enabled: # Set up sound if it is enabled
			self.soundclippool = self.engine.getSoundClipPool()
			self.emitter['bgsound'] = self.soundmanager.createEmitter()
			self.emitter['bgsound'].setGain(horizons.main.settings.sound.volume_music)
			self.emitter['bgsound'].setLooping(False)
			self.emitter['effects'] = self.soundmanager.createEmitter()
			self.emitter['effects'].setGain(horizons.main.settings.sound.volume_effects)
			self.emitter['effects'].setLooping(False)
			self.emitter['speech'] = self.soundmanager.createEmitter()
			self.emitter['speech'].setGain(horizons.main.settings.sound.volume_effects)
			self.emitter['speech'].setLooping(False)
			self.emitter['ambient'] = []

			self.music_rand_element = random.randint(0, len(self.menu_music) - 1)
			self.initial_menu_music_element = self.music_rand_element

			def check_music():
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


			check_music() # Start background music
			ExtScheduler().add_new_object(check_music, self, loops=-1)
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
		for name, stylepart in horizons.gui.style.STYLES.iteritems():
			self.pychan.manager.addStyle(name, stylepart)
		self.pychan.loadFonts("content/fonts/libertine.fontdef")
		pychan.widgets.registerWidget(Inventory)
		pychan.widgets.registerWidget(ImageFillStatusButton)
		pychan.widgets.registerWidget(ProgressBar)
		pychan.widgets.registerWidget(ToggleImageButton)
		pychan.widgets.registerWidget(TooltipIcon)
		pychan.widgets.registerWidget(TooltipButton)

		self._gotInited = True

	def play_sound(self, emitter, soundfile):
		"""Plays a soundfile on the given emitter.
		@param emitter: string with the emitters name in horizons.main.fife.emitter that is to play the  sound
		@param soundfile: string containing the path to the soundfile"""
		if horizons.main.settings.sound.enabled: # Set up sound if it is enabled
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
		if horizons.main.settings.sound.enabled:
			self.emitter[emitter_name].setGain(value)

	def set_volume_music(self, value):
		"""Sets the volume of the music emitters to 'value'.
		@param value: double - value that's used to set the emitters gain.
		"""
		if horizons.main.settings.sound.enabled:
				self.emitter['bgsound'].setGain(value)


	def set_volume_effects(self, value):
		"""Sets the volume of effects, speech and ambient emitters.
		@param value: double - value that's used to set the emitters gain.
		"""
		if horizons.main.settings.sound.enabled:
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
