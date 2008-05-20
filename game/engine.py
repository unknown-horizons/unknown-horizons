# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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
import gui.style
import main

class Fife:
	def __init__(self):
		self.engine = fife.Engine()
		self.settings = self.engine.getSettings()
		self.pychan = pychan

		self._doQuit = False
		self._doBreak = False
		self._doReturn = None
		self._gotInited = False

		#init settings
		main.instance.settings.addCategorys('fife')
		main.instance.settings.fife.addChangeListener(self._setSetting)
		main.instance.settings.fife.addCategorys('defaultFont', 'sound', 'renderer', 'screen')

		main.instance.settings.fife.defaultFont.setDefaults(
			path = 'content/gfx/fonts/samanata.ttf',
			size = 12,
			glyphs = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?-+/():;%&`'*#=[]\"",
		)

		main.instance.settings.fife.sound.setDefaults(
			initialVolume = 5.0,
		)

		main.instance.settings.fife.renderer.setDefaults(
			backend = 'OpenGL',
			SDLRemoveFakeAlpha = False,
			imageChunkingSize = 256,
		)

		main.instance.settings.fife.screen.setDefaults(
			fullscreen = False,
			width = 1024,
			height = 768,
			bpp = 0
		)

	def _setSetting(self, settingObject, settingName, value):
		setting = settingObject._name + settingName
		print setting, '=', value
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

	def init(self):
		logToPrompt, logToFile, debugPychan = True, True, False
		if self._gotInited:
			return
		#start modules
		self.log = fifelog.LogManager(self.engine, 1 if logToPrompt else 0, 1 if logToFile else 0)
		self.log.setVisibleModules('controller')

		self.engine.init()

		#init sound and background emitter
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		self.bgsound = self.soundmanager.createEmitter()
		self.bgsound.setSoundClip(self.engine.getSoundClipPool().addResourceFromFile('content/audio/music/music.ogg'))
		self.bgsound.setLooping(True)

		#init pychan
		self.pychan.init(self.engine, debugPychan)
		self.pychan.setupModalExecution(self.loop, self.breakLoop)
		for name, stylepart in gui.style.STYLES.items():
			self.pychan.manager.addStyle(name, stylepart)
		self.pychan.loadFonts("content/fonts/samanata.fontdef")

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
