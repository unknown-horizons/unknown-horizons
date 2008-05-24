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
from game.settings import Settings
from game.session import Game
from game.gui.mainlistener import MainListener

def start():
	global db, settings, fife, mainmenu, gamemenu, gui, game
	#init db
	db = DbReader(':memory:')
	db.query("attach ? AS data", ('content/openanno.sqlite'))

	#init settings
	settings = Settings()
	settings.addCategorys('sound')
	settings.sound.setDefaults(enabled = True)

	#init fife
	fife = Fife()
	fife.init()

	if settings.sound.enabled:
		fife.bgsound.play()

	mainmenu = fife.pychan.loadXML('content/gui/mainmenu.xml')
	mainmenu.stylize('menu')
	gamemenu = fife.pychan.loadXML('content/gui/gamemenu.xml')
	gamemenu.stylize('menu')

	eventMap = {
		'startGame'    : startGame,
		'settingsLink' : showSettings,
		'creditsLink'  : showCredits,
		'closeButton'  : showQuit,
	}
	mainmenu.mapEvents(eventMap)
	gamemenu.mapEvents(eventMap)

	mainlistener = MainListener()

	gui = mainmenu
	gui.show()

	game = None

	fife.run()

def showCredits():
	global fife
	fife.pychan.loadXML('content/gui/credits.xml').execute({ 'okButton' : True })

def showSettings():
	global fife, settings
	resolutions = ["640x480", "800x600", "1024x768", "1440x900"];
	try:
		resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))
	except:
		resolutions.append(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))
	dlg = fife.pychan.loadXML('content/gui/settings.xml')
	dlg.distributeInitialData({
		'screen_resolution' : resolutions,
		'screen_renderer' : ["OpenGL", "SDL"],
		'screen_bpp' : ["Desktop", "16", "24", "32"]
	})
	dlg.distributeData({
		'screen_resolution' : resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)),
		'screen_renderer' : 0 if settings.fife.renderer.backend == 'OpenGL' else 1,
		'screen_bpp' : int(settings.fife.screen.bpp / 10), # 0:0 16:1 24:2 32:3 :)
		'screen_fullscreen' : settings.fife.screen.fullscreen,
		'sound_enable_opt' : settings.sound.enabled
	})
	if(not dlg.execute({ 'okButton' : True, 'cancelButton' : False })):
		return;
	screen_resolution, screen_renderer, screen_bpp, screen_fullscreen, sound_enable_opt = dlg.collectData('screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt')
	changes_require_restart = False
	if screen_fullscreen != settings.fife.screen.fullscreen:
		settings.fife.screen.fullscreen = screen_fullscreen
		changes_require_restart = True
	if sound_enable_opt != settings.sound.enabled:
		settings.sound.enabled = sound_enable_opt
		changes_require_restart = True
	if screen_bpp != int(settings.fife.screen.bpp / 10):
		settings.fife.screen.bpp = 0 if screen_bpp == 0 else ((screen_bpp + 1) * 8)
		changes_require_restart = True
	if screen_renderer != (0 if settings.fife.renderer.backend == 'OpenGL' else 1):
		settings.fife.renderer.backend = 'OpenGL' if screen_renderer == 0 else 'SDL'
		changes_require_restart = True
	if screen_resolution != resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)):
		settings.fife.screen.width = int(resolutions[screen_resolution].partition('x')[0])
		settings.fife.screen.height = int(resolutions[screen_resolution].partition('x')[2])
		changes_require_restart = True
	if changes_require_restart:
		fife.pychan.loadXML('content/gui/changes_require_restart.xml').execute({ 'okButton' : True})

def showQuit():
	global game, fife, gui
	if game is None:
		if(fife.pychan.loadXML('content/gui/quitgame.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
			fife.quit()
	else:
		if(fife.pychan.loadXML('content/gui/quitsession.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
			game = None
			gui.hide()
			gui = mainmenu
			gui.show()

def startGame():
	global gui, game
	gui.hide()
	gui = gamemenu
	if game is None:
		game = Game()
		game.init()
		game.loadmap("content/maps/demo.sqlite")
