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

class Main:
	"""OpenAnno class, main game class. Creates the base."""
	def __init__(self):
		#init db
		self.db = DbReader(':memory:')
		self.db.query("attach ? AS data", ('content/openanno.sqlite'))

		#load fife
		self.fife = Fife()

		#init config
		configFile = './openanno-config.sqlite'
		if not os.path.exists(configFile):
			shutil.copyfile('content/config.sqlite', configFile)
		self.db.query("attach ? AS config", (configFile))
		self.sound_enable = True
		for (name, value) in self.db.query("select name, value from config.config where ((name in ('screen_full', 'sound_enable') and value in ('0', '1')) or (name in ('screen_width', 'screen_height') and value regexp '^[0-9]+$') or (name = 'screen_bpp' and value in ('0', '16', '24', '32')) or (name = 'screen_renderer' and value in ('SDL', 'OpenGL')) or (name = 'sound_volume' and value regexp '^[0-9]+([.][0-9]+)?$'))").rows:
			if name == 'sound_enable':
				self.sound_enable = (value == '1')
			if name == 'screen_full':
				self.fife.settings.setFullScreen(int(value))
			if name == 'screen_width':
				self.fife.settings.setScreenWidth(int(value))
			if name == 'screen_height':
				self.fife.settings.setScreenHeight(int(value))
			if name == 'screen_bpp':
				self.fife.settings.setBitsPerPixel(int(value))
			if name == 'screen_renderer':
				self.fife.settings.setRenderBackend(str(value))

		#init fife
		self.fife.init()

 		if self.sound_enable:
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
			resolutions.index(str(self.fife.settings.getScreenWidth()) + 'x' + str(self.fife.settings.gerScreenHeight()))
		except:
			resolutions.append(str(self.fife.settings.getScreenWidth()) + 'x' + str(self.fife.settings.getScreenHeight()))
		dlg = self.fife.pychan.loadXML('content/gui/settings.xml')
		dlg.distributeInitialData({
			'screen_resolution' : resolutions,
			'screen_renderer' : ["OpenGL", "SDL"],
			'screen_bpp' : ["Desktop", "16", "24", "32"]
		})
		dlg.distributeData({
			'screen_resolution' : resolutions.index(str(self.fife.settings.getScreenWidth()) + 'x' + str(self.fife.settings.getScreenHeight())),
			'screen_renderer' : 0 if self.fife.settings.getRenderBackend() == 'OpenGL' else 1,
			'screen_bpp' : int(self.fife.settings.getBitsPerPixel() / 10), # 0:0 16:1 24:2 32:3 :)
			'screen_fullscreen' : self.fife.settings.isFullScreen() == 1,
			'sound_enable_opt' : self.sound_enable == 1
		})
		if(not dlg.execute({ 'okButton' : True, 'cancelButton' : False })):
			return;
		screen_resolution, screen_renderer, screen_bpp, screen_fullscreen, sound_enable_opt = dlg.collectData('screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt')
		changes_require_restart = False
		if screen_fullscreen != (self.fife.settings.isFullScreen() == 1):
			self.fife.settings.setFullScreen(1 if screen_fullscreen else 0)
			self.db.query("REPLACE INTO config.config (name, value) VALUES (?, ?)", ('screen_full', 1 if screen_fullscreen else 0));
			changes_require_restart = True
		if sound_enable_opt != (self.sound_enable == 1):
			self.sound_enable = (1 if sound_enable_opt else 0)
			self.db.query("REPLACE INTO config.config (name, value) VALUES (?, ?)", ('sound_enable', self.sound_enable));
			changes_require_restart = True
		if screen_bpp != int(self.fife.settings.getBitsPerPixel() / 10):
			self.fife.settings.setBitsPerPixel(0 if screen_bpp == 0 else ((screen_bpp + 1) * 8))
			self.db.query("REPLACE INTO config.config (name, value) VALUES (?, ?)", ('screen_bpp', self.fife.settings.getBitsPerPixel()));
			changes_require_restart = True
		if screen_renderer != (0 if self.fife.settings.getRenderBackend() == 'OpenGL' else 1):
			self.fife.settings.RenderBackend = 'OpenGL' if screen_renderer == 0 else 'SDL'
			self.db.query("REPLACE INTO config.config (name, value) VALUES (?, ?)", ('screen_renderer', self.fife.settings.getRenderBackend()));
			changes_require_restart = True
		if screen_resolution != resolutions.index(str(self.fife.settings.getScreenWidth()) + 'x' + str(self.fife.settings.getScreenHeight())):
			self.fife.settings.setScreenWidth(int(resolutions[screen_resolution].partition('x')[0]))
			self.fife.settings.setScreenHeight(int(resolutions[screen_resolution].partition('x')[2]))
			self.db.query("REPLACE INTO config.config (name, value) VALUES (?, ?)", ('screen_width', self.fife.settings.getScreenWidth()));
			self.db.query("REPLACE INTO config.config (name, value) VALUES (?, ?)", ('screen_height', self.fife.settings.getScreenHeight()));
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