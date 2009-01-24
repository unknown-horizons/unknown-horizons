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
import game.main
import fife
import os
import os.path
import glob
import time

from game.util.color import Color
from game.serverlist import WANServerList, LANServerList, FavoriteServerList
from game.serverlobby import MasterServerLobby, ClientServerLobby
from game.network import Socket, ServerConnection, ClientConnection
class Menus(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc."""

	def __init__(self):
		fife = game.main.fife
		self.current = None # currently active window
		self.widgets = {} # Stores all the widgets, to prevent double loading
		self.widgets['mainmenu'] = fife.pychan.loadXML('content/gui/mainmenu.xml')
		self.widgets['mainmenu'].stylize('menu')
		self.widgets['quitgame'] = fife.pychan.loadXML('content/gui/quitgame.xml')
		self.widgets['credits'] = fife.pychan.loadXML('content/gui/credits.xml')
		self.widgets['settings'] = fife.pychan.loadXML('content/gui/settings.xml')
		self.widgets['requirerestart'] = fife.pychan.loadXML('content/gui/changes_require_restart.xml')
		self.widgets['popup_with_cancel'] = fife.pychan.loadXML('content/gui/popupbox_with_cancel.xml')
		self.widgets['popup'] = fife.pychan.loadXML('content/gui/popupbox.xml')
		self.widgets['gamemenu'] = fife.pychan.loadXML('content/gui/gamemenu.xml')
		self.widgets['gamemenu'].stylize('menu')
		self.widgets['chime'] = fife.pychan.loadXML('content/gui/chime.xml')
		self.widgets['help'] = fife.pychan.loadXML('content/gui/help.xml')
		self.widgets['quitsession'] = fife.pychan.loadXML('content/gui/quitsession.xml')
		self.widgets['singleplayermenu'] = fife.pychan.loadXML('content/gui/singleplayermenu.xml')
		self.widgets['singleplayermenu'].stylize('menu')
		self.widgets['serverlist'] = fife.pychan.loadXML('content/gui/serverlist.xml')
		self.widgets['serverlist'].stylize('menu')
		self.widgets['serverlobby'] = fife.pychan.loadXML('content/gui/serverlobby.xml')
		self.widgets['serverlobby'].stylize('menu')
		self.widgets['loadingscreen'] = fife.pychan.loadXML('content/gui/loadingscreen.xml')
		self.widgets['ingame_load'] = fife.pychan.loadXML('content/gui/ingame_load.xml')
		self.widgets['savegame'] = fife.pychan.loadXML('content/gui/ingame_save.xml')

	def show_main(self):
		""" shows the main menu
		"""
		self.hide() # Hide old gui
		self.current = self.widgets['mainmenu']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)
		eventMap = {
			'startSingle'  : self.show_single,
			'startMulti'   : self.show_multi,
			'settingsLink' : self.show_settings,
			'creditsLink'  : self.show_credits,
			'closeButton'  : self.show_quit,
			'helpLink'     : self.on_help,
			'loadgameButton' : self.load_game,
			'dead_link'	 : self.on_chime
		}
		self.current.mapEvents(eventMap)
		self.current.show()
		self.on_escape = self.show_quit


	def show_quit(self):
		"""Shows the quit dialog
		"""
		if self.show_dialog(self.widgets['quitgame'], {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
			game.main.quit()

	def show_credits(self):
		"""Shows the credits dialog.
		"""
		self.show_dialog(self.widgets['credits'], {'okButton' : True}, onPressEscape = True)

	def show_dialog(self, dlg, actions, onPressEscape = None, event_map = None):
		"""
		@param dlg: dialog that is to be shown
		@param actions: actions that are executed by the dialog { 'ok': callback, 'cancel': callback }
		@param onPressEscape: callback that is to be called if the escape button is pressed.
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		"""
		# Uncomment if detach Segfault is resolved.
		# gui.deepApply(lambda x: x.event_mapper.detach())
		if event_map is not None:
			dlg.mapEvents(event_map)
		if onPressEscape is not None:
			def _escape():
				game.main.fife.pychan.get_manager().breakFromMainLoop(onPressEscape)
				dlg.hide()
			tmp_escape = self.on_escape
			self.on_escape = _escape
		dlg.resizeToContent()
		ret = dlg.execute(actions)
		if onPressEscape is not None:
			self.on_escape = tmp_escape
		# Uncomment if detach Segfault is resolved.
		#gui.deepApply(lambda x: x.event_mapper.attach())
		return ret

	def show_settings(self):
		"""Shows the settings.
		"""
		fife = game.main.fife
		settings = game.main.settings

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
		dlg = self.widgets['settings']
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

		dlg.mapEvents({
			'volume_music' : game.main.fife.pychan.tools.callbackWithArguments(self.set_volume, \
				dlg.findChild(name='volume_music_value'), \
				dlg.findChild(name='volume_music'), \
				'bgsound'),
			'volume_effects' : game.main.fife.pychan.tools.callbackWithArguments(self.set_volume, \
				dlg.findChild(name='volume_effects_value'), \
				dlg.findChild(name='volume_effects'), \
				'effects')
		})

		# Save old musik volumes incase the user presses cancel
		volume_music_intial = settings.sound.volume_music
		volume_effects_intial = settings.sound.volume_effects

		# Set music volume display and slider correctly
		volume_music = dlg.findChild(name='volume_music')
		volume_music.setValue(settings.sound.volume_music)
		volume_music_value =  dlg.findChild(name='volume_music_value')
		volume_music_value.text = str(int(volume_music.getValue() * 100)) + '%'

		# Set effects volume display and slider correctly
		volume_effects = dlg.findChild(name='volume_effects')
		volume_effects.setValue(settings.sound.volume_effects)
		volume_effects_value =  dlg.findChild(name='volume_effects_value')
		volume_effects_value.text = str(int(volume_effects.getValue() * 100)) + '%'

		if not self.show_dialog(dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
			if settings.sound.enabled:
				fife.emitter['bgsound'].setGain(volume_music_intial)
				fife.emitter['effects'].setGain(volume_effects_intial)
				fife.emitter['speech'].setGain(volume_effects_intial)
			return

		# the following lines prevent typos
		setting_keys = ['autosaveinterval', 'savedautosaves', 'savedquicksaves', 'screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt']
		new_settings = {}
		for key in setting_keys:
			new_settings[key] = dlg.collectData(key)

		changes_require_restart = False

		if (new_settings['autosaveinterval'])*2 != settings.savegame.autosaveinterval:
			print settings.savegame.autosaveinterval
			settings.savegame.autosaveinterval = (new_settings['autosaveinterval'])*2
			print settings.savegame.autosaveinterval
		if new_settings['savedautosaves']+1 != settings.savegame.savedautosaves:
			settings.savegame.savedautosaves =new_settings[' savedautosaves']+1
		if new_settings['savedquicksaves']+1 != settings.savegame.savedquicksaves:
			settings.savegame.savedquicksaves = new_settings['savedquicksaves']+1
		if new_settings['screen_fullscreen'] != settings.fife.screen.fullscreen:
			settings.fife.screen.fullscreen = new_settings['screen_fullscreen']
			changes_require_restart = True
		if new_settings['sound_enable_opt'] != settings.sound.enabled:
			settings.sound.enabled = new_settings['sound_enable_opt']
			changes_require_restart = True
		if volume_music.getValue() != settings.sound.volume_music:
			settings.sound.volume_music = volume_music.getValue()
		if volume_effects.getValue() != settings.sound.volume_effects:
			settings.sound.volume_effects = volume_effects.getValue()
		if new_settings['screen_bpp'] != int(settings.fife.screen.bpp / 10):
			settings.fife.screen.bpp = 0 if screen_bpp == 0 else ((screen_bpp + 1) * 8)
			changes_require_restart = True
		if new_settings['screen_renderer'] != (0 if settings.fife.renderer.backend == 'OpenGL' else 1):
			settings.fife.renderer.backend = 'OpenGL' if new_settings['screen_renderer'] == 0 else 'SDL'
			changes_require_restart = True
		if new_settings['screen_resolution'] != resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)):
			settings.fife.screen.width = int(resolutions[screen_resolution].partition('x')[0])
			settings.fife.screen.height = int(resolutions[screen_resolution].partition('x')[2])
			changes_require_restart = True

		if changes_require_restart:
			self.show_dialog(self.widgets['requirerestart'], {'okButton' : True}, onPressEscape = True)

	def show_popup(self, windowtitle, message, show_cancel_button = False):
		""" Displays a popup with the specified text

		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, show cancel button or not
		@return: True on ok, False on cancel (if no cancel button, always True)
		"""

		if show_cancel_button:
			popup = self.widgets['popup_with_cancel']
		else:
			popup = self.widgets['popup']
		popup.findChild(name='popup_window').title = windowtitle
		popup.findChild(name='popup_message').text = message
		if show_cancel_button:
			return self.show_dialog(popup,{'okButton' : True, 'cancelButton' : False}, onPressEscape = False)
		else:
			return self.show_dialog(popup,{'okButton' : True}, onPressEscape = True)

	def show_pause(self):
		"""
		Show Pause menu
		"""
		self.hide() # Hide old gui
		self.current = self.widgets['gamemenu']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)
		eventMap = {
			'startGame'    : self.return_to_game,
			'closeButton'  : self.quit_session,
			'savegameButton' : game.main.saveGame,
			'loadgameButton' : self.load_game,
			'helpLink'	 : self.on_help,
			'settingsLink'   : self.show_settings,
			'dead_link'	 : self.on_chime
		}
		self.current.mapEvents(eventMap)
		self.current.show()
		game.main.session.speed_pause()
		self.on_escape = self.return_to_game


	def on_chime(self):
		"""
		Called chime action.
		"""
		game.main.fife.play_sound('effects', 'content/audio/sounds/ships_bell.ogg')
		self.show_dialog(self.widgets['chime'], {'okButton' : True}, onPressEscape = True)


	def set_volume(self, label, slider, emitter):
		label.text = str(int(slider.getValue() * 100)) + '%'
		game.main.fife.set_volume(emitter, slider.getValue())

	def on_help(self):
		"""
		Called on help action
		"""
		self.show_dialog(self.widgets['help'], {'okButton' : True}, onPressEscape = True)


	def quit_session(self):
		"""
		Quits the current session
		"""
		if self.show_dialog(self.widgets['quitsession'],  {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
			self.current.hide()
			self.current = None
			game.main.session = None
			self.show_main()


	def return_to_game(self):
		"""
		Return to the game.
		"""
		self.hide() # Hide olo gui
		self.current = None
		game.main.session.speed_unpause()
		self.on_escape = self.show_pause

	def show_single(self, showRandom = False, showCampaign = True, showLoad = False):
		"""
		@param showRandom: Bool if random games menu is to be shown.
		@param showCampaign: Bool if  campaigngame menu is to be shown.
		@param showLoad: Bool if saved games menu is to be shown.
		"""
		self.hide() # Hide old gui
		self.widgets['singleplayermenu'] = game.main.fife.pychan.loadXML('content/gui/singleplayermenu.xml') # reload because parts are beeing removed on each show
		self.widgets['singleplayermenu'].stylize('menu')
		self.current = self.widgets['singleplayermenu']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)
		eventMap = {
			'cancel'   : self.show_main,
			'okay'     : self.start_single,
		}
		if showRandom:
			print self.current
			print self.current.findChild(name='load')
			self.current.removeChild(self.current.findChild(name="load"))
			eventMap['showCampaign'] = game.main.fife.pychan.tools.callbackWithArguments(self.show_single, False, True, False)
			eventMap['showLoad'] = game.main.fife.pychan.tools.callbackWithArguments(self.show_single, False, False, True)
			self.current.distributeInitialData({
				'playercolor' : [ i.name for i in Color ]
			})
			self.current.distributeData({
				'playercolor' : 0
			})
		else:
			self.current.findChild(name="random")._parent.removeChild(self.current.findChild(name="random"))
			self.current.files, display = self.get_maps(showCampaign, showLoad)
			self.current.distributeInitialData({
				'maplist' : display,
			})
			if len(display) > 0:
				self.current.distributeData({
					'maplist' : 0
				})
				eventMap["maplist"] = self.create_show_savegame_details(self.current, self.current.files, 'maplist')
			if showCampaign:
				eventMap['showRandom'] = game.main.fife.pychan.tools.callbackWithArguments(self.show_single, True, False, False)
				eventMap['showLoad'] = game.main.fife.pychan.tools.callbackWithArguments(self.show_single, False, False, True)
			elif showLoad:
				eventMap['showRandom'] = game.main.fife.pychan.tools.callbackWithArguments(self.show_single, True, False, False)
				eventMap['showCampaign'] = game.main.fife.pychan.tools.callbackWithArguments(self.show_single, False, True, False)
		self.current.mapEvents(eventMap)

		self.current.distributeData({
			'showRandom' : showRandom,
			'showCampaign' : showCampaign,
			'showLoad' : showLoad,
		})

		self.current.show()
		self.on_escape = self.show_main

	def get_maps(self, showCampaign = True, showLoad = False):
		""" Gets available maps both for displaying and loading.

		@param showCampaign: Bool, show campaign games true/false
		@param showLoad saves: Bool, show saved games yes/no
		@return: Tuple of two lists; first: files with path; second: files for displaying
		"""
		if showLoad:
			return game.main.savegamemanager.get_saves()
		elif showCampaign:
			files = [f for p in ('content/maps',) for f in glob.glob(p + '/*.sqlite') if os.path.isfile(f)]
			display = [os.path.split(i)[1].rpartition('.')[0] for i in files]
			return (files, display)


	def on_escape(self):
		pass

	def show_multi(self):
		if self.current is not None:
			# delete serverlobby and (Server|Client)Connection
			try:
				self.current.serverlobby.end()
			except AttributeError:
				pass
			self.current.serverlobby = None
			game.main.connection = None
			self.current.hide()

		self.current = self.widgets['serverlist']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)
		self.current.server = []
		def _close():
			"""
			"""
			self.current.serverList.end()
			self.current.serverList = None
			self.show_main()
		eventMap = {
			'cancel'  : _close,
			'create'  : self.show_create_server,
			'join'    : self.show_join_server
		}
		self.current.mapEvents(eventMap)
		self.current.show()
		self.on_escape = _close
		self.current.oldServerType = None
		self.list_servers()

	def list_servers(self, serverType = 'internet'):
		"""
		@param serverType:
		"""
		self.current.mapEvents({
			'refresh'       : game.main.fife.pychan.tools.callbackWithArguments(self.list_servers, serverType),
			'showLAN'       : game.main.fife.pychan.tools.callbackWithArguments(self.list_servers, 'lan') if serverType != 'lan' else lambda : None,
			'showInternet'  : game.main.fife.pychan.tools.callbackWithArguments(self.list_servers, 'internet') if serverType != 'internet' else lambda : None,
			'showFavorites' : game.main.fife.pychan.tools.callbackWithArguments(self.list_servers, 'favorites') if serverType != 'favorites' else lambda : None
		})
		self.current.distributeData({
			'showLAN'       : serverType == 'lan',
			'showInternet'  : serverType == 'internet',
			'showFavorites' : serverType == 'favorites'
		})

		if self.current.oldServerType != serverType:
			# deselect server when changing mode
			self.current.distributeData({'list' : -1})
			if self.current.oldServerType is not None:
				self.current.serverList.end()
			if serverType == 'internet':
				self.current.serverList = WANServerList()
			elif serverType == 'lan':
				self.current.serverList = LANServerList()
			elif serverType == 'favorites':
				self.current.serverList = FavoriteServerList()
		else:
			self.current.serverList.changed = lambda : None
			self.current.serverList.update()
		def _changed():
			"""
			"""
			servers = []
			for server in self.current.serverList:
				servers.append(str(server))
			self.current.distributeInitialData({'list' : servers})
		_changed()
		self.current.serverList.changed = _changed
		self.current.oldServerType = serverType


	def show_create_server(self):
		"""Interface for creating a server

		Here, the game master can set details about a multiplayer game.
		"""
		if self.current is not None:
			self.current.serverList.end()
			self.current.hide()
		self.current = self.widgets['serverlobby']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)

		game.main.connection = ServerConnection(game.main.settings.network.port)

		self.current.serverlobby = MasterServerLobby(self.current)
		self.current.serverlobby.update_gui()

		def _cancel():
			game.main.connection.end()
			self.current.serverlobby.end()
			game.main.connection = None
			self.current.serverlobby = None
			self.show_multi()

		self.current.mapEvents({
			'startMulti' : game.main.startMulti,
			'cancel' : _cancel
		})

		self.current.show()
		self.on_escape = self.show_multi


	def show_join_server(self):
		"""Interface for joining a server

		The user can select username & color here
		and map & player are displayed (read-only)
		"""
		#if gui is not None:
		# gui has to be not None, otherwise the selected server
		# couldn't be retrieved

		server_id = self.current.collectData('list')
		if server_id == -1: # no server selected
			self.show_popup('Error','You have to select a server')
			return
		server = self.current.serverList[server_id]
		self.current.serverList.end()
		self.current.hide()

		game.main.connection = ClientConnection()
		game.main.connection.join(server.address, server.port)
		self.current = self.widgets['serverlobby']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)
		self.current.serverlobby = ClientServerLobby(self.current)

		def _cancel():
			game.main.connection.end()
			self.current.serverlobby.end()
			game.main.connection = None
			self.current.serverlobby = None
			showMulti()

		self.current.mapEvents({
			'cancel' : _cancel
		})
		self.current.show()
		self.on_escape = self.show_multi


	def delete_savegame(self, gui, map_files):
		"""Deletes the selected savegame if the user confirms
		@param gui: handle for pychan gui, that includes the widget 'savegamelist'
		@param map_files: list of files that corresponds to the entries of 'savegamelist'
		@return: True if something was deleted, else False
		"""
		selected_item = self.current.collectData("savegamelist")
		if selected_item == -1:
			showPopup("No file selected", "You need to select a savegame to delete")
			return False
		selected_file = map_files[selected_item]
		if showPopup("Confirm deletiom",
								 'Do you really want to delete the savegame "%s"?' % os.path.basename(selected_file),
								 show_cancel_button = True):
			os.unlink(selected_file)
			return True
		else:
			return False

	def create_show_savegame_details(self, gui, map_files, savegamelist):
		def tmp_show_details():
			"""Fetches details of selected savegame and displays it"""
			box = gui.findChild(name="savegamedetails_box")
			old_label = box.findChild(name="savegamedetails_lbl")
			if old_label is not None:
				box.removeChild(old_label)
			try:
				savegame_info = game.main.savegamemanager.get_savegame_info(map_files[gui.collectData(savegamelist)])
			except:
				gui.adaptLayout()
				return
			details_label = game.main.fife.pychan.widgets.Label(max_size=(140,290), wrap_text=True)
			details_label.name="savegamedetails_lbl"
			details_label.text="Unknown savedate" if savegame_info['timestamp'] == -1 else "Saved at %s" % time.strftime("%H:%M, %A, %B %d", time.localtime(savegame_info['timestamp']))
			box.addChild( details_label )
			gui.adaptLayout()
		return tmp_show_details

	def hide(self):
		if self.current is not None:
			self.current.hide()

	def show(self):
		if self.current is not None:
			self.current.show()


	def start_single(self):
		""" Starts a single player game.
		"""
		showRandom = self.current.collectData('showRandom')
		showCampaign = self.current.collectData('showCampaign')
		showLoad = self.current.collectData('showLoad')

		if showRandom:
			playername = self.current.collectData('playername')
			if len(playername) == 0:
				showPopup("Invalid player name", "You entered an invalid playername")
				return
			playercolor = Color[self.current.collectData('playercolor')+1] # +1 cause list entries start with 0, color indexes with 1
			showPopup("Not implemented", "Sorry, random map creation is not implemented at the moment.")
			return
		else:
			map_id = self.current.collectData('maplist')
			if map_id == -1:
				return
			map_file = self.current.files[map_id]

			self.hide()
			self.current = self.widgets['loadingscreen']
			self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
			self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)

			game.main.start_singleplayer(map_file)


	def load_game(self, savegame = None):
		# Loading is disabled for now
		#showDialog(fife.pychan.loadXML('content/gui/load_disabled.xml'), {'okButton' : True}, onPressEscape = True)
		#return

		if savegame is None:
			map_files, map_file_display = game.main.savegamemanager.get_saves()

			if len(map_files) == 0:
				self.show_popup("No saved games", "There are no saved games to load")
				return

			load_dlg = self.widgets['ingame_load']

			load_dlg.distributeInitialData({'savegamelist' : map_file_display})

			def tmp_delete_savegame():
				if self.delete_savegame(load_dlg, map_files):
					load_dlg.hide()
					self.load_game()

			load_dlg.findChild(name="savegamelist").capture(self.create_show_savegame_details(load_dlg, map_files, 'savegamelist'))
			if not self.show_dialog(load_dlg, {'okButton' : True, 'cancelButton' : False},
												onPressEscape = False,
												event_map={'deleteButton' : tmp_delete_savegame}):
				return

			selected_savegame = load_dlg.collectData('savegamelist')
			if selected_savegame == -1:
				return
			savegamefile = map_files[ selected_savegame ]
		else:
			savegamefile = savegame

		assert(os.path.exists(savegamefile))

		self.hide()
		self.current = self.widget['loadingscreen']
		self.current.x += int((game.main.settings.fife.screen.width - self.current.width) / 2)
		self.current.y += int((game.main.settings.fife.screen.height - self.current.height) / 2)
		self.show()
		game.main.start_multiplayer(savegamefile)

	def save_game(self):
		savegame_files, savegame_display = savegamemanager.get_regular_saves()

		save_dlg = self.widgets['savegame']

		save_dlg.distributeInitialData({'savegamelist' : savegame_display})

		def tmp_selected_changed():
			"""Fills in the name of the savegame in the textbox when selected in the list"""
			save_dlg.distributeData({'savegamefile' : savegame_display[save_dlg.collectData('savegamelist')]})

		def tmp_delete_savegame():
			if delete_savegame(save_dlg, savegame_files):
				save_dlg.hide()
				self.save_game()

		save_dlg.findChild(name='savegamelist').capture(tmp_selected_changed)
		if not self.show_dialog(save_dlg, {'okButton' : True, 'cancelButton' : False},
											onPressEscape = False,
											event_map={'deleteButton' : tmp_delete_savegame}):
			return

		savegamename = save_dlg.collectData('savegamefile')
		game.main.saveGame(savegamename)
