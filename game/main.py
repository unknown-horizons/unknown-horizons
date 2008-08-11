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

import re
import time
import os.path
import glob
import shutil

from game.util.color import Color
from game.dbreader import DbReader
from game.engine import Fife
from game.settings import Settings
from game.session import Session
from game.gui.mainlistener import MainListener
from game.serverlist import WANServerList, LANServerList, FavoriteServerList
from game.serverlobby import MasterServerLobby, ClientServerLobby
from game.network import Socket, ServerConnection, ClientConnection
from extscheduler import ExtScheduler

#import gc; gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS)

def start():
	"""Starts the game.
	"""
	global db, settings, fife, gui, session, connection, ext_timer, ext_scheduler
	#init db
	db = DbReader(':memory:')
	db("attach ? AS data", 'content/openanno.sqlite')
	
	#init settings
	settings = Settings()
	settings.addCategorys('sound')
	settings.sound.setDefaults(enabled = True)
	settings.addCategorys('network')
	settings.network.setDefaults(port = 62666, url_servers = 'http://master.openanno.org/servers', url_master = 'master.openanno.org', favorites = [])
	settings.addCategorys('savegame')
	settings.savegame.setDefaults(savedquicksaves = 10, autosaveinterval = 10, savedautosaves = 10)

	fife = Fife()
	ext_scheduler = ExtScheduler(fife.pump)

	fife.init()

	mainlistener = MainListener()
	mainlistener.begin()
	connection = None
	session = None
	gui = None

	showMain()

	fife.run()

def onEscape():
	pass

def showCredits():
	"""Shows the credits dialog.
	"""
	global fife
	showDialog(fife.pychan.loadXML('content/gui/credits.xml'), {'okButton' : True}, onPressEscape = True)

def showSettings():
	"""Shows the settings.
	"""
	global fife, settings, onEscape
	resolutions = [str(w) + "x" + str(h) for w, h in fife.settings.getPossibleResolutions() if w >= 1024 and h >= 768]
	if len(resolutions) == 0:
		old = fife.settings.isFullScreen()
		fife.settings.setFullScreen(1)
		resolutions = [str(w) + "x" + str(h) for w, h in fife.settings.getPossibleResolutions() if w >= 1024 and h >= 768]
		fife.settings.setFullScreen(1 if old else 0)
	try:
		resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))
	except:
		resolutions.append(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))
	dlg = fife.pychan.loadXML('content/gui/settings.xml')
	dlg.distributeInitialData({
		'autosaveinterval' : range(0, 60, 2),
		'savedautosaves' : range(1,30),
		'savedquicksaves' : range(1,30),
		'screen_resolution' : resolutions,
		'screen_renderer' : ["OpenGL", "SDL"],
		'screen_bpp' : ["Desktop", "16", "24", "32"]
	})
	dlg.distributeData({
		'autosaveinterval' : settings.savegame.autosaveinterval/2,
		'savedautosaves' : settings.savegame.savedautosaves-1,
		'savedquicksaves' : settings.savegame.savedquicksaves-1,
		'screen_resolution' : resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)),
		'screen_renderer' : 0 if settings.fife.renderer.backend == 'OpenGL' else 1,
		'screen_bpp' : int(settings.fife.screen.bpp / 10), # 0:0 16:1 24:2 32:3 :)
		'screen_fullscreen' : settings.fife.screen.fullscreen,
		'sound_enable_opt' : settings.sound.enabled
	})
	
	if not showDialog(dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		return

	# the following lines prevent typos
	setting_keys = ['autosaveinterval', 'savedautosaves', 'savedquicksaves', 'screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt']
	for key in setting_keys:
		globals()[key] = dlg.collectData(key) 
	
	changes_require_restart = False
	
	if (autosaveinterval)*2 != settings.savegame.autosaveinterval:
		print settings.savegame.autosaveinterval 
		settings.savegame.autosaveinterval = (autosaveinterval)*2
		print settings.savegame.autosaveinterval 
	if savedautosaves+1 != settings.savegame.savedautosaves:
		settings.savegame.savedautosaves = savedautosaves+1
	if savedquicksaves+1 != settings.savegame.savedquicksaves:
		settings.savegame.savedquicksaves = savedquicksaves+1
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

def showDialog(dlg, actions, onPressEscape = None, event_map = None):
	"""
	@param dlg: dialog that is to be shown
	@param actions:
	@param onPressEscape:
	"""
	global onEscape
	if event_map is not None:
		dlg.mapEvents(event_map)
	if onPressEscape is not None:
		def _escape():
			fife.pychan.get_manager().breakFromMainLoop(onPressEscape)
			dlg.hide()
		tmp_escape = onEscape
		onEscape = _escape
	dlg.resizeToContent()
	ret = dlg.execute(actions)
	if onPressEscape is not None:
		onEscape = tmp_escape
	return ret

def showPopup(windowtitle, message, show_cancel_button = False):
	""" Displays a popup with the specified text

	@param windowtitle: the title of the popup
	@param message: the text displayed in the popup
	@return: True on ok, False on cancel (if no cancel button, always True)
	"""
		
	if show_cancel_button:
		popup = fife.pychan.loadXML('content/gui/popupbox_with_cancel.xml')
	else:
		popup = fife.pychan.loadXML('content/gui/popupbox.xml')
	popup.findChild(name='popup_window').title = windowtitle
	popup.findChild(name='popup_message').text = message
	if show_cancel_button:
		# FIXME: check if onPressEscape really should be true here
		return showDialog(popup,{'okButton' : True, 'cancelButton' : False}, onPressEscape = True)
	else:
		return showDialog(popup,{'okButton' : True}, onPressEscape = True)

def getMaps(showOnlySaved = False):
	""" Gets available maps both for displaying and loading.

	@param showOnlySaved: Bool wether saved games are to be shown.
	@return: Tuple of two lists; first: files with path; second: files for displaying
	"""
	if showOnlySaved:
		files = ([f for p in ('content/save/','content/save/quicksave','content/save/autosave','content/demo') for f in glob.glob(p + '/*.sqlite') if os.path.isfile(f)])
	else:
		files = [None] + [f for p in ('content/maps',) for f in glob.glob(p + '/*.sqlite') if os.path.isfile(f)]

	display = ['Random Map' if i is None else os.path.split(i)[1].rpartition('.')[0] for i in files]
	return (files, display)

def showQuit():
	"""Shows the quit dialog
	"""
	global fife
	if showDialog(fife.pychan.loadXML('content/gui/quitgame.xml'), {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		quit()
		
def quit():
	"""Quits the game"""
	global fife
	fife.quit()

def showMain():
	""" shows the main menu
	"""
	global gui, onEscape, showQuit, showSingle, showMulti, showSettings, showCredits
	if gui is not None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/mainmenu.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
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

def showSingle(showOnlySaved = False):
	"""
	@param showOnlySaved: Bool whether saved games are to be shown.
	"""
	global gui, onEscape, db
	if gui is not None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/singleplayermenu.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.stylize('menu')

	eventMap = {
		'cancel'   : showMain,
		'okay'     : startSingle,
	}
	gui.mapEvents(eventMap)
	if showOnlySaved:
		eventMap['showNew'] = fife.pychan.tools.callbackWithArguments(showSingle, False)
	else:
		eventMap['showLoad'] = fife.pychan.tools.callbackWithArguments(showSingle, True)
	gui.mapEvents(eventMap)

	# distribute data
	(gui.files, display) = getMaps(showOnlySaved)

	gui.distributeInitialData({
		'maplist' : display,
		'playercolor' : [ i.name for i in Color ]
	})
	gui.distributeData({
		'showNew' : not showOnlySaved,
		'showLoad' : showOnlySaved,
		'playercolor' : 0
	})

	gui.show()
	onEscape = showMain

def startSingle():
	""" Starts a single player game.
	"""
	global gui, fife, session, onEscape, showPause

	map_id = gui.collectData('maplist')
	if map_id == -1:
		# BUG: this selects the last map by default
		# uncomment the following lines to fix the bug
		#showPopup('Error','You have to select a map')
		#return
		pass

	map_file = gui.files[map_id]
	playername = gui.collectData('playername')
	playercolor = Color[gui.collectData('playercolor')+1] # +1 cause list entries start with 0, color indexes with 1

	if gui is not None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/loadingscreen.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.show()
	fife.engine.pump()
	gui.hide()
	gui = None

	session = Session()
	session.begin()
	if map_file is None:
		session.generateMap()
	else:
		session.load(map_file)
	session.world.setupPlayer(playername, playercolor)

def showMulti():
	global gui, onEscape, showMain, connection
	if gui is not None:
		# delete serverlobby and (Server|Client)Connection
		try:
			gui.serverlobby.end()
		except AttributeError:
			pass
		gui.serverlobby = None
		connection = None
		gui.hide()

	gui = fife.pychan.loadXML('content/gui/serverlist.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.stylize('menu')
	gui.server = []
	def _close():
		"""
		"""
		global gui
		gui.serverList.end()
		gui.serverList = None
		showMain()
	eventMap = {
		'cancel'  : _close,
		'create'  : showCreateServer,
		'join'    : showJoinServer
	}
	gui.mapEvents(eventMap)
	gui.show()
	onEscape = _close
	gui.oldServerType = None
	listServers()

def startMulti():
	"""Starts a multiplayer game server (dummy)

	This also starts the game for the game mater
	"""
	pass

def listServers(serverType = 'internet'):
	"""
	@param serverType:
	"""
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
		# deselect server when changing mode
		gui.distributeData({'list' : -1})
		if gui.oldServerType is not None:
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
		"""
		"""
		servers = []
		for server in gui.serverList:
			servers.append(str(server))
		gui.distributeInitialData({'list' : servers})
	_changed()
	gui.serverList.changed = _changed
	gui.oldServerType = serverType

def showCreateServer():
	"""Interface for creating a server

	Here, the game master can set details about a multiplayer game.
	"""
	global gui, onEscape, showMulti, startMulti, settings, connection
	if gui is not None:
		gui.serverList.end()
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/serverlobby.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)

	connection = ServerConnection(settings.network.port)

	gui.serverlobby = MasterServerLobby(gui)
	gui.serverlobby.update_gui()

	def _cancel():
		global gui, connection
		connection.end()
		gui.serverlobby.end()
		connection = None
		gui.serverlobby = None
		showMulti()

	gui.mapEvents({
		'startMulti' : startMulti,
		'cancel' : _cancel
	})

	gui.stylize('menu')
	gui.show()
	onEscape = showMulti

def showJoinServer():
	"""Interface for joining a server

	The user can select username & color here
	and map & player are displayed (read-only)
	"""
	global gui, onEscape, showMulti, connection, settings
	#if gui is not None:
	# gui has to be not None, otherwise the selected server
	# couldn't be retrieved

	server_id = gui.collectData('list')
	if server_id == -1: # no server selected
		showPopup('Error','You have to select a server')
		return
	server = gui.serverList[server_id]
	gui.serverList.end()
	gui.hide()

	connection = ClientConnection()
	connection.join(server.address, server.port)
	gui = fife.pychan.loadXML('content/gui/serverlobby.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.serverlobby = ClientServerLobby(gui)

	def _cancel():
		global gui, connection
		connection.end()
		gui.serverlobby.end()
		connection = None
		gui.serverlobby = None
		showMulti()

	gui.mapEvents({
		'cancel' : _cancel
	})
	gui.stylize('menu')
	gui.show()
	onEscape = showMulti

def showPause():
	"""
	"""
	global gui, onEscape, quitSession
	if gui is not None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/gamemenu.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.stylize('menu')
	eventMap = {
		'startGame'    : returnGame,
		'closeButton'  : quitSession,
		'savegameButton' : saveGame,
		'loadgameButton' : loadGame
	}
	gui.mapEvents(eventMap)
	gui.show()
	onEscape = returnGame

def returnGame():
	"""
	"""
	global gui, onEscape, showPause
	gui.hide()
	gui = None
	onEscape = showPause

def quitSession():
	"""
	"""
	global gui, fife, session
	if showDialog(fife.pychan.loadXML('content/gui/quitsession.xml'), {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		gui.hide()
		gui = None
		session.end()
		session = None
		showMain()
		
def saveGame():
	global session
	
	savegame_files, savegame_display = getMaps(showOnlySaved = True)
	
	save_dlg = fife.pychan.loadXML('content/gui/ingame_save.xml')
	
	save_dlg.distributeInitialData({'savegamelist' : savegame_display})
	
	def tmp_selected_changed():
		"""Fills in the name of the savegame in the textbox when selected in the list"""
		save_dlg.distributeData({'savegamefile' : savegame_display[save_dlg.collectData('savegamelist')]})
	
	save_dlg.findChild(name='savegamelist').capture(tmp_selected_changed)
	if not showDialog(save_dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False,):
		return
	
	savegamename = save_dlg.collectData('savegamefile')
	
	# allow only: alphanumeric, '.' and '-'
	if re.match('^[\w\.\-]+$', savegamename) is None:
		showPopup("Invalid filename", "You entered an invalid filename.")
		saveGame()
		return
	
	savegamefile = 'content/save/%s.sqlite' % savegamename
	
	if os.path.exists(savegamefile):
		if not showPopup("Confirmation for overwriting", 
										 "A savegame with the name \"%s\" already exists. Should i overwrite it?"%savegamename, 
										 show_cancel_button = True):
			saveGame()
			return
	
	session.save(savegamefile)

def loadGame():
	global session, gui, fife
	
	map_files, map_file_display = getMaps(showOnlySaved = True)

	if len(map_files) == 0:
		showPopup("No saved games", "There are no saved games to load")
		return
	
	load_dlg = fife.pychan.loadXML('content/gui/ingame_load.xml')
	
	load_dlg.distributeInitialData({'savegamelist' : map_file_display})
	
	def tmp_show_details():
		"""Fetches details of selected savegame and displays it"""
		box = load_dlg.findChild(name="savegamedetails_box")
		details_label = fife.pychan.widgets.Label(max_size=(140,290), wrap_text=True)
		details_label.name="savegamedetails_lbl"
		db = DbReader(map_files[load_dlg.collectData("savegamelist")])
		timestamp = db("SELECT `value` FROM `metadata` WHERE `name` = \"timestamp\"")[0][0]
		timestamp = float(timestamp)
		details_label.text="Saved at "+time.strftime("%H:%M, %A, %B %d", time.localtime(timestamp))
		old_label = load_dlg.findChild(name="savegamedetails_lbl")
		if old_label is not None:
			box.removeChild(old_label)
		box.addChild( details_label )
		load_dlg.adaptLayout()
	
	load_dlg.findChild(name="savegamelist").capture(tmp_show_details)
	if not showDialog(load_dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
		return
	
	savegamefile = map_files[ load_dlg.collectData('savegamelist') ]
	
	assert(os.path.exists(savegamefile))
	
	session.end()
	session = None
	
	if gui is not None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/loadingscreen.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.show()
	fife.engine.pump()

	session = Session()
	session.begin()
	session.load(savegamefile)
	returnGame()

def onHelp():
	"""
	"""
	global fife
	showDialog(fife.pychan.loadXML('content/gui/help.xml'), {'okButton' : True}, onPressEscape = True)
