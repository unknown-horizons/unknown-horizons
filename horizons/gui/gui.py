# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
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
import os
import os.path
import glob
import time
import pychan

import horizons.main

from horizons.savegamemanager import SavegameManager
from horizons.serverlist import WANServerList, LANServerList, FavoriteServerList
from horizons.serverlobby import MasterServerLobby, ClientServerLobby
from horizons.network import ServerConnection, ClientConnection
from horizons.i18n import load_xml_translated, update_all_translations
from horizons.i18n.utils import find_available_languages
from horizons.gui.keylisteners import MainListener
from horizons.util import Callback, Color
from horizons.gui.utility import center_widget

class LazyWidgetsDict(dict):
	"""Dictionary for UH widgets. Loads widget on first access."""
	def __getitem__(self, widgetname):
		try:
			return dict.__getitem__(self, widgetname)
		except KeyError:
			widget = load_xml_translated(widgetname+'.xml')
			center_widget(widget)
			headline = widget.findChild(name='headline')
			if headline:
				headline.stylize('headline')
			if widgetname in Gui.styles:
				widget.stylize(Gui.styles[widgetname])

			self[widgetname] = widget
			return self[widgetname]


class Gui(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc."""
	# styles to apply to a widget
	styles = {
	  'mainmenu': 'menu',
	  'quitgame': 'book',
	  'credits': 'book',
	  'settings': 'book',
	  'requirerestart': 'book',
	  'popup_with_cancel': 'book',
	  'popup': 'book',
	  'gamemenu': 'menu',
	  'chime': 'book',
	  'help': 'book',
	  'quitsession': 'book',
	  'singleplayermenu': 'book',
	  'serverlist': 'menu',
	  'serverlobby': 'menu',
	  'select_savegame': 'book',
	  'ingame_pause': 'book'
	  }

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.current = None # currently active window
		self.widgets = LazyWidgetsDict() # access widgets with their filenames without '.xml'

	def show_main(self):
		""" shows the main menu """
		self.__switch_current_widget('mainmenu', center=True, show=True, event_map = {
			'startSingle'  : self.show_single,
			'startMulti'   : self.show_multi,
			'settingsLink' : self.show_settings,
			'creditsLink'  : self.show_credits,
			'closeButton'  : self.show_quit,
			'helpLink'     : self.on_help,
			'loadgameButton' : horizons.main.load_game,
			'dead_link'	 : self.on_chime
		})
		self.on_escape = self.show_quit

	def show_quit(self):
		"""Shows the quit dialog """
		if self.show_dialog(self.widgets['quitgame'], {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
			horizons.main.quit()

	def show_credits(self):
		"""Shows the credits dialog. """
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
				pychan.internal.get_manager().breakFromMainLoop(onPressEscape)
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
		fife = horizons.main.fife
		settings = horizons.main.settings

		resolutions = [str(w) + "x" + str(h) for w, h in fife.settings.getPossibleResolutions() if w >= 1024 and h >= 768]
		if len(resolutions) == 0:
			old = fife.settings.isFullScreen()
			fife.settings.setFullScreen(1)
			resolutions = [str(w) + "x" + str(h) for w, h in fife.settings.getPossibleResolutions() if w >= 1024 and h >= 768]
			fife.settings.setFullScreen(1 if old else 0)
		try:
			resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))
		except ValueError:
			resolutions.append(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))

		languages_map = dict(reversed(find_available_languages()))
		languages_map[_('System default')] = ''

		dlg = self.widgets['settings']
		dlg.distributeInitialData({
			'language' : languages_map.keys(),
			'autosaveinterval' : range(0, 60, 2),
			'savedautosaves' : range(1, 30),
			'savedquicksaves' : range(1, 30),
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
			'sound_enable_opt' : settings.sound.enabled,
			'language' : languages_map.keys().index(_('System default') if \
		      settings.language.name == '' or settings.language.name == 'System default' else \
		      settings.language.name)
		})

		dlg.mapEvents({
			'volume_music' : pychan.tools.callbackWithArguments(self.set_volume, dlg.findChild(name='volume_music_value'), dlg.findChild(name='volume_music')),
			'volume_effects' : pychan.tools.callbackWithArguments(self.set_volume, dlg.findChild(name='volume_effects_value'), dlg.findChild(name='volume_effects'))
		})

		# Save old music volumes in case the user presses cancel
		volume_music_intial = settings.sound.volume_music
		volume_effects_intial = settings.sound.volume_effects

		# Set music volume display and slider correctly
		volume_music = dlg.findChild(name='volume_music')
		volume_music.setValue(settings.sound.volume_music)
		volume_music_value =  dlg.findChild(name='volume_music_value')
		volume_music_value.text = unicode(int(volume_music.getValue() * 100 * 5)) + '%'

		# Set effects volume display and slider correctly
		volume_effects = dlg.findChild(name='volume_effects')
		volume_effects.setValue(settings.sound.volume_effects)
		volume_effects_value =  dlg.findChild(name='volume_effects_value')
		volume_effects_value.text = unicode(int(volume_effects.getValue() * 100 * 2)) + '%'

		if not self.show_dialog(dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
			if settings.sound.enabled:
				fife.emitter['bgsound'].setGain(volume_music_intial)
				fife.emitter['effects'].setGain(volume_effects_intial)
				fife.emitter['speech'].setGain(volume_effects_intial)
				for e in fife.emitter['ambient']:
					e.setGain(volume_effects_intial)
			return

		# the following lines prevent typos
		setting_keys = ['autosaveinterval', 'savedautosaves', 'savedquicksaves', 'screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt', 'language']
		new_settings = {}
		for key in setting_keys:
			new_settings[key] = dlg.collectData(key)

		changes_require_restart = False

		settings.savegame.autosaveinterval = (new_settings['autosaveinterval'])*2
		settings.savegame.savedautosaves = new_settings['savedautosaves']+1
		settings.savegame.savedquicksaves = new_settings['savedquicksaves']+1
		if new_settings['screen_fullscreen'] != settings.fife.screen.fullscreen:
			settings.fife.screen.fullscreen = new_settings['screen_fullscreen']
			changes_require_restart = True
		if new_settings['sound_enable_opt'] != settings.sound.enabled:
			settings.sound.enabled = new_settings['sound_enable_opt']
			changes_require_restart = True
		settings.sound.volume_music = volume_music.getValue()
		settings.sound.volume_effects = volume_effects.getValue()
		if new_settings['screen_bpp'] != int(settings.fife.screen.bpp / 10):
			settings.fife.screen.bpp = 0 if new_settings['screen_bpp'] == 0 else ((new_settings['screen_bpp'] + 1) * 8)
			changes_require_restart = True
		if new_settings['screen_renderer'] != (0 if settings.fife.renderer.backend == 'OpenGL' else 1):
			settings.fife.renderer.backend = 'OpenGL' if new_settings['screen_renderer'] == 0 else 'SDL'
			changes_require_restart = True
		if new_settings['screen_resolution'] != resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)):
			settings.fife.screen.width = int(resolutions[new_settings['screen_resolution']].partition('x')[0])
			settings.fife.screen.height = int(resolutions[new_settings['screen_resolution']].partition('x')[2])
			changes_require_restart = True
		if languages_map.items()[new_settings['language']][0] != settings.language.name:
			import gettext
			settings.language.name, settings.language.position = languages_map.items()[new_settings['language']]
			if settings.language.name != _('System default'):
				trans = gettext.translation('unknownhorizons', settings.language.position, languages=[settings.language.name])
				trans.install(unicode=1)
			else:
				gettext.install('unknownhorizons', 'po', unicode=1)
				settings.language.name = ''
			update_all_translations()

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
		# just to be safe, the gettext-function is used twice,
		# once on the original, once on the unicode string.
		popup.findChild(name='headline').text = _(unicode(_(windowtitle)))
		popup.findChild(name='popup_message').text = _(unicode(_(message)))
		if show_cancel_button:
			return self.show_dialog(popup, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False)
		else:
			return self.show_dialog(popup, {'okButton' : True}, onPressEscape = True)

	def show_pause(self):
		"""
		Show Pause menu
		"""
		self.__switch_current_widget('gamemenu', center=True, show=True, event_map={
			'startGame'    : self.return_to_game,
			'closeButton'  : self.quit_session,
			'savegameButton' : horizons.main.save_game,
			'loadgameButton' : horizons.main.load_game,
			'helpLink'	 : self.on_help,
			'settingsLink'   : self.show_settings,
			'dead_link'	 : self.on_chime
		})
		horizons.main.session.speed_pause()
		self.on_escape = self.return_to_game

	def on_chime(self):
		"""
		Called chime action.
		"""
		# this is just for now, so hardcoded path is ok
		horizons.main.fife.play_sound('effects', 'content/audio/sounds/ships_bell.ogg')
		self.show_dialog(self.widgets['chime'], {'okButton' : True}, onPressEscape = True)

	def set_volume(self, label, slider):
		if label.name == 'volume_music_value':
			label.text = unicode(int(slider.getValue() * 100 * 5)) + '%'
			horizons.main.fife.set_volume_music(slider.getValue())
		else:
			label.text = unicode(int(slider.getValue() * 100 * 2)) + '%'
			horizons.main.fife.set_volume_effects(slider.getValue())

	help_is_displayed = False
	def on_help(self):
		"""Called on help action
		Toggles help screen via static variable help_is_displayed"""
		help_dlg = self.widgets['help']
		if not self.help_is_displayed:
			self.help_is_displayed = True
			# make game pause if there is a game and we're not in the main menu
			if horizons.main.session is not None and self.current != self.widgets['gamemenu']:
				horizons.main.session.speed_pause()
			self.show_dialog(help_dlg, {'okButton' : True}, onPressEscape = True)
			if horizons.main.session is not None and self.current != self.widgets['gamemenu']:
				horizons.main.session.speed_unpause()
		else:
			self.help_is_displayed = False
			if horizons.main.session is not None and self.current != self.widgets['gamemenu']:
				horizons.main.session.speed_unpause()
			help_dlg.hide()
			self.on_escape = self.show_pause

	def quit_session(self):
		"""Quits the current session"""
		if self.show_dialog(self.widgets['quitsession'],  {'okButton': True, 'cancelButton': False}, onPressEscape=False):
			self.current.hide()
			self.current = None
			horizons.main.session.end()
			horizons.main.session = None
			self.show_main()

	def return_to_game(self):
		"""Return to the horizons."""
		self.hide() # Hide old gui
		self.current = None
		horizons.main.session.speed_unpause()
		self.on_escape = self.show_pause

	@classmethod
	def get_maps(cls, showCampaign = True, showLoad = False):
		""" Gets available maps both for displaying and loading.

		@param showCampaign: Bool, show campaign games true/false
		@param showLoad saves: Bool, show saved games yes/no
		@return: Tuple of two lists; first: files with path; second: files for displaying
		"""
		if showLoad:
			return SavegameManager.get_saves()
		elif showCampaign:
			files = [f for p in ('content/maps',) for f in glob.glob(p + '/*.sqlite') if os.path.isfile(f)]
			files.sort()
			display = [os.path.split(i)[1].rpartition('.')[0] for i in files]
			return (files, display)

	def on_escape(self):
		pass

	def show_multi(self):
		# Remove this after it has been implemented.
		self.show_popup(_("Not yet implemented"), _("Sorry, multiplayer has not been implemented yet."))
		return
		if self.current is not None:
			# delete serverlobby and (Server|Client)Connection
			try:
				self.current.serverlobby.end()
			except AttributeError:
				pass
			self.current.serverlobby = None
			horizons.main.connection = None
			self.current.hide()

		self.current = self.widgets['serverlist']
		center_widget(self.current)
		self.current.server = []
		def _close():
			self.current.serverList.end()
			self.current.serverList = None
			self.show_main()
		event_map = {
			'cancel'  : _close,
			'create'  : self.show_create_server,
			'join'    : self.show_join_server
		}
		self.current.mapEvents(event_map)
		self.current.show()
		self.on_escape = _close
		self.current.oldServerType = None
		self.list_servers()

	def list_servers(self, serverType = 'internet'):
		"""
		@param serverType:
		"""
		self.current.mapEvents({
			'refresh'       : pychan.tools.callbackWithArguments(self.list_servers, serverType),
			'showLAN'       : pychan.tools.callbackWithArguments(self.list_servers, 'lan') if serverType != 'lan' else lambda : None,
			'showInternet'  : pychan.tools.callbackWithArguments(self.list_servers, 'internet') if serverType != 'internet' else lambda : None,
			'showFavorites' : pychan.tools.callbackWithArguments(self.list_servers, 'favorites') if serverType != 'favorites' else lambda : None
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
			servers = []
			for server in self.current.serverList:
				servers.append(str(server))
			self.current.distributeInitialData({'list' : servers})
		_changed()
		self.current.serverList.changed = _changed
		self.current.oldServerType = serverType

	def show_create_server(self):
		"""Interface for creating a server

		Here, the game master can set details about a multiplayer horizons.
		"""
		if self.current is not None:
			self.current.serverList.end()
			self.current.hide()
		self.current = self.widgets['serverlobby']
		center_widget(self.current)

		horizons.main.connection = ServerConnection(horizons.main.settings.network.port)

		self.current.serverlobby = MasterServerLobby(self.current)
		self.current.serverlobby.update_gui()

		def _cancel():
			horizons.main.connection.end()
			self.current.serverlobby.end()
			horizons.main.connection = None
			self.current.serverlobby = None
			self.show_multi()

		self.current.mapEvents({
			'startMulti' : horizons.main.startMulti,
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
			self.show_popup(_('Error'), _('You have to select a server'))
			return
		server = self.current.serverList[server_id]
		self.current.serverList.end()
		self.current.hide()

		horizons.main.connection = ClientConnection()
		horizons.main.connection.join(server.address, server.port)
		self.current = self.widgets['serverlobby']
		center_widget(self.current)
		self.current.serverlobby = ClientServerLobby(self.current)

		def _cancel():
			horizons.main.connection.end()
			self.current.serverlobby.end()
			horizons.main.connection = None
			self.current.serverlobby = None
			self.show_multi()

		self.current.mapEvents({
			'cancel' : _cancel
		})
		self.current.show()
		self.on_escape = self.show_multi

	def _delete_savegame(self, map_files):
		"""Deletes the selected savegame if the user confirms
		self.current has to contain the widget "savegamelist"
		@param map_files: list of files that corresponds to the entries of 'savegamelist'
		@return: True if something was deleted, else False
		"""
		selected_item = self.current.collectData("savegamelist")
		if selected_item == -1:
			self.show_popup(_("No file selected"), _("You need to select a savegame to delete"))
			return False
		selected_file = map_files[selected_item]
		if self.show_popup(_("Confirm deletion"),
											 _('Do you really want to delete the savegame "%s"?') % \
											 SavegameManager.get_savegamename_from_filename(selected_file), \
											 show_cancel_button = True):
			os.unlink(selected_file)
			return True
		else:
			return False

	@staticmethod
	def _create_show_savegame_details(gui, map_files, savegamelist):
		def tmp_show_details():
			"""Fetches details of selected savegame and displays it"""
			box = gui.findChild(name="savegamedetails_box")
			old_label = box.findChild(name="savegamedetails_lbl")
			if old_label is not None:
				box.removeChild(old_label)
			savegame_info = SavegameManager.get_metadata(map_files[gui.collectData(savegamelist)])
			details_label = pychan.widgets.Label(min_size=(140, 0), max_size=(140, 290), wrap_text=True)
			details_label.name = "savegamedetails_lbl"
			details_label.text = u""
			if savegame_info['timestamp'] == -1:
				details_label.text += "Unknown savedate\n"
			else:
				details_label.text += "Saved at %s\n" % \
										 time.strftime("%H:%M, %A, %B %d", time.localtime(savegame_info['timestamp']))
			details_label.text += "Saved %d time%s\n" % (savegame_info['savecounter'], \
			                                             's' if savegame_info['savecounter'] > 1 else '')
			box.addChild( details_label )
			gui.adaptLayout()
		return tmp_show_details

	def hide(self):
		if self.current is not None:
			self.current.hide()

	def show(self):
		if self.current is not None:
			self.current.show()

	def show_select_savegame(self, mode):
		"""Shows menu to select a savegame.
		@param mode: 'save' or 'load'
		@return: Path to savegamefile or None"""
		assert mode in ('save', 'load')
		import pdb ; pdb.set_trace()
		map_files, map_file_display = None, None
		if mode == 'load':
			map_files, map_file_display = SavegameManager.get_saves()
			if len(map_files) == 0:
				self.show_popup(_("No saved games"), _("There are no saved games to load"))
				return
		else: # don't show autosave and quicksave on save
			map_files, map_file_display = SavegameManager.get_regular_saves()

		# Prepare widget
		old_current = self.__switch_current_widget('select_savegame')
		self.current.findChild(name='headline').text = _('Save game') if mode == 'save' else _('Load game')

		""" this doesn't work (yet), see http://fife.trac.cvsdude.com/engine/ticket/375
		if mode == 'save': # only show enter_filename on save
			self.current.findChild(name='enter_filename').show()
		else:
			self.current.findChild(name='enter_filename').hide()
		"""

		def tmp_selected_changed():
			"""Fills in the name of the savegame in the textbox when selected in the list"""
			if self.current.collectData('savegamelist') != -1: # Check if it actually collected valid data
				self.current.distributeData({'savegamefile' : \
				                             map_file_display[self.current.collectData('savegamelist')]})

		self.current.distributeInitialData({'savegamelist' : map_file_display})
		self.current.findChild(name="savegamelist").capture( Callback.ChainedCallbacks( \
		  Gui._create_show_savegame_details(self.current, map_files, 'savegamelist'), \
		  tmp_selected_changed))

		retval = self.show_dialog(self.current, \
		                        {'okButton': True, 'cancelButton': False, 'deleteButton': 'delete'},
														onPressEscape = False)

		if not retval: # canceled
			self.current = old_current
			return

		if retval == 'delete':
			# delete button was pressed. Apply delete and reshow dialog, delegating the return value
			self._delete_savegame(map_files)
			return self.show_select_savegame(mode=mode)

		selected_savegame = None
		if mode == 'save': # return from textfield
			selected_savegame = self.current.collectData('savegamefile')
			if selected_savegame in map_file_display: # savegamename already exists
				if not self.show_popup(_("Confirmation for overwriting"), \
				      _("A savegame with the name \"%s\" already exists. Should i overwrite it?") % \
				      selected_savegame, show_cancel_button = True):
					return self.show_select_savegame(mode=mode) # reshow dialog
		else: # return selected item from list
			selected_savegame = self.current.collectData('savegamelist')
			selected_savegame = None if selected_savegame == -1 else map_files[selected_savegame]
		self.current = old_current # reuse old widget
		return selected_savegame

	def show_loading_screen(self):
		self.hide()
		self.current = self.widgets['loadingscreen']
		center_widget(self.current)
		self.show()

	def toggle_ingame_pause(self):
		"""Called when the hotkey for pause is pressed. Displays pause notification and does
		the acctual (un)pausing."""
		if not horizons.main.session.speed_is_paused():
			horizons.main.session.speed_pause()
			self.on_escape = self.toggle_ingame_pause
			self.widgets['ingame_pause'].mapEvents({'unpause_button': self.toggle_ingame_pause})
			self.widgets['ingame_pause'].show()
		else:
			self.on_escape = self.show_pause
			self.widgets['ingame_pause'].hide()
			horizons.main.session.speed_unpause()

	def toggle_ingame_pdb_start(self):
		"""Called when the hotkey for debug is pressed. Displays only debug notification."""
		pass

	def __switch_current_widget(self, new_widget, center=False, event_map=None, show=False):
		"""Switches self.current to a new widget.
		@param new_widget: str, widget name
		@param center: bool, whether to center the new widget
		@param event_map: pychan event map to apply to new widget
		@param show: bool, if True old window gets hidden and new one shown
		@return: instance of old widget"""
		old = self.current
		if show and old is not None:
			old.hide()
		self.current = self.widgets[new_widget]
		if center:
			center_widget(self.current)
		if event_map:
			self.current.mapEvents(event_map)
		if show:
			self.current.show()
		return old

	def show_single(self, showRandom = False, showCampaign = True):
		"""
		@param showRandom: Bool if random games menu is to be shown.
		@param showCampaign: Bool if  campaigngame menu is to be shown.
		"""
		self.hide() # Hide old gui
		if 'singleplayermenu' in self.widgets:
			del self.widgets['singleplayermenu'] # reload because parts are being removed on each show
		self.__switch_current_widget('singleplayermenu', center=True)
		eventMap = {
			'cancel'   : self.show_main,
			'okay'     : self.start_single,
		}
		if showRandom:
			self.current.removeChild(self.current.findChild(name="load"))
			eventMap['showCampaign'] = pychan.tools.callbackWithArguments(self.show_single, False, True)
			self.current.distributeInitialData({ 'playercolor' : [ i.name for i in Color ] })
			self.current.distributeData({ 'playercolor' : 0 })
		else:
			eventMap['showRandom'] = lambda: self.show_popup(_('Not yet implemented'), _("Sorry, the random map feature isn't yet implemented."))

			# get the map files and their display names
			self.current.files, maps_display = self.get_maps(showCampaign, showLoad=False)
			self.current.distributeInitialData({
				'maplist' : maps_display,
			})
			if len(maps_display) > 0:
				# select first entry
				self.current.distributeData({
					'maplist' : 0,
				})
				eventMap["maplist"] = Gui._create_show_savegame_details(self.current, self.current.files, 'maplist')
		self.current.mapEvents(eventMap)

		self.current.distributeInitialData({
		  'playercolor' : [ color.name for color in Color ],
		  })
		self.current.distributeData({
			'showRandom' : showRandom,
			'showCampaign' : showCampaign,
		  'playername': _("Unknown Player"),
		  'playercolor': 0
		})

		self.current.show()
		self.on_escape = self.show_main

	def start_single(self):
		""" Starts a single player horizons. """
		assert self.current is self.widgets['singleplayermenu']
		showRandom = self.current.collectData('showRandom')
		showCampaign = self.current.collectData('showCampaign')

		game_data = {}
		game_data['playername'] = self.current.collectData('playername')
		if len(game_data['playername']) == 0:
			self.show_popup(_("Invalid player name"), _("You entered an invalid playername"))
			return
		game_data['playercolor'] = Color[self.current.collectData('playercolor')+1] # +1 cause list entries start with 0, color indexes with 1

		if showRandom:
			self.show_popup(_("Not yet implemented"), _("Sorry, random map creation is not implemented at the moment."))
			return
		else:
			map_id = self.current.collectData('maplist')
			if map_id == -1:
				return
			map_file = self.current.files[map_id]

			self.hide()
			self.current = self.widgets['loadingscreen']
			center_widget(self.current)

			horizons.main.start_singleplayer(map_file, game_data)


