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

import logging

from horizons.network.common import *
from horizons import network
from horizons.network import packets, find_enet_module

enet = find_enet_module()

MAX_PEERS = 4095
CONNECTION_TIMEOUT = 500

logging.basicConfig(level = logging.DEBUG)

class Server(object):
	def __init__(self, hostname, port):
		self.host = None
		self.hostname = hostname
		self.port = port
		self.callbacks = {
			'connect':    [ self.onconnect ],
			'disconnect': [ self.ondisconnect ],
			'receive':    [ self.onreceive ],
			packets.cmd_error:                 [ self.onerror ],
			packets.cmd_fatalerror:            [ self.onfatalerror ],
			packets.client.cmd_creategame:     [ self.oncreategame ],
			packets.client.cmd_listgames:      [ self.onlistgames ],
			packets.client.cmd_joingame:       [ self.onjoingame ],
			packets.client.cmd_leavegame:      [ self.onpktleavegame ],
			packets.client.cmd_chatmsg:        [ self.onchat ],
			packets.client.cmd_holepunchingok: [ self.onholepunchingok ],
			'holepunching':   [ self.onholepunching ],
			'startgame':      [ self.onstartgame ],
			'leavegame':      [ self.onleavegame ],
			'deletegame':     [ self.ondeletegame ],
		}
		self.games = []
		pass


	def register_callback(self, type, callback, prepend = False):
		if type in self.callbacks:
			if prepend:
				self.callbacks[type].insert(0, callback)
			else:
				self.callbacks[type].append(callback)
		else:
			raise TypeError("Unsupported type")


	def call_callbacks(self, type, *args):
		if not type in self.callbacks:
			return
		for callback in self.callbacks[type]:
			callback(*args)


	def run(self):
		logging.info("Starting up server on %s:%d" % (self.hostname, self.port))
		try:
			self.host = enet.Host(enet.Address(self.hostname, self.port), MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError):
			raise network.NetworkException("Unable to create network structure. Maybe invalid or irresolvable server address.")

		logging.debug("Entering the main loop...")
		while True:
			event = self.host.service(CONNECTION_TIMEOUT)
			if event.type == enet.EVENT_TYPE_NONE:
				continue
			elif event.type == enet.EVENT_TYPE_CONNECT:
				self.call_callbacks("connect", event)
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				self.call_callbacks("disconnect", event);
			elif event.type == enet.EVENT_TYPE_RECEIVE:
				self.call_callbacks("receive", event);
			else:
				logging.warning("Invalid packet (%u)" % (event.type))


	def send(self, peer, packet, channelid = 0):
		if self.host is None:
			raise network.NotConnected("Server is not running")
		packet.send(peer, channelid)
		self.host.flush()


	def disconnect(self, peer, later = False):
		logging.debug("Disconnecting client %s" % (peer.address))
		try:
			if later:
				peer.disconnect_later()
			else:
				peer.disconnect()
		except IOError:
			peer.reset()


	def onconnect(self, event):
		logging.debug("[CONNECT] New Client from %s" % (event.peer.address))


	def ondisconnect(self, event):
		logging.debug("[DISCONNECT] Client %s disconnected" % (event.peer.address))
		game = player = None
		for _game in self.games:
			for _player in _game.players:
				if _player.address == event.peer.address:
					game = _game
					player = _player
					break
		if game is None or player is None:
			return
		self.call_callbacks("leavegame", game, player)


	def onreceive(self, event):
		#logging.debug("[RECEIVE] Got data from %s" % (event.peer.address))
		packet = packets.unserialize(event.packet.data)
		if packet is None:
			logging.warning("Unknown packet from %s!" % (event.peer.address))
			self.send(event.peer, packets.cmd_fatalerror("Unknown packet. Maybe old client?"))
			self.disconnect(event.peer, True)
			return
		if not packet.__class__ in self.callbacks:
			logging.warning("Unhandled network packet from %s!" % (event.peer.address))
			return
		self.call_callbacks(packet.__class__, event.peer, packet)


	def onerror(self, peer, packet):
		# we shouldn't receive any errors from client
		# so ignore them all
		logging.debug("[ERROR] Client Message: %s" % (packet.errorstr))


	def onfatalerror(self, peer, packet):
		logging.debug("[FATAL] Client Message: %s" % (packet.errorstr))
		self.disconnect(peer, True)


	def oncreategame(self, peer, packet):
		game = None
		for _game in self.games:
			for _player in _game.players:
				if _player.address == peer.address:
					game = _game
					break
		if game is not None:
			self.send(peer, packets.cmd_error("You can't create a game while in another game"))
			return
		game = Game(packet, peer)
		logging.debug("[CREATE] uuid=%s, maxplayers=%d" % (game.uuid, game.maxplayers))
		self.games.append(game)
		self.send(peer, packets.server.data_gamestate(game))

		if game.playercnt == game.maxplayers:
			game.gamestarts = True
			self.call_callbacks("holepunching", game)



	def ondeletegame(self, game):
		logging.debug("[REMOVE] Game %s removed" % (game.uuid))
		self.games.remove(game)


	def onlistgames(self, peer, packet):
		logging.debug("[LIST]")
		gameslist = packets.server.data_gameslist()
		for _game in self.games:
			if _game.gamestarts:
				continue
			if _game.maxplayers == len(_game.players):
				continue
			if packet.clientversion != _game.clientversion:
				continue
			if packet.mapname and packet.mapname != _game.mapname:
				continue
			if packet.maxplayers and packet.maxplayers != _game.maxplayers:
				continue
			gameslist.addgame(_game);
		self.send(peer, gameslist)


	def onjoingame(self, peer, packet):
		logging.debug("[JOIN] name=%s, uuid=%s" % (packet.playername, packet.uuid))
		game = None
		for _game in self.games:
			for _player in _game.players:
				if _player.address == peer.address:
					game = _game
					break
		if game is not None:
			self.send(peer, packets.cmd_error("You can't join a game while in another game"))
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
			self.send(peer, packets.cmd_error("Unknown game"))
			return
		if game.gamestarts:
			self.send(peer, packets.cmd_error("Game has already started. No more joining"))
			return
		elif game.maxplayers == len(game.players):
			self.send(peer, packets.cmd_error("Game is full"))
			return

		playerunique = True
		for _player in game.players:
			if _player.name == packet.playername:
				playerunique = False
				break
			elif _player.address == peer.address:
				playerunique = False
				break
		if not playerunique:
			self.send(peer, packets.cmd_error("Your name or address is already known to this game"))
			return

		game.addplayer(Player(packet.playername, peer))
		game.playercnt += 1
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))

		# if game is full ... lets start the game
		if game.playercnt == game.maxplayers:
			game.gamestarts = True
			self.call_callbacks("holepunching", game)


	def onpktleavegame(self, peer, packet):
		game = player = None
		for _game in self.games:
			for _player in _game.players:
				if _player.address == peer.address:
					game = _game
					player = _player
					break
		if game is None or player is None:
			self.send(peer, packets.cmd_error("You are an unknown player"))
			return
		self.call_callbacks("leavegame", game, player)
		self.send(peer, packets.cmd_ok())


	def onleavegame(self, game, player):
		logging.debug("[LEAVE] Player %s leaves game %s" % (player.name, game.uuid))
		game.players.remove(player)
		game.playercnt -= 1
		if not game.gamestarts:
			for _player in game.players:
				self.send(_player.peer, packets.server.data_gamestate(game))
		if game.playercnt <= 0:
			self.call_callbacks('deletegame', game)


	def onholepunching(self, game):
		logging.debug("[HOLEPUNCHING] %s" % (game.uuid))
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_holepunching())


	def onholepunchingok(self, peer, packet):
		game = player = None
		for _game in self.games:
			for _player in _game.players:
				if _player.address == peer.address:
					game = _game
					player = _player
					break
		if game is None:
			self.send(peer, packets.cmd_fatalerror("Unable to find the game you're in"))
			self.disconnect(peer, True)
			return
		player.ready = True
		logging.debug("[HOLEPUNCHING] [%s] Player %s (%s) is ready" % (game.uuid, player.name, player.address))

		playersready = True
		for _player in game.players:
			if not _player.ready:
				playersready = False
				break
		if playersready:
			self.call_callbacks("startgame", game)


	def onstartgame(self, game):
		logging.debug("[START] %s" % (game.uuid))
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_startgame())


	def onchat(self, peer, packet):
		game = player = None
		for _game in self.games:
			for _player in _game.players:
				if _player.address == peer.address:
					game = _game
					player = _player
					break
		if game is None or player is None:
			self.send(peer, packets.cmd_error("You are an unknown player"))
			self.disconnect(peer, True)
			return
		logging.debug("[CHAT] [%s] %s: %s" % (game.uuid, player.name, packet.chatmsg))
		# don't send packets to already started games
		if game.gamestarts:
			return
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_chatmsg(player.name, packet.chatmsg))

