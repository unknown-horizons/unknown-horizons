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
import uuid

from horizons.network.common import *
from horizons import network
from horizons.network import packets, find_enet_module

enet = find_enet_module(client = False)

MAX_PEERS = 4095
CONNECTION_TIMEOUT = 500

logging.basicConfig(format = '[%(asctime)-15s] [%(levelname)s] %(message)s',
		level = logging.DEBUG)

class Server(object):
	def __init__(self, hostname, port, statistic_file = None):
		packets.SafeUnpickler.set_mode(client = False)
		self.host = None
		self.hostname = hostname
		self.port = port
		self.statistic = {
			'file': statistic_file,
			'timestamp': 0,
			'interval': 1 * 60 * 1000,
		}
		self.callbacks = {
			'onconnect':    [ self.onconnect ],
			'ondisconnect': [ self.ondisconnect ],
			'onreceive':    [ self.onreceive ],
			packets.cmd_error:                 [ self.onerror ],
			packets.cmd_fatalerror:            [ self.onfatalerror ],
			packets.client.cmd_creategame:     [ self.oncreategame ],
			packets.client.cmd_listgames:      [ self.onlistgames ],
			packets.client.cmd_joingame:       [ self.onjoingame ],
			packets.client.cmd_leavegame:      [ self.onleavegame ],
			packets.client.cmd_chatmsg:        [ self.onchat ],
			packets.client.cmd_changename:     [ self.onchangename ],
			packets.client.cmd_preparedgame:   [ self.onpreparedgame ],
			'preparegame':    [ self.preparegame ],
			'startgame':      [ self.startgame ],
			'leavegame':      [ self.leavegame ],
			'deletegame':     [ self.deletegame ],
			'terminategame':  [ self.terminategame ],
			'gamedata':       [ self.gamedata ],
		}
		self.games = [] # list of games
		self.players = {} # sessionid => Player() dict
		self.check_urandom()

	def check_urandom(self):
		try:
			import os
			os.urandom(1)
		except NotImplementedError:
			import random
			import time
			random.seed(uuid.getnode() + int(time.time() * 1e3))
			logging.warning("[INIT] Your system doesn't support /dev/urandom")


	# uuid4() uses /dev/urandom when possible
	def generate_session_id(self):
		return uuid.uuid4().hex


	def register_callback(self, type, callback, prepend = False):
		if type in self.callbacks:
			if prepend:
				self.callbacks[type].insert(0, callback)
			else:
				self.callbacks[type].append(callback)
		else:
			raise TypeError("Unsupported type")


	def call_callbacks(self, type, *args):
		if type not in self.callbacks:
			return
		for callback in self.callbacks[type]:
			callback(*args)


	def run(self):
		logging.info("Starting up server on %s:%d" % (self.hostname, self.port))
		try:
			self.host = enet.Host(enet.Address(self.hostname, self.port), MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError):
			# these exceptions do not provide any information.
			raise network.NetworkException("Unable to create network structure. Maybe invalid or irresolvable server address:")

		logging.debug("Entering the main loop...")
		while True:
			if self.statistic['file'] is not None:
				if self.statistic['timestamp'] <= 0:
					self.print_statistic(self.statistic['file'])
					self.statistic['timestamp'] = self.statistic['interval']
				else:
					self.statistic['timestamp'] -= CONNECTION_TIMEOUT

			event = self.host.service(CONNECTION_TIMEOUT)
			if event.type == enet.EVENT_TYPE_NONE:
				continue
			elif event.type == enet.EVENT_TYPE_CONNECT:
				self.call_callbacks("onconnect", event)
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				self.call_callbacks("ondisconnect", event)
			elif event.type == enet.EVENT_TYPE_RECEIVE:
				self.call_callbacks("onreceive", event)
			else:
				logging.warning("Invalid packet (%u)" % (event.type))


	def send(self, peer, packet, channelid = 0):
		if self.host is None:
			raise network.NotConnected("Server is not running")
		packet.send(peer, None, channelid)
		self.host.flush()

	def _send(self, peer, data, channelid = 0):
		if self.host is None:
			raise network.NotConnected("Server is not running")
		packets.packet._send(peer, data, channelid)
		self.host.flush()


	def disconnect(self, peer, later = True):
		logging.debug("[DISCONNECT] Disconnecting client %s" % (peer.address))
		try:
			if later:
				peer.disconnect_later()
			else:
				peer.disconnect()
		except IOError:
			peer.reset()


	def error(self, peer, message):
		self.send(peer, packets.cmd_error(message))


	def fatalerror(self, peer, message, later = True):
		self.send(peer, packets.cmd_fatalerror(message))
		self.disconnect(peer, later)


	def onconnect(self, event):
		peer = event.peer
		# disable that check as peer.data may be uninitialized which segfaults then
		#if peer.data in self.players:
		#	logging.warning("[CONNECT] Already known player %s!" % (peer.address))
		#	self.fatalerror(event.peer, "You can't connect more than once")
		#	return
		player = Player(event.peer, self.generate_session_id(), event.data)
		logging.debug("[CONNECT] New Client: %s" % (player))

		# store session id inside enet.peer.data
		# NOTE: ALWAYS initialize peer.data
		event.peer.data = player.sid

		if (player.protocol > 0):
			logging.warning("[CONNECT] %s runs old or unsupported protocol" % (player))
			self.fatalerror(event.peer, "Old or unsupported multiplayer protocol. Please check your game version")
			return

		# note: copying bytes or int doesn't work here
		self.players[player.sid] = player
		self.send(event.peer, packets.server.cmd_session(player.sid))


	def ondisconnect(self, event):
		peer = event.peer
		# check need for early disconnects (e.g. old protocol)
		if peer.data not in self.players:
			return
		player = self.players[peer.data]
		logging.debug("[DISCONNECT] %s disconnected" % (player))
		if player.game is not None:
			self.call_callbacks("leavegame", player.game, player)
		del self.players[peer.data]


	def onreceive(self, event):
		peer = event.peer
		#logging.debug("[RECEIVE] Got data from %s" % (peer.address))
		# check player is known by server
		if peer.data not in self.players:
			logging.warning("[RECEIVE] Packet from unknown player %s!" % (peer.address))
			self.fatalerror(event.peer, "I don't know you")
			return

		player = self.players[peer.data]

		# shortpath if game is running
		if player.game is not None and player.game.state is Game.State.Running:
			self.call_callbacks('gamedata', event.peer, event.packet.data)
			return

		packet = None
		try:
			packet = packets.unserialize(event.packet.data)
		except Exception:
			logging.warning("[RECEIVE] Unknown packet from %s!" % (peer.address))
			self.fatalerror(event.peer, "Unknown packet. Please check your game version")
			return

		# session id check
		if packet.sid != player.sid:
			logging.warning("[RECEIVE] Invalid session id for player %s (%s vs %s)!" % (peer.address, packet.sid, player.sid))
			self.fatalerror(event.peer, "Invalid/Unknown session") # this will trigger ondisconnect() for cleanup
			return

		if packet.__class__ not in self.callbacks:
			logging.warning("[RECEIVE] Unhandled network packet from %s - Ignoring!" % (peer.address))
			return
		self.call_callbacks(packet.__class__, event.peer, packet)


	def onerror(self, peer, packet):
		# we shouldn't receive any errors from client
		# so ignore them all
		logging.debug("[ERROR] Client Message: %s" % (packet.errorstr))


	def onfatalerror(self, peer, packet):
		# we shouldn't receive any fatala errors from client
		# so just disconnect them
		logging.debug("[FATAL] Client Message: %s" % (packet.errorstr))
		self.disconnect(peer)


	def oncreategame(self, peer, packet):
		if not len(packet.playername):
			self.error(peer, "You must have a non empty name")
			return
		player = self.players[peer.data]
		if player.game is not None:
			self.error(peer, "You can't create a game while in another game")
			return
		player.name = unicode(packet.playername)
		game = Game(packet, player)
		logging.debug("[CREATE] [%s] %s created %s" % (game.uuid, player, game))
		self.games.append(game)
		self.send(peer, packets.server.data_gamestate(game))

		if game.playercnt == game.maxplayers:
			self.call_callbacks("preparegame", game)

	def deletegame(self, game):
		logging.debug("[REMOVE] [%s] %s removed" % (game.uuid, game))
		self.games.remove(game)

	def onlistgames(self, peer, packet):
		logging.debug("[LIST]")
		gameslist = packets.server.data_gameslist()
		for _game in self.games:
			if _game.state is not Game.State.Open:
				continue
			if _game.maxplayers == len(_game.players):
				continue
			if packet.clientversion != -1 and packet.clientversion != _game.clientversion:
				continue
			if packet.mapname and packet.mapname != _game.mapname:
				continue
			if packet.maxplayers and packet.maxplayers != _game.maxplayers:
				continue
			gameslist.addgame(_game)
		self.send(peer, gameslist)


	def onjoingame(self, peer, packet):
		if not len(packet.playername):
			self.error(peer, "You must have a non empty name")
			return
		player = self.players[peer.data]
		if player.game is not None:
			self.error(peer, "You can't join a game while in another game")
			return

		game = None
		for _game in self.games:
			if (packet.clientversion != _game.clientversion):
				continue
			if (packet.uuid != _game.uuid):
				continue
			game = _game
			break
		if game is None:
			self.error(peer, "Unknown game")
			return
		if game.state is not Game.State.Open:
			self.error(peer, "Game has already started. No more joining")
			return
		elif game.maxplayers == len(game.players):
			self.error(peer, "Game is full")
			return

		# make sure player names are unique
		unique = True
		for _player in game.players:
			if _player.name == packet.playername:
				unique = False
				break
		if not unique:
			self.error(peer, "There's already a player with your name inside this game. Change your name")
			return

		logging.debug("[JOIN] [%s] %s joined %s" % (game.uuid, player, game))
		player.name = packet.playername
		game.add_player(player)
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))

		# if game is full ... lets start the game
		if game.playercnt == game.maxplayers:
			self.call_callbacks("preparegame", game)


	def onleavegame(self, peer, packet):
		player = self.players[peer.data]
		if player.game is None:
			self.error(peer, "You are not inside a game")
			return
		self.call_callbacks("leavegame", player.game, player)
		self.send(peer, packets.cmd_ok())


	def leavegame(self, game, player):
		if game.state is not Game.State.Open:
			self.call_callbacks('terminategame', game, player)
			return
		logging.debug("[LEAVE] [%s] %s left %s" % (game.uuid, player, game))
		game.remove_player(player)
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))
		if game.playercnt <= 0:
			self.call_callbacks('deletegame', game)


	def terminategame(self, game, player = None):
		logging.debug("[TERMINATE] [%s] (by %s)" % (game.uuid, player if player is not None else None))
		for _player in game.players:
			if _player.peer.state == enet.PEER_STATE_CONNECTED:
				self.fatalerror(_player.peer, "I feel like a bad bunny but one player has terminated his game and this game is programmed to terminate the whole game now. Sorry :*(")
		game.clear()
		self.call_callbacks('deletegame', game)


	def preparegame(self, game):
		logging.debug("[PREPARE] [%s] Players: %s" % (game.uuid, [unicode(i) for i in game.players]))
		game.state = Game.State.Prepare
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_preparegame())


	def startgame(self, game):
		logging.debug("[START] [%s] Players: %s" % (game.uuid, [unicode(i) for i in game.players]))
		game.state = Game.State.Running
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_startgame())


	def onchat(self, peer, packet):
		if not len(packet.chatmsg):
			self.error(peer, "Chat message cannot be empty")
			return
		player = self.players[peer.data]
		if player.game is None:
			self.error(peer, "Chatting is only allowed inside the lobby of a game")
			return
		game = player.game
		logging.debug("[CHAT] [%s] %s: %s" % (game.uuid, player, packet.chatmsg))
		# don't send packets to already started games
		if game.state is not Game.State.Open:
			return
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_chatmsg(player.name, packet.chatmsg))


	def onchangename(self, peer, packet):
		# NOTE: that event _only_ happens inside a lobby
		if not len(packet.playername):
			self.error(peer, "You must have a non empty name")
			return
		player = self.players[peer.data]
		if player.game is None:
			# just ignore if not inside a game
			self.send(peer, packets.cmd_ok())
			return
		game = player.game
		# don't send packets to already started games
		if game.state is not Game.State.Open:
			return

		# ignore change to existing name
		if player.name == packet.playername:
			return

		# make sure player names are unique
		unique = True
		for _player in game.players:
			if _player.name == packet.playername:
				unique = False
				break
		if not unique:
			self.error(peer, "There's already a player with your name inside this game. Unable to change your name")
			return

		logging.debug("[CHANGENAME] [%s] %s -> %s" % (game.uuid, player.name, packet.playername))
		player.name = packet.playername
		if game.creator_sid == player.sid:
			game.creator = player.name
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))


	def gamedata(self, peer, data):
		player = self.players[peer.data]
		game = player.game
		#logging.debug("[GAMEDATA] [%s] %s" % (game.uuid, player))
		for _player in game.players:
			if _player is player:
				continue
			self._send(_player.peer, data)


	def onpreparedgame(self, peer, packet):
		player = self.players[peer.data]
		game = player.game
		if game is None:
			return
		logging.debug("[PREPARED] [%s] %s" % (game.uuid, player))
		player.ready = True
		readycount = 0
		for _player in game.players:
			if _player.ready:
				readycount += 1
		if readycount != game.playercnt:
			return
		self.call_callbacks('startgame', game)


	def print_statistic(self, file):
		try:
			fd = open(file, "w")

			fd.write("Games.Total: %d\n" % (len(self.games)))
			games_playing = 0
			for game in self.games:
				if game.state is Game.State.Running:
					games_playing += 1
			fd.write("Games.Playing: %d\n" % (games_playing))

			fd.write("Players.Total: %d\n" % (len(self.players)))
			players_inlobby = 0
			players_playing = 0
			for player in self.players.values():
				if player.game is None:
					continue
				if player.game.state is Game.State.Running:
					players_playing += 1
				else:
					players_inlobby += 1
			fd.write("Players.Lobby: %d\n" % (players_inlobby))
			fd.write("Players.Playing: %d\n" % (players_playing))

			fd.close()
		except IOError as e:
			logging.error("[STATISTIC] Unable to open statistic file: %s" % (e))
		return

