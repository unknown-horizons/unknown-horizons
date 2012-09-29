# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import hashlib
import logging
import textwrap

from fife.extensions.pychan.widgets import HBox, Icon, Label

from horizons.gui.modules import PlayerDataSelection
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.savegamemanager import SavegameManager
from horizons.network.networkinterface import MPGame
from horizons.constants import MULTIPLAYER
from horizons.network.networkinterface import NetworkInterface
from horizons.network import find_enet_module
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.util.color import Color
from horizons.util.python.callback import Callback
from horizons.util.savegameaccessor import SavegameAccessor

enet = find_enet_module()

class MultiplayerMenu(object):
	log = logging.getLogger("networkinterface")

	def show_multi(self):
		"""Shows main multiplayer menu"""
		if enet == None:
			headline = _(u"Unable to find pyenet")
			descr = _(u'The multiplayer feature requires the library "pyenet", '
			          u"which could not be found on your system.")
			advice = _(u"Linux users: Try to install pyenet through your package manager.")
			self.show_error_popup(headline, descr, advice)
			return

		if NetworkInterface() is None:
			try:
				NetworkInterface.create_instance()
			except RuntimeError as e:
				headline = _(u"Failed to initialize networking.")
				descr = _("Network features could not be initialized with the current configuration.")
				advice = _("Check the settings you specified in the network section.")
				self.show_error_popup(headline, descr, advice, unicode(e))
				return

		if not NetworkInterface().isconnected():
			connected = self.__connect_to_server()
			if not connected:
				return

		if NetworkInterface().isjoined():
			if not NetworkInterface().leavegame():
				return

		event_map = {
			'cancel'  : self.__cancel,
			'join'    : self.__join_game,
			'create'  : self.__show_create_game,
			'load'    : self.__show_load_game,
			'refresh' : Callback(self.__refresh, play_sound=True)
		}
		# store old name and color
		self.__apply_new_nickname()
		self.__apply_new_color()
		# reload because changing modes (not yet implemented) will need it
		self.widgets.reload('multiplayermenu')
		self._switch_current_widget('multiplayermenu', center=True, event_map=event_map, hide_old=True)

		refresh_worked = self.__refresh()
		if not refresh_worked:
			self.show_main()
			return
		self.current.findChild(name='gamelist').capture(self.__update_game_details)
		self.current.findChild(name='showonlyownversion').capture(self.__show_only_own_version_toggle)
		self.current.playerdata = PlayerDataSelection(self.current, self.widgets)

		self.current.show()

		self.on_escape = event_map['cancel']

	def create_default_mp_game(self):
		"""For debugging; creates a valid game. Call right after show_multi"""
		self.__show_create_game()
		#self.current.distributeData({'playerlimit': 1})
		#self.current.distributeData({'playerlimit': 1}) # TODO remove
		self.__create_game(chosen_map='mp-dev')
		self.__toggle_ready()

	def join_mp_game(self):
		"""For debugging; joins first open game. Call right after show_multi"""
		self.__join_game()
		self.__toggle_ready()

	def __connect_to_server(self):
		NetworkInterface().register_chat_callback(self.__receive_chat_message)
		NetworkInterface().register_game_prepare_callback(self.__prepare_game)
		NetworkInterface().register_game_starts_callback(self.__start_game)
		NetworkInterface().register_error_callback(self._on_error)

		NetworkInterface().register_game_terminated_callback(self.__game_terminated)
		NetworkInterface().register_game_details_changed_callback(self.__update_game_details)
		NetworkInterface().register_player_joined_callback(self.__player_joined)
		NetworkInterface().register_player_left_callback(self.__player_left)
		NetworkInterface().register_player_changed_name_callback(self.__player_changed_name)
		NetworkInterface().register_player_changed_color_callback(self.__player_changed_color)
		NetworkInterface().register_player_toggle_ready_callback(self.__player_toggled_ready)
		NetworkInterface().register_kick_callback(self.__player_kicked)

		NetworkInterface().register_player_fetch_game_callback(self.__fetch_game) #TODO

		try:
			NetworkInterface().connect()
		except Exception as err:
			headline = _(u"Fatal Network Error")
			descr = _(u"Could not connect to master server.")
			advice = _(u"Please check your Internet connection. If it is fine, "
			           u"it means our master server is temporarily down.")
			self.show_error_popup(headline, descr, advice, unicode(err))
			return False
		return True

	def _on_error(self, exception, fatal=True):
		"""Error callback"""
		if fatal and self.session is not None:
			self.session.timer.ticks_per_second = 0
		if self.dialog_executed:
			# another message dialog is being executed, and we were called by that action.
			# if we now trigger another message dialog, we will probably loop.
			return
		if not fatal:
			self.show_popup(_("Error"), unicode(exception))
		else:
			self.show_popup(_("Fatal Network Error"),
		                 _("Something went wrong with the network:") + u'\n' +
		                 unicode(exception) )
			self.quit_session(force=True)

	def __cancel(self):
		if NetworkInterface().isconnected():
			NetworkInterface().disconnect()
		self.__apply_new_nickname()
		self.__apply_new_color()
		self.show_main()

	def __player_kicked(self, game, player, myself):
		if myself:
			self.show_popup(_("Kicked"), _("You have been kicked from the game by creator"))
			self.show_multi()
		else:
			self.__print_event_message(_("{player} got kicked by creator").format(player=player.name))

	def __game_terminated(self, game, errorstr):
		self.show_popup(_("Terminated"), errorstr)
		self.show_multi()

	def _display_game_name(self, game):
		same_version = game.get_version() == NetworkInterface().get_clientversion()
		template = u"{password}{gamename}: {name} ({players}, {limit}){version}"
		return template.format(
			password="(Password!) " if game.has_password() else "",
			name=game.get_map_name(),
			gamename=game.get_name(),
			players=game.get_player_count(),
			limit=game.get_player_limit(),
			version=u" " + _("Version differs!") if not same_version else u"")

	def __refresh(self, play_sound=False):
		"""Refresh list of games.
		Only possible in multiplayer main menu state.
		@param play_sound: whether to play the refresh sound
		@return bool, whether refresh worked"""
		if play_sound:
			AmbientSoundComponent.play_special('refresh')
		only_this_version_allowed = self.current.findChild(name='showonlyownversion').marked
		self.games = NetworkInterface().get_active_games(only_this_version_allowed)
		if self.games is None:
			return False

		gamelist = [self._display_game_name(g) for g in self.games]
		self.current.distributeInitialData({'gamelist': gamelist})
		self.current.distributeData({'gamelist': 0}) # select first map
		self.__update_game_details()
		return True

	def __get_selected_game(self):
		try:
			if NetworkInterface().isjoined():
				return NetworkInterface().get_game()
			else:
				index = self.current.collectData('gamelist')
				return self.games[index]
		except:
			return None

	def __show_only_own_version_toggle(self):
		self.__refresh()

	def __update_game_details(self, game=None):
		"""Set map name and other misc data in a widget. Only possible in certain states"""
		if game is None:
			game = self.__get_selected_game()
			if game is None:
				return
		#xgettext:python-format
		self.current.findChild(name="game_map").text = _("Map: {map_name}").format(map_name=game.get_map_name())
		self.current.findChild(name="game_name").text = _("Name: {game_name}").format(game_name=game.get_name())
		self.current.findChild(name="game_creator").text = _("Creator: {game_creator}").format(game_creator=game.get_creator())
		#xgettext:python-format
		self.current.findChild(name="game_playersnum").text = _("Players: {player_amount}/{player_limit}").format(
		                           player_amount=game.get_player_count(),
		                           player_limit=game.get_player_limit())
		vbox_inner = self.current.findChild(name="game_info")
		if game.is_savegame(): # work around limitations of current systems via messages
			path = SavegameManager.get_multiplayersave_map(game.mapname)
			btn_name = "save_missing_help_button"
			btn = vbox_inner.findChild(name=btn_name)
			if SavegameAccessor.get_hash(path) != game.get_map_hash():
				text = ""
				if btn is None:
					btn = Button(name=btn_name)
					btn.text = _("This savegame is missing (click here)")
					last_elem = vbox_inner.findChild(name="game_info_last")
					if last_elem is None: # no last elem -> we are last
						vbox_inner.addChild( btn )
					else:
						vbox_inner.insertChildBefore( btn, last_elem )
				btn_text = _(u"For multiplayer load, it is necessary for you to have the correct savegame file.") + u"\n"
				btn_text += _(u"The file will be downloaded when the game starts.")
				btn.btn_text = btn_text
				def show():
					self.show_popup(_("Help"), btn_text, size=1)
				btn.capture(show)

			else:
				text = _(u"This is a savegame.")
				if btn is not None:
					btn.hide()

			if text:
				self.current.findChild(name="game_isloaded").text = text

		self.__update_players_box(game)

		vbox_inner.adaptLayout() # inner vbox always exists
		vbox = self.current.findChild(name="gamedetailsbox")
		if vbox is not None:
			vbox.adaptLayout()

	def __actual_join(self, game=None, password=""):
		"""Does the actual joining to the game.

		 This method is called after everything is OK for joining."""
		if game is None:
			return False

		self.__apply_new_nickname()
		self.__apply_new_color()

		fetch = False
		if game.is_savegame() and SavegameAccessor.get_hash(SavegameManager.get_multiplayersave_map(game.mapname)) != game.get_map_hash():
			fetch = True

		if not NetworkInterface().joingame(game.get_uuid(), password, fetch):
			return False
		self.__show_gamelobby()
		return True

	def __join_game(self, game=None):
		"""Joins a multiplayer game. Displays lobby for that specific game"""
		if game == None:
			game = self.__get_selected_game()
		if game is None:
			return
		if game.get_uuid() == -1: # -1 signals no game
			AmbientSoundComponent.play_special('error')
			return
		if game.get_version() != NetworkInterface().get_clientversion():
			self.show_popup(_("Wrong version"),
			                   #xgettext:python-format
			                _("The game's version differs from your version. Every player in a multiplayer game must use the same version. This can be fixed by every player updating to the latest version. Game version: {game_version} Your version: {own_version}").format(
			                  game_version=game.get_version(),
			                  own_version=NetworkInterface().get_clientversion()))
			return

		# actual join
		if game.password:
			self.__enter_password_dialog(game)

		else:
			self.__actual_join(game)


	def __enter_password_dialog(self, game):
		"""Shows a dialog where the player can enter the password"""
		set_password_dialog = self.widgets['set_password']
		def _enter_password():
			password = hashlib.sha1(set_password_dialog.collectData("password")).hexdigest()
			if self.__actual_join(game, password):
				set_password_dialog.hide()

		def _cancel():
			set_password_dialog.hide()

		events = {
			OkButton.DEFAULT_NAME: _enter_password,
			CancelButton.DEFAULT_NAME: _cancel
		}
		self.on_escape = _cancel

		password = set_password_dialog.findChild(name='password')
		password.text = u""
		set_password_dialog.mapEvents(events)
		set_password_dialog.show()
		password.capture(_enter_password)

	def __prepare_game(self, game):
		self._switch_current_widget('loadingscreen', center=True, show=True)
		# send map data
		# NetworkClient().sendmapdata(...)
		import horizons.main
		horizons.main.prepare_multiplayer(game)

	def __start_game(self, game):
		import horizons.main
		horizons.main.start_multiplayer(game)

	def __toggle_ready(self):
		game = NetworkInterface().get_game()
		NetworkInterface().toggle_ready()

	def __show_gamelobby(self):
		"""Shows lobby (gui for waiting until all players have joined). Allows chatting"""
		game = self.__get_selected_game()
		event_map = {
			'cancel' : self.show_multi,
			'ready_btn' : self.__toggle_ready,
		}
		self.widgets.reload('multiplayer_gamelobby') # remove old chat messages, etc
		self._switch_current_widget('multiplayer_gamelobby', center=True, event_map=event_map, hide_old=True)

		self.__update_game_details(game)

		textfield = self.current.findChild(name="chatTextField")
		textfield.capture(self.__send_chat_message)
		textfield.capture(self.__chatfield_onfocus, 'mouseReleased', 'default')
		self.current.show()

		self.on_escape = event_map['cancel']

	def __apply_new_nickname(self):
		if hasattr(self.current, 'playerdata'):
			playername = self.current.playerdata.get_player_name()
			NetworkInterface().change_name(playername)

	def __apply_new_color(self):
		if hasattr(self.current, 'playerdata'):
			playercolor = self.current.playerdata.get_player_color()
			NetworkInterface().change_color(playercolor.id)

	def __chatfield_onfocus(self):
		textfield = self.current.findChild(name="chatTextField")
		textfield.text = u""
		textfield.capture(None, 'mouseReleased', 'default')

	def __send_chat_message(self):
		"""Sends a chat message. Called when user presses enter in the input field"""
		msg = self.current.findChild(name="chatTextField").text
		if msg:
			self.current.findChild(name="chatTextField").text = u""
			NetworkInterface().chat(msg)

	def __receive_chat_message(self, game, player, msg):
		"""Receive a chat message from the network. Only possible in lobby state"""
		line_max_length = 40
		chatbox = self.current.findChild(name="chatbox")
		full_msg = u""+ player + ": "+msg
		lines = textwrap.wrap(full_msg, line_max_length)
		for line in lines:
			chatbox.items.append(line)
		chatbox.selected = len(chatbox.items) - 1

	def __print_event_message(self, msg):
		line_max_length = 40
		chatbox = self.current.findChild(name="chatbox")
		full_msg = u"* " + msg + " *"
		lines = textwrap.wrap(full_msg, line_max_length)
		for line in lines:
			chatbox.items.append(line)
		chatbox.selected = len(chatbox.items) - 1

	def __player_joined(self, game, player):
		self.__print_event_message(_("{player} has joined the game").format(player=player.name))

	def __player_left(self, game, player):
		self.__print_event_message(_("{player} has left the game").format(player=player.name))

	def __player_toggled_ready(self, game, plold, plnew, myself):
		self.__update_players_box(NetworkInterface().get_game())
		if myself:
			if plnew.ready:
				self.__print_event_message(_("You are now ready"))
			else:
				self.__print_event_message(_("You are not ready anymore"))
		else:
			if plnew.ready:
				self.__print_event_message(_("{player} is now ready").format(player=plnew.name))
			else:
				self.__print_event_message(_("{player} not ready anymore").format(player=plnew.name))

	def __player_changed_name(self, game, plold, plnew, myself):
		if myself:
			self.__print_event_message(_("You are now known as {new_name}").format(new_name=plnew.name))
		else:
			self.__print_event_message(_("{player} is now known as {new_name}").format(player=plold.name, new_name=plnew.name))

	def __player_changed_color(self, game, plold, plnew, myself):
		if myself:
			self.__print_event_message(_("You changed your color"))
		else:
			self.__print_event_message(_("{player} changed its color").format(player=plnew.name))

	def __fetch_game(self, game):
		self.__print_event_message(_("You fetched the savegame data"))
		self.__update_game_details()

	def __show_create_game(self):
		"""Shows the interface for creating a multiplayer game"""
		event_map = {
			'cancel' : self.show_multi,
			'create' : self.__create_game
		}
		self.__apply_new_nickname()
		self.__apply_new_color()
		self._switch_current_widget('multiplayer_creategame', center=True, event_map=event_map, hide_old=True)

		self.current.files, self.maps_display = SavegameManager.get_maps()
		self.current.distributeInitialData({
			'maplist' : self.maps_display,
			'playerlimit' : range(2, MULTIPLAYER.MAX_PLAYER_COUNT)
		})
		def _update_infos():
			mapindex = self.current.collectData('maplist')
			mapfile = self.current.files[mapindex]
			number_of_players = SavegameManager.get_recommended_number_of_players(mapfile)
			#xgettext:python-format
			self.current.findChild(name="recommended_number_of_players_lbl").text = \
					_("Recommended number of players: {number}").format(number=number_of_players)
		if self.maps_display: # select first entry
			self.current.distributeData({
				'maplist' : 0,
				'playerlimit' : 0
			})
			_update_infos()
		self.current.findChild(name="maplist").mapEvents({
		  'maplist/action': _update_infos
		})
		self.current.findChild(name="password").text = u""
		gamename_textfield = self.current.findChild(name="gamename")
		def clear_gamename_textfield():
			gamename_textfield.text = u""
		gamename_textfield.capture(clear_gamename_textfield, 'mouseReleased', 'default')

		self.current.show()

		self.on_escape = event_map['cancel']

	def __show_load_game(self):
		ret = self.show_select_savegame(mode='mp_load')
		if ret is None: # user aborted
			return
		path, gamename, gamepassword = ret
		# get name from path
		paths, names = SavegameManager.get_multiplayersaves()
		mapname = names[paths.index(path)]
		self.__create_game(load=(mapname, gamename, gamepassword))


	def __create_game(self, load=None, chosen_map=None):
		"""
		Actually create a game, join it, and display the lobby.

		@param load: game data tuple for creating loaded games
		@param chosen_map: the name of the map to start a new game on (overrides the gui)
		"""
		# create the game
		if load:
			mapname, gamename, gamepassword = load
			path = SavegameManager.get_multiplayersave_map(mapname)
			maxplayers = SavegameAccessor.get_players_num(path)
			password = gamepassword
			maphash = SavegameAccessor.get_hash(path)
		else:
			mapindex = None
			if chosen_map is not None:
				for i, map in enumerate(self.maps_display):
					if map == chosen_map:
						mapindex = i
						break

			if mapindex is None:
				mapindex = self.current.collectData('maplist')
			mapname = self.maps_display[mapindex]
			maxplayers = self.current.collectData('playerlimit') + 2 # 1 is the first entry
			gamename = self.current.collectData('gamename')
			password = self.current.collectData('password')
			maphash = ""


		password = hashlib.sha1(password).hexdigest() if password != "" else ""
		game = NetworkInterface().creategame(mapname, maxplayers, gamename, maphash, password)
		if game is None:
			return

		self.__show_gamelobby()

	def __update_players_box(self, game=None):
		"""Updates player list in game lobby.

		This function is called when there is a change in players (or their attributes.
		Uses players_vbox in multiplayer_gamelobby.xml and creates a hbox for each player.

		Also adds kick button for game creator."""
		if not game:
			return

		players_vbox = self.current.findChild(name="players_vbox")

		#if we are not in game lobby then return
		if not players_vbox:
			return

		players_vbox.removeAllChildren()

		gicon = Icon(name="gslider", image="content/gui/images/background/hr.png")
		players_vbox.addChild(gicon)

		def _add_player_line(player):
			pname = Label(name="pname_%s" % player['name'])
			pname.helptext = _("Click here to change your name and/or color")
			pname.text = player['name']
			if player['name'] == NetworkInterface().get_client_name():
				pname.capture(Callback(self.__show_change_player_details_popup))
			pname.min_size = pname.max_size = (130, 15)

			pcolor = Label(name="pcolor_%s" % player['name'], text=u"   ")
			pcolor.helptext = _("Click here to change your name and/or color")
			pcolor.background_color = player['color']
			if player['name'] == NetworkInterface().get_client_name():
				pcolor.capture(Callback(self.__show_change_player_details_popup))
			pcolor.min_size = pcolor.max_size = (15, 15)

			pstatus = Label(name="pstatus_%s" % player['name'])
			pstatus.text = "\t\t\t" + player['status']
			pstatus.min_size = pstatus.max_size = (120, 15)

			picon = Icon(name="picon_%s" % player['name'])
			picon.image = "content/gui/images/background/hr.png"

			hbox = HBox()
			hbox.addChild(pname)
			hbox.addChild(pcolor)
			hbox.addChild(pstatus)

			if NetworkInterface().get_client_name() == game.get_creator() and player['name'] != game.get_creator():
				pkick = CancelButton(name="pkick_%s" % player['name'], helptext=_("Kick {player}").format(player=player['name']))
				pkick.capture(Callback(NetworkInterface().kick, player['sid']))
				pkick.up_image = "content/gui/images/buttons/delete_small.png"
				pkick.down_image = "content/gui/images/buttons/delete_small.png"
				pkick.hover_image = "content/gui/images/buttons/delete_small_h.png"
				pkick.min_size = pkick.max_size = (20, 15)
				hbox.addChild(pkick)

			players_vbox.addChild(hbox)
			players_vbox.addChild(picon)

		for player in game.get_player_list():
			_add_player_line(player)

		players_vbox.adaptLayout()

	def __show_change_player_details_popup(self):
		"""Shows a dialog where the player can change its name and/or color"""

		def _get_unused_colors():
			"""Returns unused colors list in a game """

			assigned = [p["color"] for p in NetworkInterface().get_game().get_player_list()  if p["name"] != NetworkInterface().get_client_name() ]
			available = set(Color) - set(assigned)
			return available

		set_player_details_dialog = self.widgets['set_player_details']
		#remove all children of color and name pop-up and then show them
		set_player_details_dialog.findChild(name="playerdataselectioncontainer").removeAllChildren()
		#assign playerdata to self.current.playerdata to use self.__apply_new_color() and __apply_new_nickname()
		self.current.playerdata = PlayerDataSelection(set_player_details_dialog, self.widgets, color_palette=_get_unused_colors())
		self.current.playerdata.set_player_name(NetworkInterface().get_client_name())
		self.current.playerdata.set_color(NetworkInterface().get_client_color())

		def _change_playerdata():
			self.__apply_new_nickname()
			self.__apply_new_color()
			set_player_details_dialog.hide()
			self.__update_game_details()

		def _cancel():
			set_player_details_dialog.hide()

		events = {
			OkButton.DEFAULT_NAME: _change_playerdata,
			CancelButton.DEFAULT_NAME: _cancel
		}
		self.on_escape = _cancel

		set_player_details_dialog.mapEvents(events)
		set_player_details_dialog.show()
