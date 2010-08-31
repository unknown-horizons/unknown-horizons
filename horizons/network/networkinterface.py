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

import horizons.main

from horizons.util.python.singleton import ManualConstructionSingleton
from horizons.util import Color
from horizons.extscheduler import ExtScheduler
from horizons.constants import NETWORK, VERSION
from horizons.network.client import Client
from horizons.network import CommandError, NetworkException


import getpass
import logging
import os

class NetworkInterface(object):
	"""Interface for low level networking"""
	__metaclass__ = ManualConstructionSingleton

	log = logging.getLogger("network")

	PING_INTERVAL = 0.5 # ping interval in seconds

	def __init__(self):
		# TODO: a user should be able to set its name in settings!
		name = horizons.main.fife.get_uh_setting("Nickname")
		self.__setup_client(name)
		# cbs means callbacks
		self.cbs_game_details_changed = []
		self.cbs_game_starts = []
		self.cbs_p2p_ready = []
		self.cbs_error = [] # cbs with 1 parameter which is an Exception instance
		self._client.register_callback("lobbygame_join", self._cb_game_details_changed)
		self._client.register_callback("lobbygame_leave", self._cb_game_details_changed)
		self._client.register_callback("lobbygame_starts", self._cb_game_starts)
		self._client.register_callback("p2p_ready", self._cb_p2p_ready)
		self._client.register_callback("p2p_data", self._cb_p2p_data)
		self.received_packets = []

	def add_to_extscheduler(self):
		ExtScheduler().add_new_object(self.ping, self, self.PING_INTERVAL, -1)

	def get_game(self):
		game = self._client.game
		return self.game2mpgame(game)

	def isconnected(self):
		return self._client.isconnected()

	def isjoined(self):
		return self._client.game is not None

	def change_name(self, name):
		self.disconnect()
		self.__setup_client(name)
		self.connect()

	def __setup_client(self, name):
		serveraddress = [NETWORK.SERVER_ADDRESS, NETWORK.SERVER_PORT]
		clientaddress = None
		if NETWORK.CLIENT_ADDRESS is not None and NETWORK.CLIENT_PORT > 0:
			clientaddress = [NETWORK.CLIENT_ADDRESS, NETWORK.CLIENT_PORT]
		try:
			self._client = Client(name, VERSION.RELEASE_VERSION, serveraddress, clientaddress)
		except NetworkException, e:
			raise RuntimeError(e)

	def connect(self):
		"""
		@throws: NetworkError
		"""
		self._client.connect()

	def disconnect(self):
		"""
		@throws: NetworkError
		"""
		self._client.disconnect()

	def ping(self):
		"""calls _client.ping until all packets are received"""
		if self._client.isconnected():
			try:
				while self._client.ping(): # ping receives packets
					pass
			except NetworkException, e:
				self._cb_error(e)

	def creategame(self, mapname, maxplayers):
		self.log.debug("[CREATEGAME] %s, %s", mapname, maxplayers)
		try:
			game = self._client.creategame(mapname, maxplayers)
		except NetworkException, e:
			self._cb_error(e)
			return None
		return self.game2mpgame(game)

	def joingame(self, uuid):
		i = 2
		try:
			while i < 10:
				try:
					self._client.joingame(uuid)
					return True
				except CommandError:
					self.log.debug("NetworkInterface: failed to join")
				self._client.disconnect()
				self._client.name = getpass.getuser() + str(i)
				self._client.connect()
				i = i + 1
			self._client.joingame(uuid)
		except NetworkException, e:
			self._cb_error(e)
		return False

	def leavegame(self):
		try:
			self._client.leavegame()
		except NetworkException, e:
			self._cb_error(e)
			return False
		return True

	def chat(self, message):
		try:
			self._client.chat(message)
		except NetworkException, e:
			self._cb_error(e)
			return False
		return True

	def register_chat_callback(self, function):
		self._client.register_callback("lobbygame_chat", function)

	def register_game_details_changed_callback(self, function, unique = True):
		if unique and function in self.cbs_game_details_changed:
			return
		self.cbs_game_details_changed.append(function)

	def _cb_game_details_changed(self, game, player):
		for callback in self.cbs_game_details_changed:
			callback()

	def register_game_starts_callback(self, function, unique = True):
		if unique and function in self.cbs_game_starts:
			return
		self.cbs_game_starts.append(function)

	def _cb_game_starts(self,game):
		for callback in self.cbs_game_starts:
			callback(self.get_game())

	def register_game_ready_callback(self, function, unique = True):
		if unique and function in self.cbs_p2p_ready:
			return
		self.cbs_p2p_ready.append(function)

	def _cb_p2p_ready(self):
		for callback in self.cbs_p2p_ready:
			callback(self.get_game())

	def _cb_p2p_data(self, address, data):
		self.received_packets.append(data)

	def register_error_callback(self, function, unique = True):
		if unique and function in self.cbs_error:
			return
		self.cbs_error.append(function)

	def _cb_error(self, exception=u""):
		for callback in self.cbs_error:
			callback(exception)

	def get_active_games(self):
		ret_mp_games = []
		try:
			games = self._client.listgames()
		except NetworkException, e:
			self._cb_error(e)
			return None
		for game in games:
			ret_mp_games.append(self.game2mpgame(game))
			self.log.debug("NetworkInterface: found active game %s", game.mapname)
		return ret_mp_games

	def send_to_all_clients(self, packet):
		"""
		Sends packet to all players, that are part of the game
		"""
		self._client.send(packet)

	def receive_all(self):
		"""
		Returns list of all packets, that have arrived until now (since the last call)
		@return: list of packets
		"""
		try:
			while self._client.ping(): # ping receives packets
				pass
		except NetworkException, e:
			self._cb_error(e)
			raise
		ret_list = self.received_packets
		self.received_packets = []
		return ret_list

	def game2mpgame(self, game):
		return MPGame(game.uuid, game.creator, game.mapname, game.maxplayers, game.playercnt, map(lambda x: unicode(x.name), game.players), self._client.name)

class MPGame(object):
	def __init__(self, uuid, creator, mapname, maxplayers, playercnt, players, localname):
		self.uuid       = uuid
		self.creator    = creator
		self.mapname    = mapname
		self.maxplayers = maxplayers
		self.playercnt  = playercnt
		self.players    = players
		self.localname  = localname

	def get_uuid(self):
		return self.uuid

	def get_map_name(self):
		return self.mapname

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
			ret_players.append({ 'id': id, 'name': playername, 'color': Color[id], 'local': self.localname == playername })
			id += 1
		return ret_players

	def get_player_count(self):
		return self.playercnt

	def __str__(self):
		return self.get_map_name() + " (" + self.get_player_count() + "/" + self.get_player_limit() + ")"
