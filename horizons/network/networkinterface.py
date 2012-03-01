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

import horizons.main

from horizons.util.python.singleton import ManualConstructionSingleton
from horizons.util import Color, DifficultySettings, parse_port
from horizons.extscheduler import ExtScheduler
from horizons.constants import NETWORK, VERSION
from horizons.network.client import Client
from horizons.network import CommandError, NetworkException, FatalError

import logging

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
		self._client.register_callback("lobbygame_join",       self._cb_game_details_changed)
		self._client.register_callback("lobbygame_leave",      self._cb_game_details_changed)
		#self._client.register_callback("lobbygame_changename", self._cb_game_details_changed)
		#self._client.register_callback("lobbygame_changecolor", self._cb_game_details_changed)
		self._client.register_callback("lobbygame_starts", self._cb_game_prepare)
		self._client.register_callback("game_starts", self._cb_game_starts)
		self._client.register_callback("game_data", self._cb_game_data)
		self.received_packets = []

		ExtScheduler().add_new_object(self.ping, self, self.PING_INTERVAL, -1)

	def get_game(self):
		game = self._client.game
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
		serveraddress = [NETWORK.SERVER_ADDRESS, NETWORK.SERVER_PORT]
		clientaddress = None
		client_port = parse_port(horizons.main.fife.get_uh_setting("NetworkPort"), allow_zero=True)
		if NETWORK.CLIENT_ADDRESS is not None or client_port > 0:
			clientaddress = [NETWORK.CLIENT_ADDRESS, client_port]
		try:
			self._client = Client(name, VERSION.RELEASE_VERSION, serveraddress, clientaddress)
		except NetworkException as e:
			raise RuntimeError(e)

	def __get_player_name(self):
		return horizons.main.fife.get_uh_setting("Nickname")

	def connect(self):
		"""
		@throws: NetworkError
		"""
		try:
			self._client.connect()
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

	def creategame(self, mapname, maxplayers, name, load=None):
		self.log.debug("[CREATEGAME] %s, %s, %s, %s", mapname, maxplayers, name, load)
		try:
			game = self._client.creategame(mapname, maxplayers, name, load)
		except NetworkException as e:
			fatal = self._handle_exception(e)
			return None
		return self.game2mpgame(game)

	def joingame(self, uuid):
		"""Join a game with a certain uuid"""
		i = 2
		try:
			while i < 10: # try 10 different names
				try:
					self._client.joingame(uuid)
					return True
				except CommandError:
					self.log.debug("NetworkInterface: failed to join")
				self.change_name( self.__get_player_name() + unicode(i), save=False )
				i += 1
			self._client.joingame(uuid)
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
			horizons.main.fife.set_uh_setting("Nickname", new_nick)
			horizons.main.fife.save_settings()
		try:
			return self._client.changename(new_nick)
		except NetworkException as e:
			self._handle_exception(e)
			return False

	def register_chat_callback(self, function):
		self._client.register_callback("lobbygame_chat", function)

	def register_player_joined_callback(self, function):
		self._client.register_callback("lobbygame_join", function)

	def register_player_left_callback(self, function):
		self._client.register_callback("lobbygame_leave", function)

	def register_player_changed_name_callback(self, function):
		self._client.register_callback("lobbygame_changename", function)

	#def register_player_changed_color_callback(self, function):
	#	self._client.register_callback("lobbygame_changecolor", function)

	def register_game_details_changed_callback(self, function, unique = True):
		if unique and function in self.cbs_game_details_changed:
			return
		self.cbs_game_details_changed.append(function)

	def _cb_game_details_changed(self, game, player):
		for callback in self.cbs_game_details_changed:
			callback()

	def register_game_prepare_callback(self, function, unique = True):
		if unique and function in self.cbs_game_prepare:
			return
		self.cbs_game_prepare.append(function)

	def _cb_game_prepare(self, game):
		for callback in self.cbs_game_prepare:
			callback(self.get_game())

	def register_game_starts_callback(self, function, unique = True):
		if unique and function in self.cbs_game_starts:
			return
		self.cbs_game_starts.append(function)

	def _cb_game_starts(self, game):
		for callback in self.cbs_game_starts:
			callback(self.get_game())

	def _cb_game_data(self, data):
		self.received_packets.append(data)

	def register_error_callback(self, function, unique = True):
		if unique and function in self.cbs_error:
			return
		self.cbs_error.append(function)

	def _cb_error(self, exception=u"", fatal=True):
		for callback in self.cbs_error:
			callback(exception, fatal)

	def get_active_games(self, only_this_version_allowed = False):
		"""Returns a list of active games or None on fatal error"""
		ret_mp_games = []
		try:
			games = self._client.listgames(onlyThisVersion=only_this_version_allowed)
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
		return MPGame(game.uuid, game.creator, game.mapname, game.maxplayers, game.playercnt, map(lambda x: unicode(x.name), game.players), self._client.name, game.clientversion, game.name, game.load)

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


class MPGame(object):
	def __init__(self, uuid, creator, mapname, maxplayers, playercnt, players, localname, version, name, load):
		self.uuid       = uuid
		self.creator    = creator
		self.mapname    = mapname
		self.maxplayers = maxplayers
		self.playercnt  = playercnt
		self.players    = players
		self.localname  = localname
		self.version    = version
		self.name       = name
		self.load       = load

	def get_uuid(self):
		return self.uuid

	def get_map_name(self):
		return self.mapname

	def get_name(self):
		return self.name

	def get_creator(self):
		return self.creator

	def get_player_limit(self):
		return self.maxplayers

	def get_players(self):
		return self.players

	def get_player_list(self):
		ret_players = []
		id = 1
		for playername in self.get_players():
			# TODO: add support for selecting difficulty levels to the GUI
			ret_players.append({'id': id, 'name': playername, 'color': Color[id], 'local': self.localname == playername, \
				'ai': False, 'difficulty': DifficultySettings.DEFAULT_LEVEL})
			id += 1
		return ret_players

	def get_player_count(self):
		return self.playercnt

	def get_version(self):
		return self.version

	def __str__(self):
		return "%s (%d/%d)" % (self.get_map_name(), self.get_player_count(), self.get_player_limit())
