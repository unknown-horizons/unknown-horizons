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

import logging
import os.path
import textwrap
from fife.extensions import pychan

from horizons.gui.modules import PlayerDataSelection
from horizons.savegamemanager import SavegameManager
from horizons.network.networkinterface import MPGame
from horizons.constants import MULTIPLAYER
from horizons.network.networkinterface import NetworkInterface
from horizons.network import find_enet_module
from horizons.util import SavegameAccessor
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent

enet = find_enet_module()

class MultiplayerMenu(object):
	log = logging.getLogger("networkinterface")

	def show_multi(self):
		"""Shows main multiplayer menu"""
		if enet == None:
			headline = _(u"Unable to find pyenet")
			descr = _(u"The multiplayer feature requires the library \"pyenet\", which couldn't be found on your system.")
			advice = _(u"Linux users: Try to install pyenet through your package manager.") + "\n" + \
						 _(u"Windows users: There is currently no reasonable support for Windows.")
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
			'refresh' : self.__refresh,
		}
		# store old name and color
		self.__apply_new_nickname()
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
		self.__create_game(chosen_map = 'mp-dev')

	def join_mp_game(self):
		"""For debugging; joins first open game. Call right after show_multi"""
		self.__join_game()

	def __connect_to_server(self):
		NetworkInterface().register_chat_callback(self.__receive_chat_message)
		NetworkInterface().register_game_details_changed_callback(self.__update_game_details)
		NetworkInterface().register_game_prepare_callback(self.__prepare_game)
		NetworkInterface().register_game_starts_callback(self.__start_game)
		NetworkInterface().register_error_callback(self._on_error)
		NetworkInterface().register_player_joined_callback(self.__player_joined)
		NetworkInterface().register_player_left_callback(self.__player_left)
		NetworkInterface().register_player_changed_name_callback(self.__player_changed_name)

		try:
			NetworkInterface().connect()
		except Exception as err:
			headline = _(u"Fatal Network Error")
			descr = _(u"Could not connect to master server.")
			advice = _(u"Please check your Internet connection. If it is fine, it means our master server is temporarily down.")
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
			self.show_popup(_("Fatal Network Error"), \
		                 _("Something went wrong with the network:") + u'\n' + \
		                 unicode(exception) )
			self.quit_session(force=True)

	def __cancel(self):
		if NetworkInterface().isconnected():
			NetworkInterface().disconnect()
		self.__apply_new_nickname()
		self.show_main()

	def __refresh(self):
		"""Refresh list of games.
		Only possible in multiplayer main menu state.
		@return bool, whether refresh worked"""
		self.games = NetworkInterface().get_active_games(self.current.findChild(name='showonlyownversion').marked)
		if self.games is None:
			return False

		self.current.distributeInitialData(
		  {'gamelist' : map(lambda x: "{gamename}: {name} ({players}, {limit}){version}".format(
		                        name=x.get_map_name(),
		                        gamename=x.get_name(),
		                        players=x.get_player_count(),
		                        limit=x.get_player_limit(),
		                        version=" " + _("Version differs!") if x.get_version() != NetworkInterface().get_clientversion() else ""),
		                    self.games)})
		self.current.distributeData({'gamelist' : 0}) # select first map
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
			return MPGame(-1, "", "", 0, 0, [], "", -1, "", False)

	def __show_only_own_version_toggle(self):
		self.__refresh()

	def __update_game_details(self, game = None):
		"""Set map name and other misc data in a widget. Only possible in certain states"""
		if game == None:
			game = self.__get_selected_game()
		#xgettext:python-format
		self.current.findChild(name="game_map").text = _("Map: {map_name}").format(map_name=game.get_map_name())
		self.current.findChild(name="game_name").text = _("Name: {game_name}").format(game_name=game.get_name())
		#xgettext:python-format
		self.current.findChild(name="game_playersnum").text =  _("Players: {player_amount}/{player_limit}").format(
		                           player_amount=game.get_player_count(),
		                           player_limit=game.get_player_limit())
		creator_text = self.current.findChild(name="game_creator")
		#xgettext:python-format
		creator_text.text = _("Creator: {player}").format(player=game.get_creator())
		creator_text.adaptLayout()
		vbox_inner = self.current.findChild(name="game_info")
		if game.load is not None: # work around limitations of current systems via messages
			path = SavegameManager.get_multiplayersave_map(game.mapname)
			if SavegameAccessor.get_hash(path) != game.load:
				text = ""
				btn_name = "save_missing_help_button"
				btn = vbox_inner.findChild(name=btn_name)
				if btn is None:
					btn = pychan.widgets.Button(name=btn_name,
					                            text=_("This savegame is missing (click here)"))
					last_elem = vbox_inner.findChild(name="game_info_last")
					if last_elem is None: # no last elem -> we are last
						vbox_inner.addChild( btn )
					else:
						vbox_inner.insertChildBefore( btn, last_elem )
				btn_text = _(u"For multiplayer load, it is currently necessary for you to ensure you have the correct savegame file.") + u"\n"
				btn_text += _(u"This is not nice and we hope to offer a more convenient solution very soon.") + u"\n"
				btn_text += _(u"Meanwhile, please request the file {path} from the game creator and put it in {map_directory} .").format(path=os.path.basename(path), map_directory=os.path.dirname(path))
				btn.btn_text = btn_text
				def show():
					self.show_popup(_("Help"), btn_text, size=1)
				btn.capture(show)

			else:
				text = _(u"This is a savegame.")

			if text:
				self.current.findChild(name="game_isloaded").text = text
		textplayers = self.current.findChild(name="game_players")
		if textplayers is not None:
			textplayers.text = u", ".join(game.get_players())

		vbox_inner.adaptLayout() # inner vbox always exists
		vbox = self.current.findChild(name="gamedetailsbox")
		if vbox is not None:
			vbox.adaptLayout()

	def __join_game(self, game = None):
		"""Joins a multiplayer game. Displays lobby for that specific game"""
		if game == None:
			game = self.__get_selected_game()
		if game.load is not None and SavegameAccessor.get_hash(SavegameManager.get_multiplayersave_map(game.mapname)) != game.load:
			self.show_popup(_("Error"), self.current.findChild(name="save_missing_help_button").btn_text, size=1)
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
		join_worked = NetworkInterface().joingame(game.get_uuid())
		if not join_worked:
			return
		self.__apply_new_nickname()
		self.__show_gamelobby()

	def __prepare_game(self, game):
		self._switch_current_widget('loadingscreen', center=True, show=True)
		import horizons.main
		horizons.main.prepare_multiplayer(game)

	def __start_game(self, game):
		import horizons.main
		horizons.main.start_multiplayer(game)

	def __show_gamelobby(self):
		"""Shows lobby (gui for waiting until all players have joined). Allows chatting"""
		event_map = {
			'cancel' : self.show_multi,
		}
		game = self.__get_selected_game()
		self.widgets.reload('multiplayer_gamelobby') # remove old chat messages, etc
		self._switch_current_widget('multiplayer_gamelobby', center=True, event_map=event_map, hide_old=True)

		self.__update_game_details(game)
		self.current.findChild(name="game_players").text = u", ".join(game.get_players())
		textfield = self.current.findChild(name="chatTextField")
		textfield.capture(self.__send_chat_message)
		textfield.capture(self.__chatfield_onfocus, 'mouseReleased', 'default')
		self.current.show()

		self.on_escape = event_map['cancel']

	def __apply_new_nickname(self):
		if hasattr(self.current, 'playerdata'):
			playername = self.current.playerdata.get_player_name()
			NetworkInterface().change_name(playername)

	def __chatfield_onfocus(self):
		textfield = self.current.findChild(name="chatTextField")
		textfield.text = u""
		textfield.capture(None, 'mouseReleased', 'default')

	def __send_chat_message(self):
		"""Sends a chat message. Called when user presses enter in the input field"""
		msg = self.current.findChild(name="chatTextField").text
		if len(msg):
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
		self.__print_event_message(u"{player} has joined the game".format(player=player.name))

	def __player_left(self, game, player):
		self.__print_event_message(u"{player} has left the game".format(player=player.name))

	def __player_changed_name(self, game, plold, plnew, myself):
		if myself:
			self.__print_event_message(u"You are now known as {new_name}".format(new_name=plnew.name))
		else:
			self.__print_event_message(u"{player} is now known as {new_name}".format(player=plold.name, new_name=plnew.name))

	def __show_create_game(self):
		"""Shows the interface for creating a multiplayer game"""
		event_map = {
			'cancel' : self.show_multi,
			'create' : self.__create_game
		}
		self.__apply_new_nickname()
		self._switch_current_widget('multiplayer_creategame', center=True, event_map=event_map, hide_old=True)

		self.current.files, self.maps_display = SavegameManager.get_maps()
		self.current.distributeInitialData({
			'maplist' : self.maps_display,
			'playerlimit' : range(2, MULTIPLAYER.MAX_PLAYER_COUNT)
		})
		def _update_infos():
			mapindex = self.current.collectData('maplist')
			mapfile = self.current.files[mapindex]
			number_of_players = SavegameManager.get_recommended_number_of_players( mapfile )
			#xgettext:python-format
			self.current.findChild(name="recommended_number_of_players_lbl").text = \
					_("Recommended number of players: {number}").format(number=number_of_players)
		if len(self.maps_display) > 0: # select first entry
			self.current.distributeData({
				'maplist' : 0,
				'playerlimit' : 0
			})
			_update_infos()
		self.current.findChild(name="maplist").mapEvents({
		  'maplist/action': _update_infos,
		  'maplist/mouseWheelMovedUp'   : _update_infos,
		  'maplist/mouseWheelMovedDown' : _update_infos
		})

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
		path, gamename = ret
		# get name from path
		paths, names = SavegameManager.get_multiplayersaves()
		mapname = names[paths.index(path)]
		self.__create_game(load=(mapname, gamename))


	def __create_game(self, load=None, chosen_map=None):
		"""
		Actually create a game, join it, and display the lobby.
		
		@param load: game data tuple for creating loaded games
		@param chosen_map: the name of the map to start a new game on (overrides the gui)
		"""
		# create the game
		if load:
			mapname, gamename = load
			path = SavegameManager.get_multiplayersave_map(mapname)
			maxplayers = SavegameAccessor.get_players_num(path)
			load = SavegameAccessor.get_hash(path)
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
			load = None

		game = NetworkInterface().creategame(mapname, maxplayers, gamename, load)
		if game is None:
			return

		self.__show_gamelobby()

