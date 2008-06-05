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

class SQLiteAnimationLoader(fife.AnimationLoader):
	def __init__(self):
		fife.AnimationLoader.__init__(self)
		self.thisown = 0

	def loadResource(self, location):
		print "Loading animation:", location.getFilename()
		ani = fife.Animation()
		ani.setActionFrame(0)
		for (file,) in game.main.db("SELECT file from data.animation where animation_id = ?", location.getFilename()):
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			img = game.main.fife.imagepool.getImage(img)
			img.setXShift(0)
			img.setYShift(0)
			ani.addFrame(img, 1)
		ani.thisown = 0
		return ani

class Fife(object):
	def __init__(self):
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
			bpp = 0
		)

	def _setSetting(self, settingObject, settingName, value):
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
			self.settings.setRenderBackend(str(value))
		elif setting == 'fife_renderer_SDLRemoveFakeAlpha':
			self.settings.setSDLRemoveFakeAlpha(value)
		elif setting == 'fife_renderer_imageChunkingSize':
			self.settings.setImageChunkingSize(value)
		elif setting == 'fife_sound_initialVolume':
			self.settings.setInitialVolume(value)

	def init(self):
		logToPrompt, logToFile, debugPychan = True, True, True
		if self._gotInited:
			return
		#start modules
		self.log = fifelog.LogManager(self.engine, 1 if logToPrompt else 0, 1 if logToFile else 0)
		self.log.setVisibleModules('controller')

		self.engine.init()

		#init stuff
		self.eventmanager = self.engine.getEventManager()
		self.eventmanager.setNonConsumableKeys([fife.Key.ESCAPE, fife.Key.F10])
		self.guimanager = self.engine.getGuiManager()
		self.console = self.guimanager.getConsole()
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		self.bgsound = self.soundmanager.createEmitter()
		self.bgsound.setSoundClip(self.engine.getSoundClipPool().addResourceFromFile('content/audio/music/music.ogg'))
		self.bgsound.setLooping(True)
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

		self._gotInited = True

	def run(self):
		self.init()
		self.engine.initializePumping()
		self.loop()
		self.engine.finalizePumping()

	def loop(self):
		while not self._doQuit:
			try:
				self.engine.pump()
			except fife.Exception, e:
				print e.getMessage()
				break
			self.pump()
			if self._doBreak:
				self._doBreak = False
				return self._doReturn

	def pump(self):
		pass

	def breakLoop(self, returnValue = None):
		self._doReturn = returnValue
		self._doBreak = True

	def quit(self):
		self._doQuit = True
