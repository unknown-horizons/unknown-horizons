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

import os.path
import shutil
from game.dbreader import DbReader
from game.engine import Fife
from game.session import Game
from game.settings import Settings

class Main:
	"""OpenAnno class, main game class. Creates the base."""
	def init(self):
		#init db
		self.db = DbReader(':memory:')
		self.db.query("attach ? AS data", ('content/openanno.sqlite'))

		#init settings
		self.settings = Settings()
		self.settings.addCategorys('sound')
		self.settings.sound.setDefaults(enabled = True)

		#init fife
		self.fife = Fife()
		self.fife.init()

 		if self.settings.sound.enabled:
			self.fife.bgsound.play()
		
		self.mainmenu = self.fife.pychan.loadXML('content/gui/mainmenu.xml')
		self.mainmenu.stylize('menu')
		self.gamemenu = self.fife.pychan.loadXML('content/gui/gamemenu.xml')
		self.gamemenu.stylize('menu')

		eventMap = {
			'startGame' : self.start_game,
			'settingsLink' : self.showSettings,
			'creditsLink'  : self.showCredits,
			'closeButton'  : self.showQuit,
		}
		self.mainmenu.mapEvents(eventMap)
		self.gamemenu.mapEvents(eventMap)
		self.gui = self.mainmenu
		self.gui.show()
		self.game = None

	def run(self):
		self.fife.run()

	def showCredits(self):
		self.fife.pychan.loadXML('content/gui/credits.xml').execute({ 'okButton' : True })

	def showSettings(self):
		resolutions = ["640x480", "800x600", "1024x768", "1440x900"];
		try:
			resolutions.index(str(self.settings.fife.screen.width) + 'x' + str(self.settings.fife.screen.height))
		except:
			resolutions.append(str(self.settings.fife.screen.width) + 'x' + str(self.settings.fife.screen.height))
		dlg = self.fife.pychan.loadXML('content/gui/settings.xml')
		dlg.distributeInitialData({
			'screen_resolution' : resolutions,
			'screen_renderer' : ["OpenGL", "SDL"],
			'screen_bpp' : ["Desktop", "16", "24", "32"]
		})
		dlg.distributeData({
			'screen_resolution' : resolutions.index(str(self.settings.fife.screen.width) + 'x' + str(self.settings.fife.screen.height)),
			'screen_renderer' : 0 if self.settings.fife.renderer.backend == 'OpenGL' else 1,
			'screen_bpp' : int(self.settings.fife.screen.bpp / 10), # 0:0 16:1 24:2 32:3 :)
			'screen_fullscreen' : self.settings.fife.screen.fullscreen,
			'sound_enable_opt' : self.settings.sound.enabled
		})
		if(not dlg.execute({ 'okButton' : True, 'cancelButton' : False })):
			return;
		screen_resolution, screen_renderer, screen_bpp, screen_fullscreen, sound_enable_opt = dlg.collectData('screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt')
		changes_require_restart = False
		if screen_fullscreen != self.settings.fife.screen.fullscreen:
			self.settings.fife.screen.fullscreen = screen_fullscreen
			changes_require_restart = True
		if sound_enable_opt != self.settings.sound.enabled:
			self.settings.sound.enabled = sound_enable_opt
			changes_require_restart = True
		if screen_bpp != int(self.settings.fife.screen.bpp / 10):
			self.settings.fife.screen.bpp = 0 if screen_bpp == 0 else ((screen_bpp + 1) * 8)
			changes_require_restart = True
		if screen_renderer != (0 if self.settings.fife.renderer.backend == 'OpenGL' else 1):
			self.settings.fife.renderer.backend = 'OpenGL' if screen_renderer == 0 else 'SDL'
			changes_require_restart = True
		if screen_resolution != resolutions.index(str(self.settings.fife.screen.width) + 'x' + str(self.settings.fife.screen.height)):
			self.settings.fife.screen.width = int(resolutions[screen_resolution].partition('x')[0])
			self.settings.fife.screen.height = int(resolutions[screen_resolution].partition('x')[2])
			changes_require_restart = True
		if changes_require_restart:
			self.fife.pychan.loadXML('content/gui/changes_require_restart.xml').execute({ 'okButton' : True})

	def showQuit(self):
		if self.game is None:
			if(self.fife.pychan.loadXML('content/gui/quitgame.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
				self.fife.quit()
		else:
			if(self.fife.pychan.loadXML('content/gui/quitsession.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
				self.game = None
				self.gui.hide()
				self.gui = self.mainmenu
				self.gui.show()

	def start_game(self):
		self.gui.hide()
		self.gui = self.gamemenu
		if self.game is None:
			self.game = Game()
			self.game.init("content/maps/demo.sqlite")

instance = Main()
instance.init()