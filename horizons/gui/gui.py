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
import time
from fife.extensions import pychan
import logging

import horizons.main

from horizons.savegamemanager import SavegameManager
from horizons.serverlist import WANServerList, LANServerList, FavoriteServerList
from horizons.serverlobby import MasterServerLobby, ClientServerLobby
from horizons.network import ServerConnection, ClientConnection
from horizons.gui.keylisteners import MainListener
from horizons.util import Callback
from horizons.gui.utility import center_widget, LazyWidgetsDict
from horizons.settings import Settings

from horizons.gui.modules import SettingsGui, SingleplayerMenu

class Gui(SettingsGui, SingleplayerMenu):
	"""This class handles all the out of game menu, like the main and pause menu, etc.

	"""
	log = logging.getLogger("gui")

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
		self.widgets = LazyWidgetsDict(self.styles) # access widgets with their filenames without '.xml'
		self.session = None

	def show_main(self):
		"""Shows the main menu """
		self._switch_current_widget('mainmenu', center=True, show=True, event_map = {
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
		"""Shows any pychan dialog.
		@param dlg: dialog that is to be shown
		@param actions: actions that are executed by the dialog { 'ok': callback, 'cancel': callback }
		@param onPressEscape: callback that is to be called if the escape button is pressed.
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		"""
		if event_map is not None:
			dlg.mapEvents(event_map)
		if onPressEscape is not None:
			def _escape():
				pychan.internal.get_manager().breakFromMainLoop(onPressEscape)
				dlg.hide()
			dlg.capture(_escape, event_name="keyPressed")
		ret = dlg.execute(actions)
		return ret

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
		popup.adaptLayout() # recalculate widths
		headline = popup.findChild(name='headline')
		headline.position = ( popup.width/2 - headline.width/2 , headline.position[1] )
		popup.adaptLayout()
		if show_cancel_button:
			return self.show_dialog(popup, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False)
		else:
			return self.show_dialog(popup, {'okButton' : True}, onPressEscape = True)

	def show_pause(self):
		"""
		Show Pause menu
		"""
		self._switch_current_widget('gamemenu', center=True, show=True, event_map={
			'startGame'    : self.return_to_game,
			'closeButton'  : self.quit_session,
			'savegameButton' : horizons.main.save_game,
			'loadgameButton' : horizons.main.load_game,
			'helpLink'	 : self.on_help,
			'settingsLink'   : self.show_settings,
			'dead_link'	 : self.on_chime
		})
		self.session.speed_pause()
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
			if self.session is not None and self.current != self.widgets['gamemenu']:
				self.session.speed_pause()
			self.show_dialog(help_dlg, {'okButton' : True}, onPressEscape = True)
			if self.session is not None and self.current != self.widgets['gamemenu']:
				self.session.speed_unpause()
		else:
			self.help_is_displayed = False
			if self.session is not None and self.current != self.widgets['gamemenu']:
				self.session.speed_unpause()
			help_dlg.hide()
			self.on_escape = self.show_pause

	def quit_session(self):
		"""Quits the current session"""
		if self.show_dialog(self.widgets['quitsession'],  {'okButton': True, 'cancelButton': False}, onPressEscape=False):
			self.current.hide()
			self.current = None
			self.session.end()
			self.session = None

			self.show_main()

	def return_to_game(self):
		"""Return to the horizons."""
		self.hide() # Hide old gui
		self.current = None
		self.session.speed_unpause()
		self.on_escape = self.show_pause

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

		horizons.main.connection = ServerConnection(Settings().network.port)

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
		"""Creates a function that displays details of a savegame in gui"""
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

			"""
			if savegame_info['screenshot']:
				fd, filename = tempfile.mkstemp()
				os.fdopen(fd, "w").write(savegame_info['screenshot'])
				box.addChild( pychan.widgets.Icon(image=filename) )
			"""

			gui.adaptLayout()
		return tmp_show_details

	def hide(self):
		self.log.debug("Gui: hiding current: %s", self.current)
		if self.current is not None:
			self.current.hide()

	def show(self):
		self.log.debug("Gui: showing current: %s", self.current)
		if self.current is not None:
			self.current.show()

	def show_select_savegame(self, mode):
		"""Shows menu to select a savegame.
		@param mode: 'save' or 'load'
		@return: Path to savegamefile or None"""
		assert mode in ('save', 'load')
		map_files, map_file_display = None, None
		if mode == 'load':
			map_files, map_file_display = SavegameManager.get_saves()
			if len(map_files) == 0:
				self.show_popup(_("No saved games"), _("There are no saved games to load"))
				return
		else: # don't show autosave and quicksave on save
			map_files, map_file_display = SavegameManager.get_regular_saves()

		# Prepare widget
		old_current = self._switch_current_widget('select_savegame')
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
				      _("A savegame with the name \"%s\" already exists. \nShould i overwrite it?") % \
				      selected_savegame, show_cancel_button = True):
					return self.show_select_savegame(mode=mode) # reshow dialog
		else: # return selected item from list
			selected_savegame = self.current.collectData('savegamelist')
			selected_savegame = None if selected_savegame == -1 else map_files[selected_savegame]
		self.current = old_current # reuse old widget
		return selected_savegame

	def show_loading_screen(self):
		self._switch_current_widget('loadingscreen', center=True, show=True)

	def _switch_current_widget(self, new_widget, center=False, event_map=None, show=False):
		"""Switches self.current to a new widget.
		@param new_widget: str, widget name
		@param center: bool, whether to center the new widget
		@param event_map: pychan event map to apply to new widget
		@param show: bool, if True old window gets hidden and new one shown
		@return: instance of old widget"""
		old = self.current
		if show and old is not None:
			self.log.debug("Gui: hiding %s", old)
			old.hide()
		self.log.debug("Gui: setting current to %s", new_widget)
		self.current = self.widgets[new_widget]
		if center:
			center_widget(self.current)
		if event_map:
			self.current.mapEvents(event_map)
		if show:
			self.current.show()
		return old
