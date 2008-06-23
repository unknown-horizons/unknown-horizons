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

import os.path
import glob
import shutil
from game.dbreader import DbReader
from game.engine import Fife
from game.settings import Settings
from game.session import Session
from game.gui.mainlistener import MainListener
from game.serverlist import WANServerList, LANServerList, FavoriteServerList

def start():
	global db, settings, fife, gui, session, connection
	#init db
	db = DbReader(':memory:')
	db("attach ? AS data", 'content/openanno.sqlite')

	#init settings
	settings = Settings()
	settings.addCategorys('sound')
	settings.sound.setDefaults(enabled = True)
	settings.addCategorys('network')
	settings.network.setDefaults(port = 62666, url_servers = 'http://master.openanno.org/servers', url_register = 'http://master.openanno.org/register?port=%s', favorites = [])

	#init fife
	fife = Fife()
	fife.init()

	if settings.sound.enabled:
		fife.bgsound.play()

	mainlistener = MainListener()
	connection = None
	session = None
	gui = None

	showMain()

	fife.run()

def onEscape():
	pass

def showCredits():
	global fife
	showDialog(fife.pychan.loadXML('content/gui/credits.xml'), {'okButton' : True}, onPressEscape = True)

def showSettings():
	global fife, settings, onEscape
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
	if not showDialog(dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		return
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
		showDialog(fife.pychan.loadXML('content/gui/changes_require_restart.xml'), {'okButton' : True}, onPressEscape = True)

def showDialog(dlg, actions, onPressEscape = None):
	global onEscape
	if onPressEscape != None:
		def _escape():
			fife.pychan.get_manager().breakFromMainLoop(onPressEscape)
			dlg.hide()
		tmp_escape = onEscape
		onEscape = _escape
	ret = dlg.execute(actions)
	if onPressEscape != None:
		onEscape = tmp_escape
	return ret

def showQuit():
	global fife
	if showDialog(fife.pychan.loadXML('content/gui/quitgame.xml'), {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		fife.quit()

def showMain():
	global gui, onEscape, showQuit, showSingle, showMulti, showSettings, showCredits
	if gui != None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/mainmenu.xml')
	gui.stylize('menu')
	eventMap = {
		'startSingle'  : showSingle,
		'startMulti'   : showMulti,
		'settingsLink' : showSettings,
		'creditsLink'  : showCredits,
		'closeButton'  : showQuit,
	}
	gui.mapEvents(eventMap)
	gui.show()
	onEscape = showQuit

def showSingle(showSaved = False):
	global gui, onEscape
	if gui != None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/loadmap.xml')
	gui.stylize('menu')
	eventMap = {
		'cancel'   : showMain,
		'okay'     : startSingle,
	}
	if showSaved:
		eventMap['showNew'] = fife.pychan.tools.callbackWithArguments(showSingle, False)
		files = [f for p in ('content/save', 'content/demo') for f in glob.glob(p + '/*.sqlite') if os.path.isfile(f)]
	else:
		eventMap['showLoad'] = fife.pychan.tools.callbackWithArguments(showSingle, True)
		files = [None] + [f for p in ('content/maps',) for f in glob.glob(p + '/*.sqlite') if os.path.isfile(f)]
	gui.mapEvents(eventMap)
	gui.distributeData({'showNew' : not showSaved, 'showLoad' : showSaved})

	display = ['Random Map' if i == None else i.rpartition('/')[2].rpartition('.')[0] for i in files]
	gui.distributeInitialData({'list' : display})
	gui.files = files
	gui.show()
	onEscape = showMain

def startSingle():
	global gui, fife, session, onEscape, showPause

	file = gui.files[gui.collectData('list')]
	if gui != None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/loadingscreen.xml')
	gui.show()
	fife.engine.pump()
	gui.hide()
	gui = None

	session = Session()
	session.begin()
	if file == None:
		session.generateMap()
	else:
		session.loadMap(file)

def showMulti():
	global gui, onEscape, showMain
	if gui != None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/serverlist.xml')
	gui.stylize('menu')
	gui.server = []
	def _close():
		global gui
		print 'exit'
		print gui.serverList
		gui.serverList.end()
		gui.serverList = None
		showMain()
	eventMap = {
		'cancel'  : _close,
		'create'  : createServer,
		'join'    : joinServer
	}
	gui.mapEvents(eventMap)
	gui.show()
	onEscape = _close
	gui.oldServerType = None
	listServers()

def listServers(serverType = 'internet'):
	gui.mapEvents({
		'refresh'       : fife.pychan.tools.callbackWithArguments(listServers, serverType),
		'showLAN'       : fife.pychan.tools.callbackWithArguments(listServers, 'lan') if serverType != 'lan' else lambda : None,
		'showInternet'  : fife.pychan.tools.callbackWithArguments(listServers, 'internet') if serverType != 'internet' else lambda : None,
		'showFavorites' : fife.pychan.tools.callbackWithArguments(listServers, 'favorites') if serverType != 'favorites' else lambda : None
	})
	gui.distributeData({
		'showLAN'       : serverType == 'lan',
		'showInternet'  : serverType == 'internet',
		'showFavorites' : serverType == 'favorites'
	})

	if gui.oldServerType != serverType:
		if gui.oldServerType != None:
			gui.serverList.end()
		if serverType == 'internet':
			gui.serverList = WANServerList()
		elif serverType == 'lan':
			gui.serverList = LANServerList()
		elif serverType == 'favorites':
			gui.serverList = FavoriteServerList()
	else:
		gui.serverList.changed = lambda : None
		gui.serverList.update()
	def _changed():
		servers = []
		for server in gui.serverList:
			servers.append(str(server))
		gui.distributeInitialData({'list' : servers})
	_changed()
	gui.serverList.changed = _changed
	gui.oldServerType = serverType

def createServer():
	global gui, onEscape, showMulti
	if gui != None:
		gui.serverList.end()
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/serverlobby.xml')
	gui.stylize('menu')
	gui.show()
	onEscape = showMulti

def joinServer():
	global gui, onEscape, showMulti
	if gui != None:
		gui.serverList.end()
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/serverlobby.xml')
	gui.stylize('menu')
	gui.show()
	onEscape = showMulti

def showMultiMapSelect():
	global gui, onEscape, showLobby
	if gui != None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/loadmap.xml')
	gui.stylize('menu')
	gui.show()
	onEscape = showLobby

def showPause():
	global gui, onEscape, quitSession
	if gui != None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/gamemenu.xml')
	gui.stylize('menu')
	eventMap = {
		'startGame'    : returnGame,
		'closeButton'  : quitSession,
	}
	gui.mapEvents(eventMap)
	gui.show()
	onEscape = returnGame

def returnGame():
	global gui, onEscape, showPause
	gui.hide()
	gui = None
	onEscape = showPause

def quitSession():
	global gui, fife, session
	if showDialog(fife.pychan.loadXML('content/gui/quitsession.xml'), {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		gui.hide()
		gui = None
		session.end()
		session = None
		showMain()

def onHelp():
	global fife
	showDialog(fife.pychan.loadXML('content/gui/help.xml'), {'okButton' : True}, onPressEscape = True)
