# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import fife
import fifelog
import pychan
import game.gui.style
import game.main
import new
import glob, random
from game.util.inventory_widget import Inventory, ImageFillStatusButton

class SQLiteAnimationLoader(fife.ResourceLoader):
	"""Loads animations from a SQLite database.
	"""
	def __init__(self):
		super(SQLiteAnimationLoader, self).__init__()
		self.thisown = 0

	def loadResource(self, location):
		"""
		@param location:
		"""
		commands = location.getFilename().split(':')
		id = commands.pop(0)
		if ',' in id:
			id, shift_x, shift_y = id.split(',')
		else:
			shift_x, shift_y = None, None
		commands = zip(commands[0::2], commands[1::2])
		print "Loading animation #%s..." % (id)
		ani = fife.Animation()
		frame_start, frame_end = 0.0, 0.0
		for file,frame_end in game.main.db("SELECT file, frame_end from data.animation where animation_id = ?", id):
			img = game.main.fife.imagepool.getImage(game.main.fife.imagepool.addResourceFromFile(file))
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

					img = game.main.fife.imagepool.getImage(game.main.fife.imagepool.addResourceFromLocation(loc))
			ani.addFrame(img, max(1,int((float(frame_end) - frame_start)*1000)))
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
		game.main.settings.addCategorys('fife')
		game.main.settings.fife.addChangeListener(self._setSetting)
		game.main.settings.fife.addCategorys('defaultFont', 'sound', 'renderer', 'screen')

		game.main.settings.fife.defaultFont.setDefaults(
			path = 'content/gfx/fonts/Essays1743-Italic.ttf',
			size = 18,
			glyphs = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?-+/():;%&`'*#=[]\"",
		)

		game.main.settings.fife.sound.setDefaults(
			initialVolume = 5.0,
		)

		game.main.settings.fife.renderer.setDefaults(
			backend = 'OpenGL',
			SDLRemoveFakeAlpha = False,
			imageChunkingSize = 256,
		)

		game.main.settings.fife.screen.setDefaults(
			fullscreen = False,
			width = 1024,
			height = 768,
			bpp = 0,
			title = 'OpenAnno',
			icon = 'content/gui/images/icon.png'
		)

	def _setSetting(self, settingObject, settingName, value):
		"""
		@param settingObject:
		@param settingName:
		@param value:
		"""
		setting = settingObject._name + settingName
		if setting == 'fife_defaultFont_path':
			self.settings.setDefaultFontPath(value)
		elif setting == 'fife_defaultFont_size':
			self.settings.setDefaultFontSize(value)
		elif setting == 'fife_defaultFont_glyphs':
			self.settings.setDefaultFontGlyphs(value)
		elif setting == 'fife_screen_fullscreen':
			self.settings.setFullScreen(1 if value else 0)
		elif setting == 'fife_screen_width':
			self.settings.setScreenWidth(value)
		elif setting == 'fife_screen_height':
			self.settings.setScreenHeight(value)
		elif setting == 'fife_screen_bpp':
			self.settings.setBitsPerPixel(1 if value else 0)
		elif setting == 'fife_renderer_backend':
			self.settings.setRenderBackend(value)
		elif setting == 'fife_renderer_SDLRemoveFakeAlpha':
			self.settings.setSDLRemoveFakeAlpha(value)
		elif setting == 'fife_renderer_imageChunkingSize':
			self.settings.setImageChunkingSize(value)
		elif setting == 'fife_sound_initialVolume':
			self.settings.setInitialVolume(value)
		elif setting == 'fife_screen_title':
			self.settings.setWindowTitle(value)
		elif setting == 'fife_screen_icon':
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
		self.music = glob.glob('content/audio/music/*.ogg')

		#init stuff
		self.eventmanager = self.engine.getEventManager()
		self.eventmanager.setNonConsumableKeys([fife.Key.ESCAPE, fife.Key.F10])
		self.guimanager = self.engine.getGuiManager()
		self.console = self.guimanager.getConsole()
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		if game.main.settings.sound.enabled:
			self.bgsound = self.soundmanager.createEmitter()
			self.bgsound.setLooping(False)
			self.music_rand_element = random.randint(0, len(self.music) - 1)
			self.bgsound.setSoundClip(self.engine.getSoundClipPool().addResourceFromFile(self.music[self.music_rand_element]))
			self.bgsound.play()
			def check_music():
				if hasattr(self, '_bgsound_old_byte_pos') and hasattr(self, '_bgsound_old_sample_pos'):
					if self._bgsound_old_byte_pos == game.main.fife.bgsound.getCursor(fife.SD_BYTE_POS) and self._bgsound_old_sample_pos == game.main.fife.bgsound.getCursor(fife.SD_SAMPLE_POS):
						self.music_rand_element = self.music_rand_element + 1 if self.music_rand_element + 1 < len(self.music) else 0
						self.bgsound.reset()
						self.bgsound.setSoundClip(self.engine.getSoundClipPool().addResourceFromFile(self.music[self.music_rand_element]))
						self.bgsound.play()
				self._bgsound_old_byte_pos, self._bgsound_old_sample_pos = game.main.fife.bgsound.getCursor(fife.SD_BYTE_POS), game.main.fife.bgsound.getCursor(fife.SD_SAMPLE_POS)
			game.main.ext_scheduler.add_new_object(check_music, self, loops=-1)
		self.imagepool = self.engine.getImagePool()
		self.animationpool = self.engine.getAnimationPool()
		self.animationloader = SQLiteAnimationLoader()
		self.animationpool.addResourceLoader(self.animationloader)

		#init pychan
		self.pychan.init(self.engine, debugPychan)
		self.pychan.setupModalExecution(self.loop, self.breakLoop)
		for name, stylepart in game.gui.style.STYLES.items():
			self.pychan.manager.addStyle(name, stylepart)
		self.pychan.loadFonts("content/fonts/Essays1743-Italic.fontdef")
		pychan.widgets.registerWidget(Inventory)
		pychan.widgets.registerWidget(ImageFillStatusButton)

		self._gotInited = True

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
