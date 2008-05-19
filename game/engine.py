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

class Fife:
	def __init__(self):
		self.engine = fife.Engine()
		self.settings = self.engine.getSettings()
		self.pychan = pychan

		self._doQuit = False
		self._doBreak = False
		self._doReturn = None
		self._gotInited = False

		#font
		self.settings.setDefaultFontPath('content/gfx/fonts/samanata.ttf')
		self.settings.setDefaultFontSize(12)
		self.settings.setDefaultFontGlyphs(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?-+/():;%&`'*#=[]\"")

		#sound
		self.settings.setInitialVolume(5.0)

		#render
		self.settings.setRenderBackend('OpenGL')
		self.settings.setSDLRemoveFakeAlpha(0)
		try:
			self.settings.setImageChunkingSize(256)
		except:
			pass

		#screen
		self.settings.setFullScreen(0)
		self.settings.setScreenWidth(1024)
		self.settings.setScreenHeight(768)
		self.settings.setBitsPerPixel(0)

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
