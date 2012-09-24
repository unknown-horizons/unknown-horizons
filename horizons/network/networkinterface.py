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

import horizons.globals

from horizons.util.color import Color
from horizons.util.difficultysettings import DifficultySettings
from horizons.util.python import parse_port
from horizons.util.python.singleton import ManualConstructionSingleton
from horizons.extscheduler import ExtScheduler
from horizons.constants import NETWORK, VERSION, LANGUAGENAMES
from horizons.network.client import Client
from horizons.network import CommandError, NetworkException, FatalError

import logging
import uuid

class NetworkInterface(object):
	"""Interface for low level networking"""
	__metaclass__ = ManualConstructionSingleton

	log = logging.getLogger("network")

	PING_INTERVAL = 0.5 # ping interval in seconds

	def __init__(self):
		self.__setup_client()
		# cbs means callbacks
		self.cbs_game_details_changed = []
		self.cbs_game_prepare = []
		self.cbs_game_starts = []
		self.cbs_error = [] # callbacks on error that looks like this: error(exception, fatal=True)

		# create a game_details_changed meta callback
		metacb = self._cb_game_details_changed
		self.register_player_joined_callback(metacb)
		self.register_player_left_callback(metacb)
		self.register_player_changed_name_callback(metacb)
		self.register_player_changed_color_callback(metacb)
		self.register_player_toggle_ready_callback(metacb)

		self._client.register_callback("lobbygame_starts", self._cb_game_prepare)
		self._client.register_callback("game_starts",      self._cb_game_starts)
		self._client.register_callback("game_data",        self._cb_game_data)
		self.received_packets = []

		ExtScheduler().add_new_object(self.ping, self, self.PING_INTERVAL, -1)

	def get_game(self):
		game = self._client.game
		if game is None:
			return None
		return self.game2mpgame(game)

	def isconnected(self):
		return self._client.isconnected()

	def isjoined(self):
		return self._client.game is not None

	def network_data_changed(self, connect=False):
		"""Call in case constants like client address or client port changed.
		@param connect: whether to connect after the data updated
		@throws RuntimeError in case of invalid data or an NetworkException forwarded from connect"""

		if self.isconnected():
			self.disconnect()
		self.__setup_client()
		if connect:
			self.connect()

	def __setup_client(self):
		name = self.__get_player_name()
		color = self.__get_player_color()
		serveraddress = [NETWORK.SERVER_ADDRESS, NETWORK.SERVER_PORT]
		clientaddress = None
		client_port = parse_port(horizons.globals.fife.get_uh_setting("NetworkPort"))
		if NETWORK.CLIENT_ADDRESS is not None or client_port > 0:
			clientaddress = [NETWORK.CLIENT_ADDRESS, client_port]
		try:
			self._client = Client(name, VERSION.RELEASE_VERSION, serveraddress,
			                      clientaddress, color, self.__get_client_id())
		except NetworkException as e:
			raise RuntimeError(e)

	def __get_player_name(self):
		return horizons.globals.fife.get_uh_setting("Nickname")

	def __get_player_color(self):
		return horizons.globals.fife.get_uh_setting("ColorID")

	def __get_client_id(self):
		try:
			return uuid.UUID(horizons.globals.fife.get_uh_setting("ClientID")).hex
		except (ValueError, TypeError):
			# We need a new client id
			client_id = uuid.uuid4()
			horizons.globals.fife.set_uh_setting("ClientID", client_id)
			horizons.globals.fife.save_settings()
			return client_id.hex

	def get_client_id(self):
		return self._client.clientid

	def get_client_name(self):
		return self._client.name

	def get_client_color(self):
		return self._client.color

	def connect(self):
		"""
		@throws: NetworkError
		"""
		try:
			self._client.connect()
			self.set_client_language()
		except NetworkException as e:
			self.disconnect()
			raise e

	def disconnect(self):
		self._client.disconnect()

	def ping(self):
		"""calls _client.ping until all packets are received"""
		if self._client.isconnected():
			try:
				while self._client.ping(): # ping receives packets
					pass
			except NetworkException as e:
				self._handle_exception(e)

	def set_props(self, props):
		try:
			self._client.setprops(props)
		except NetworkException as e:
			self._handle_exception(e)
			return False
		return True

	def set_client_language(self):
		lang = LANGUAGENAMES.get_by_value(horizons.globals.fife.get_uh_setting("Language"))
		if len(lang):
			return self.set_props({'lang': lang})
		return True

	def creategame(self, mapname, maxplayers, name, maphash="", password=""):
		self.log.debug("[CREATEGAME] %s(h=%s), %s, %s, %s", mapname, maphash, maxplayers, name)
		try:
			game = self._client.creategame(mapname, maxplayers, name, maphash, password)
		except NetworkException as e:
			fatal = self._handle_exception(e)
			return None
		return self.game2mpgame(game)

	def joingame(self, uuid, password="", fetch=False):
		"""Join a game with a certain uuid"""
		i = 2
		try:
			while i < 10: # FIXME: try 10 different names and colors
				try:
					self._client.joingame(uuid, password, fetch)
					return True
				except CommandError as e:
					self.log.debug("NetworkInterface: failed to join")
					if 'name' in e.message:
						self.change_name( self.__get_player_name() + unicode(i), save=False )
					elif 'color' in e.message:
						self.change_color(self.__get_player_color() + i, save=False)
					else:
						raise
				i += 1
			self._client.joingame(uuid, password, fetch)
		except NetworkException as e:
			self._handle_exception(e)
		return False

	def leavegame(self):
		try:
			self._client.leavegame()
		except NetworkException as e:
			fatal = self._handle_exception(e)
			if fatal:
				return False
		return True

	def chat(self, message):
		try:
			self._client.chat(message)
		except NetworkException as e:
			self._handle_exception(e)
			return False
		return True

	def change_name(self, new_nick, save=True):
		""" see network/client.py -> changename() for _important_ return values"""
		if save:
			horizons.globals.fife.set_uh_setting("Nickname", new_nick)
			horizons.globals.fife.save_settings()
		try:
			return self._client.changename(new_nick)
		except NetworkException as e:
			self._handle_exception(e)
			return False

	def change_color(self, new_color, save=True):
		""" see network/client.py -> changecolor() for _important_ return values"""
		if new_color > len(set(Color)):
			new_color %= len(set(Color))
		if save:
			horizons.globals.fife.set_uh_setting("ColorID", new_color)
			horizons.globals.fife.save_settings()
		try:
			return self._client.changecolor(new_color)
		except NetworkException as e:
			self._handle_exception(e)
			return False

	def register_chat_callback(self, function):
		self._client.register_callback("lobbygame_chat", function)

	def register_player_joined_callback(self, function):
		self._client.register_callback("lobbygame_join", function)

	def register_player_left_callback(self, function):
		self._client.register_callback("lobbygame_leave", function)

	def register_game_terminated_callback(self, function):
		self._client.register_callback("lobbygame_terminate", function)

	def register_player_toggle_ready_callback(self, function):
		self._client.register_callback("lobbygame_toggleready", function)

	def register_kick_callback(self, function):
		self._client.register_callback("lobbygame_kick", function)

	def register_player_changed_name_callback(self, function):
		self._client.register_callback("lobbygame_changename", function)

	def register_player_changed_color_callback(self, function):
		self._client.register_callback("lobbygame_changecolor", function)

	def register_player_fetch_game_callback(self, function):
		self._client.register_callback("savegame_data", function)

	def register_game_details_changed_callback(self, function, unique=True):
		if unique and function in self.cbs_game_details_changed:
			return
		self.cbs_game_details_changed.append(function)

	def _cb_game_details_changed(self, game, player, *args, **kwargs):
		for callback in self.cbs_game_details_changed:
			callback()

	def register_game_prepare_callback(self, function, unique=True):
		if unique and function in self.cbs_game_prepare:
			return
		self.cbs_game_prepare.append(function)

	def _cb_game_prepare(self, game):
		for callback in self.cbs_game_prepare:
			callback(self.get_game())

	def register_game_starts_callback(self, function, unique=True):
		if unique and function in self.cbs_game_starts:
			return
		self.cbs_game_starts.append(function)

	def _cb_game_starts(self, game):
		for callback in self.cbs_game_starts:
			callback(self.get_game())

	def _cb_game_data(self, data):
		self.received_packets.append(data)

	def register_error_callback(self, function, unique=True):
		if unique and function in self.cbs_error:
			return
		self.cbs_error.append(function)

	def _cb_error(self, exception=u"", fatal=True):
		for callback in self.cbs_error:
			callback(exception, fatal)

	def get_active_games(self, only_this_version_allowed=False):
		"""Returns a list of active games or None on fatal error"""
		ret_mp_games = []
		try:
			games = self._client.listgames(only_this_version=only_this_version_allowed)
		except NetworkException as e:
			fatal = self._handle_exception(e)
			return [] if not fatal else None
		for game in games:
			ret_mp_games.append(self.game2mpgame(game))
			self.log.debug("NetworkInterface: found active game %s", game.mapname)
		return ret_mp_games

	def send_to_all_clients(self, packet):
		"""
		Sends packet to all players, that are part of the game
		"""
		if self._client.isconnected():
			try:
				self._client.send(packet)
			except NetworkException as e:
				self._handle_exception(e)

	def receive_all(self):
		"""
		Returns list of all packets, that have arrived until now (since the last call)
		@return: list of packets
		"""
		try:
			while self._client.ping(): # ping receives packets
				pass
		except NetworkException as e:
			self.log.debug("ping in receive_all failed: "+str(e))
			self._handle_exception(e)
			raise CommandError(e)
		ret_list = self.received_packets
		self.received_packets = []
		return ret_list

	def game2mpgame(self, game):
		return MPGame(game, self)

	def get_clientversion(self):
		return self._client.version

	def _handle_exception(self, e):
		try:
			raise e
		except FatalError as e:
			self._cb_error(e, fatal=True)
			self.disconnect()
			return True
		except NetworkException as e:
			self._cb_error(e, fatal=False)
			return False

	def toggle_ready(self):
		self._client.toggleready()

	def kick(self, player_sid):
		self._client.kick(player_sid)

	#TODO
	def send_fetch_game(self, clientversion, uuid):
		self._client.send_fetch_game(clientversion, uuid)


class MPGame(object):
	def __init__(self, game, netif):
		self.uuid       = game.uuid
		self.creator    = game.creator
		self.mapname    = game.mapname
		self.maphash    = game.maphash
		self.maxplayers = game.maxplayers
		self.playercnt  = game.playercnt
		self.players    = game.players
		self.version    = game.clientversion
		self.name       = game.name
		self.password   = game.password
		self.netif      = netif

	def get_uuid(self):
		return self.uuid

	def get_map_name(self):
		return self.mapname

	def get_map_hash(self):
		return self.maphash

	def is_savegame(self):
		return bool(self.maphash)

	def get_name(self):
		return self.name

	def get_creator(self):
		return self.creator

	def get_player_limit(self):
		return self.maxplayers

	def get_players(self):
		return self.players

	def has_password(self):
		return self.password

	def get_player_list(self):
		ret_players = []
		id = 1
		for player in self.get_players():
			# TODO: add support for selecting difficulty levels to the GUI
			status = _('Ready') if player.ready else _('Not Ready')
			ret_players.append({
				'id':         id,
				'sid':        player.sid,
				'name':       player.name,
				'color':      Color[player.color],
				'clientid':   player.clientid,
				'local':      self.netif.get_client_name() == player.name,
				'ai':         False,
				'difficulty': DifficultySettings.DEFAULT_LEVEL,
				'status':     status
				})
			id += 1
		return ret_players

	def get_player_count(self):
		return self.playercnt

	def get_version(self):
		return self.version

	def __str__(self):
		return "%s (%d/%d)" % (self.get_map_name(), self.get_player_count(), self.get_player_limit())
