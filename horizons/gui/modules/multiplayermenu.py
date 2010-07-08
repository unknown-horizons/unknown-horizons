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

from time import strftime
import logging

from horizons.gui.modules import PlayerDataSelection
from horizons.savegamemanager import SavegameManager
from horizons.network.networkinterface import MPGame
from horizons.constants import MULTIPLAYER
from horizons.network.networkinterface import NetworkInterface
from horizons.util import Callback
from horizons.network import CommandError


class MultiplayerMenu(object):
	log = logging.getLogger("networkinterface")

	def show_multi(self):
		"""Shows main multiplayer menu"""
		if not NetworkInterface().isconnected():
			NetworkInterface().register_chat_callback(self.__receive_chat_message)
			NetworkInterface().register_game_details_changed_callback(self.__update_game_details)
			NetworkInterface().register_game_starts_callback(self.__start_game)
			NetworkInterface().register_game_ready_callback(self.__game_ready)
			NetworkInterface().register_error_callback(self.__on_error)

			try:
				NetworkInterface().connect()
			except Exception, err:
				self.show_popup("Network Error", "Could not connect to master server. Details: %s" % str(err))
				return

		if NetworkInterface().isjoined():
			if not NetworkInterface().leavegame():
				return

		event_map = {
			'cancel'  : self.__cancel,
			'join'    : self.__join_game,
			'create'  : self.__show_create_game,
			'refresh' : self.__refresh,
		}
		self.widgets.reload('multiplayermenu')
		self._switch_current_widget('multiplayermenu', center=True, event_map=event_map, hide_old=True)

		refresh_worked = self.__refresh()
		if not refresh_worked:
			self.show_main()
			return
		self.current.findChild(name='gamelist').capture(self.__update_game_details)

		#self.current.playerdata = PlayerDataSelection(self.current, self.widgets)
		self.current.show()

		self.on_escape = event_map['cancel']

	def __on_error(self, exception):
		if self.session is not None:
			self.session.timer.ticks_per_second = 0
		self.show_popup( _("Network Error"), \
		                 _("Something went wrong with the network: ") + \
		                 str(exception) )
		self.quit_session(force=True)

	def __cancel(self):
		NetworkInterface().disconnect()
		self.show_main()

	def __refresh(self):
		"""Refresh list of games.
		Only possible in multiplayer main menu state.
		@return bool, whether refresh worked"""
		self.games = NetworkInterface().get_active_games()
		if self.games is None:
			return False
		self.current.distributeInitialData({'gamelist' : map(lambda x: "%s (%u, %u)"%(x.get_map_name(), x.get_player_count(), x.get_player_limit()), self.games)})
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
			return MPGame(-1, "", "", 0, 0, [], "")

	def __update_game_details(self, game = None):
		"""Set map name and other misc data in a widget. Only possible in certain states"""
		if game == None:
			game = self.__get_selected_game()
		self.current.findChild(name="game_map").text = _(u"Map: ") + game.get_map_name()
		self.current.findChild(name="game_playersnum").text =  _(u"Players: ") + \
			unicode(game.get_player_count()) + u"/" + unicode(game.get_player_limit())
		creator_text = self.current.findChild(name="game_creator")
		creator_text.text = u"Creator: " + unicode(game.get_creator())
		creator_text.adaptLayout()
		textplayers = self.current.findChild(name="game_players")
		if textplayers is not None:
			textplayers.text = u", ".join(game.get_players())

		vbox = self.current.findChild(name="gamedetailsbox")
		if vbox is not None:
			vbox.adaptLayout()

	def __join_game(self, game = None):
		"""Joins a multiplayer game. Displays lobby for that specific game"""
		if game == None:
			game = self.__get_selected_game()
		if game.get_uuid() == -1: # -1 signals no game
			return

		if True: # TODO: acctual join + check for player name and color duplicates
			join_worked = NetworkInterface().joingame(game.get_uuid())
			if not join_worked:
				return
			self.__show_gamelobby()

	def __start_game(self, game):
		self._switch_current_widget('loadingscreen', center=True, show=True)
		import horizons.main
		horizons.main.prepare_multiplayer(game)

	def __game_ready(self, game):
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

	def __chatfield_onfocus(self):
		textfield = self.current.findChild(name="chatTextField")
		textfield.text = u""
		textfield.capture(None, 'mouseReleased', 'default')

	def __send_chat_message(self):
		"""Sends a chat message. Called when user presses enter in the input field"""
		msg = self.current.findChild(name="chatTextField").text
		self.current.findChild(name="chatTextField").text = u""
		NetworkInterface().chat(msg)

	def __receive_chat_message(self, game, player, msg):
		"""Receive a chat message from the network. Only possible in lobby state"""
		chatbox = self.current.findChild(name="chatbox")
		chatbox.items.append(u"("+strftime("%H:%M:%S")+") "+ player + ": "+msg)
		chatbox.selected = len(chatbox.items)-1

	def __show_create_game(self):
		"""Shows the interface for creating a multiplayer game"""
		event_map = {
		  'cancel' : self.show_multi,
		  'create' : self.__create_game
		}
		self._switch_current_widget('multiplayer_creategame', center=True, event_map=event_map, hide_old=True)
		self.current.files, self.maps_display = SavegameManager.get_maps()
		self.current.distributeInitialData({
		  'maplist' : self.maps_display,
		  'playerlimit' : range(2, MULTIPLAYER.MAX_PLAYER_COUNT)
		})
		if len(self.maps_display) > 0: # select first entry
				self.current.distributeData({
				  'maplist' : 0,
				  'playerlimit' : 0
				 })
		self.current.show()

		self.on_escape = event_map['cancel']

	def __create_game(self):
		"""Acctually create a game, join it and display the lobby"""
		# create the game
		#TODO: possibly some input validation
		mapindex = self.current.collectData('maplist')
		mapname = self.maps_display[mapindex]
		maxplayers = self.current.collectData('playerlimit') + 2 # 1 is the first entry
		game = NetworkInterface().creategame(mapname, maxplayers)
		if game is None:
			return

		self.__show_gamelobby()
