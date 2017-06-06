# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import gettext
import logging
import uuid
from typing import Dict, List

from horizons import network
from horizons.i18n import find_available_languages
from horizons.messaging.simplemessagebus import SimpleMessageBus
from horizons.network import enet, packets
from horizons.network.common import ErrorType, Game, Player

MAX_PEERS = 4095
CONNECTION_TIMEOUT = 500
# protocols used by uh versions:
# 0 ... 2012.1
# 1 ... >2012.1
PROTOCOLS = [0, 1]

logging.basicConfig(format = '[%(asctime)-15s] [%(levelname)s] %(message)s',
		level = logging.DEBUG)


EVENTS = [
	'onconnect',
	'ondisconnect',
	'onreceive',
	packets.cmd_error,
	packets.cmd_fatalerror,
	packets.client.cmd_sessionprops,
	packets.client.cmd_creategame,
	packets.client.cmd_listgames,
	packets.client.cmd_joingame,
	packets.client.cmd_leavegame,
	packets.client.cmd_chatmsg,
	packets.client.cmd_changename,
	packets.client.cmd_changecolor,
	packets.client.cmd_preparedgame,
	packets.client.cmd_toggleready,
	packets.client.cmd_kickplayer,
	#TODO packets.client.cmd_fetch_game,
	#TODO packets.client.savegame_data,
	'preparegame',
	'startgame',
	'leavegame',
	'deletegame',
	'terminategame',
	'gamedata'
]


def T(text):
	"""
	No-op for extracting strings for translation.
	"""
	return text


def print_statistic(players, games, output_file):
	"""
	Writes information about the current state of the server (players / games).
	"""
	lines = []

	games_playing = len([game for game in games if game.state is Game.State.Running])
	lines.append("Games.Total: {}".format(len(games)))
	lines.append("Games.Playing: {}".format(games_playing))

	active_players = [p for p in players if p.game is not None]
	players_playing = len([p for p in active_players if p.game.state is Game.State.Running])
	players_inlobby = len(active_players) - players_playing

	lines.append("Players.Total: {}".format(len(players)))
	lines.append("Players.Lobby: {}".format(players_inlobby))
	lines.append("Players.Playing: {}".format(players_playing))

	output_file.write('\n'.join(lines))


class Server:
	def __init__(self, hostname, port, statistic_file=None):
		packets.SafeUnpickler.set_mode(client=False)
		self.host     = None
		self.hostname = hostname
		self.port     = port
		self.statistic = {
			'file':      statistic_file,
			'timestamp': 0,
			'interval':  1 * 60 * 1000,
		}
		self.capabilities = {
			'minplayers'    : 2,
			'maxplayers'    : 8,
			# NOTE: this defines the global packet size maximum.
			# there's still a per packet maximum defined in the
			# individual packet classes
			'maxpacketsize' : 2 * 1024 * 1024,
		}
		self.events = SimpleMessageBus(EVENTS)

		callbacks = {
			'onconnect': self.onconnect,
			'ondisconnect': self.ondisconnect,
			'onreceive': self.onreceive,
			packets.cmd_error: self.onerror,
			packets.cmd_fatalerror: self.onfatalerror,
			packets.client.cmd_sessionprops: self.onsessionprops,
			packets.client.cmd_creategame: self.oncreategame,
			packets.client.cmd_listgames: self.onlistgames,
			packets.client.cmd_joingame: self.onjoingame,
			packets.client.cmd_leavegame: self.onleavegame,
			packets.client.cmd_chatmsg: self.onchat,
			packets.client.cmd_changename: self.onchangename,
			packets.client.cmd_changecolor: self.onchangecolor,
			packets.client.cmd_preparedgame: self.onpreparedgame,
			packets.client.cmd_toggleready: self.ontoggleready,
			packets.client.cmd_kickplayer: self.onkick,
			#TODO packets.client.cmd_fetch_game: self.onfetchgame,
			#TODO packets.client.savegame_data: self.onsavegamedata,
			'preparegame': self.preparegame,
			'startgame': self.startgame,
			'leavegame': self.leavegame,
			'deletegame': self.deletegame,
			'terminategame': self.terminategame,
			'gamedata': self.gamedata,
		}

		for event_name, callback in callbacks.items():
			self.events.subscribe(event_name, callback)

		self.games   = [] # type: List[Game]
		self.players = {} # type: Dict[str, Player]
		self.i18n    = {} # type: Dict[str, gettext.GNUTranslations]
		self.setup_i18n()

	def setup_i18n(self):
		"""
		Load available translations for server messages.
		"""
		domain = 'unknown-horizons-server'
		for lang, dir in find_available_languages(domain).items():
			if len(dir) <= 0:
				continue
			try:
				self.i18n[lang] = gettext.translation(domain, dir, [lang])
			except IOError:
				pass

	@staticmethod
	def generate_session_id():
		return uuid.uuid4().hex

	def collect_statistics(self):
		"""
		Regularly collect statistics about the server (only when enabled explicitly).
		"""
		if self.statistic['file'] is None:
			return

		if self.statistic['timestamp'] > 0:
			self.statistic['timestamp'] -= CONNECTION_TIMEOUT
			return

		try:
			with open(self.statistic['file'], 'w') as f:
				print_statistic(self.players.values(), self.games, f)
		except IOError as e:
			logging.error("[STATISTIC] Unable to open statistic file: {}".format(e))

		self.statistic['timestamp'] = self.statistic['interval']

	def run(self):
		"""
		Main loop of the server
		"""
		logging.info("Starting up server on {0!s}:{1:d}".format(self.hostname, self.port))
		try:
			self.host = enet.Host(enet.Address(self.hostname, self.port), MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError) as e:
			# these exceptions do not provide any information.
			raise network.NetworkException("Unable to create network structure: {0!s}".format((e)))

		logging.debug("Entering the main loop...")
		while True:
			self.collect_statistics()

			event = self.host.service(CONNECTION_TIMEOUT)
			if event.type == enet.EVENT_TYPE_NONE:
				continue
			elif event.type == enet.EVENT_TYPE_CONNECT:
				self.events.broadcast("onconnect", event)
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				self.events.broadcast("ondisconnect", event)
			elif event.type == enet.EVENT_TYPE_RECEIVE:
				self.events.broadcast("onreceive", event)
			else:
				logging.warning("Invalid packet ({0})".format(event.type))

	def send(self, peer: 'enet.Peer', packet: packets.packet):
		"""
		Sends a packet to a client.
		"""
		if self.host is None:
			raise network.NotConnected("Server is not running")

		self.send_raw(peer, packet.serialize())

	def send_raw(self, peer: 'enet.Peer', data: bytes):
		"""
		Sends raw data to a client.
		"""
		if self.host is None:
			raise network.NotConnected("Server is not running")

		packet = enet.Packet(data, enet.PACKET_FLAG_RELIABLE)
		peer.send(0, packet)
		self.host.flush()

	def disconnect(self, peer, later=True):
		logging.debug("[DISCONNECT] Disconnecting client {0!s}".format(peer.address))
		try:
			if later:
				peer.disconnect_later()
			else:
				peer.disconnect()
		except IOError:
			peer.reset()


	def error(self, player, message, _type=ErrorType.NotSet):
		self._error(player.peer, player.gettext(message), _type)

	def _error(self, peer, message, _type=ErrorType.NotSet):
		self.send(peer, packets.cmd_error(message, _type))

	def fatalerror(self, player, message, later=True):
		self._fatalerror(player.peer, player.gettext(message), later)

	def _fatalerror(self, peer, message, later=True):
		self.send(peer, packets.cmd_fatalerror(message))
		self.disconnect(peer, later)


	def onconnect(self, event):
		peer = event.peer
		# disable that check as peer.data may be uninitialized which segfaults then
		#if peer.data in self.players:
		#	logging.warning("[CONNECT] Already known player %s!" % (peer.address))
		#	self._fatalerror(event.peer, "You can't connect more than once")
		#	return
		player = Player(event.peer, self.generate_session_id(), event.data)
		logging.debug("[CONNECT] New Client: {0!s}".format(player))

		# store session id inside enet.peer.data
		# NOTE: ALWAYS initialize peer.data
		session_id = bytes(player.sid, 'ascii')
		event.peer.data = session_id

		if player.protocol not in PROTOCOLS:
			logging.warning("[CONNECT] {0!s} runs old or unsupported protocol".format(player))
			self.fatalerror(player, T("Old or unsupported multiplayer protocol. Please check your game version"))
			return

		# NOTE: copying bytes or int doesn't work here
		self.players[session_id] = player
		self.send(event.peer, packets.server.cmd_session(player.sid, self.capabilities))


	def ondisconnect(self, event):
		peer = event.peer
		# check need for early disconnects (e.g. old protocol)
		if peer.data not in self.players:
			return
		player = self.players[peer.data]
		logging.debug("[DISCONNECT] {0!s} disconnected".format(player))
		if player.game is not None:
			self.events.broadcast("leavegame", player)
		del self.players[peer.data]


	def onreceive(self, event):
		peer = event.peer
		#logging.debug("[RECEIVE] Got data from %s" % (peer.address))
		# check player is known by server
		if peer.data not in self.players:
			logging.warning("[RECEIVE] Packet from unknown player {0!s}!".format(peer.address))
			self._fatalerror(event.peer, "I don't know you")
			return

		player = self.players[peer.data]

		# check packet size
		if len(event.packet.data) > self.capabilities['maxpacketsize']:
			logging.warning("[RECEIVE] Global packet size exceeded from {0!s}: size={1:d}".
				format(peer.address, len(event.packet.data)))
			self.fatalerror(player, T("You've exceeded the global packet size.") + " " +
			                        T("This should never happen. "
			                          "Please contact us or file a bug report."))
			return

		# shortpath if game is running
		if player.game is not None and player.game.state is Game.State.Running:
			self.events.broadcast('gamedata', player, event.packet.data)
			return

		packet = None
		try:
			packet = packets.unserialize(event.packet.data, True, player.protocol)
		except network.SoftNetworkException as e:
			self.error(player, str(e))
			return
		except network.PacketTooLarge as e:
			logging.warning("[RECEIVE] Per packet size exceeded from {0!s}: {1!s}".
				format(player, e))
			self.fatalerror(player, T("You've exceeded the per packet size.") + " " +
			                        T("This should never happen. "
			                          "Please contact us or file a bug report.") +
			                        " " + str(e))
			return
		except Exception as e:
			logging.warning("[RECEIVE] Unknown or malformed packet from {0!s}: {1!s}".
				format(player, e))
			self.fatalerror(player, T("Unknown or malformed packet. Please check your game version"))
			return

		# session id check
		if packet.sid != player.sid:
			logging.warning(
				"[RECEIVE] Invalid session id for player {0!s} ({1!s} vs {2!s})!".
				format(peer.address, packet.sid, player.sid))
			# this will trigger ondisconnect() for cleanup
			self.fatalerror(player, T("Invalid/Unknown session"))
			return

		if not self.events.is_message_type_known(packet.__class__):
			logging.warning("[RECEIVE] Unhandled network packet from {0!s} - Ignoring!".
				format(peer.address))
			return
		self.events.broadcast(packet.__class__, player, packet)


	def onerror(self, player, packet):
		# we shouldn't receive any errors from client
		# so ignore them all
		logging.debug("[ERROR] Client Message: {0!s}".format(packet.errorstr))


	def onfatalerror(self, player, packet):
		# we shouldn't receive any fatala errors from client
		# so just disconnect them
		logging.debug("[FATAL] Client Message: {0!s}".format(packet.errorstr))
		self.disconnect(player.peer)


	def onsessionprops(self, player, packet):
		logging.debug("[PROPS] {0!s}".format(player))
		if hasattr(packet, 'lang'):
			if packet.lang in self.i18n:
				player.gettext = self.i18n[packet.lang].gettext
		self.send(player.peer, packets.cmd_ok())

	def oncreategame(self, player, packet):
		if packet.maxplayers < self.capabilities['minplayers']:
			raise network.SoftNetworkException(
				"You can't run a game with less than {0:d} players".
				format(self.capabilities['minplayers']))
		if packet.maxplayers > self.capabilities['maxplayers']:
			raise network.SoftNetworkException(
				"You can't run a game with more than {0:d} players".
				format(self.capabilities['maxplayers']))
		game = Game(packet, player)
		logging.debug("[CREATE] [{0!s}] {1!s} created {2!s}".format(game.uuid, player, game))
		self.games.append(game)
		self.send(player.peer, packets.server.data_gamestate(game))

	def deletegame(self, game):
		logging.debug("[REMOVE] [{0!s}] {1!s} removed".format(game.uuid, game))
		game.clear()
		self.games.remove(game)

	def onlistgames(self, player, packet):
		logging.debug("[LIST]")
		gameslist = packets.server.data_gameslist()
		for _game in self.games:
			if _game.creator.protocol != player.protocol:
				continue
			if not _game.is_open():
				continue
			if _game.is_full():
				continue
			if packet.clientversion != -1 and packet.clientversion != _game.creator.version:
				continue
			if packet.mapname and packet.mapname != _game.mapname:
				continue
			if packet.maxplayers and packet.maxplayers != _game.maxplayers:
				continue
			gameslist.addgame(_game)
		self.send(player.peer, gameslist)


	def __find_game_from_uuid(self, packet):
		game = None
		for _game in self.games:
			if packet.clientversion != _game.creator.version:
				continue
			if packet.uuid != _game.uuid:
				continue
			game = _game
			break
		return game


	def onjoingame(self, player, packet):
		if player.game is not None:
			self.error(player, T("You can't join a game while in another game"))
			return

		game = self.__find_game_from_uuid(packet)
		if game is None:
			self.error(player, T("Unknown game or game is running a different version"))
			return
		if not game.is_open():
			self.error(player, T("Game has already started. No more joining"))
			return
		if game.is_full():
			self.error(player, T("Game is full"))
			return
		if game.has_password() and packet.password != game.password:
			self.error(player, T("Wrong password"))
			return

		# protocol=0
		# assign free color
		if packet.playercolor is None:
			colors = []
			for _player in game.players:
				colors.append(_player.color)
			for color in range(1, len(colors) + 2):
				if color not in colors:
					break
			packet.playercolor = color

		# make sure player names, colors and clientids are unique
		for _player in game.players:
			if _player.name == packet.playername:
				self.error(player, T("There's already a player with your name inside this game.") + " " +
				                   T("Please change your name."))
				return
			if _player.color == packet.playercolor:
				self.error(player, T("There's already a player with your color inside this game.") + " " +
				                   T("Please change your color."))
				return
			if _player.clientid == packet.clientid:
				self.error(player, T("There's already a player with your unique player ID inside this game. "
				                     "This should never occur."))
				return

		logging.debug("[JOIN] [{0!s}] {1!s} joined {2!s}".format(game.uuid, player, game))
		game.add_player(player, packet)
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))

		if player.protocol == 0:
			if game.is_full():
				self.events.broadcast("preparegame", game)


	def onleavegame(self, player, packet):
		if player.game is None:
			self.error(player, T("You are not inside a game"))
			return
		self.events.broadcast("leavegame", player)
		self.send(player.peer, packets.cmd_ok())


	def leavegame(self, player):
		game = player.game
		# leaving the game if game has already started is a hard error
		if not game.is_open():
			self.events.broadcast('terminategame', game, player)
			return
		logging.debug("[LEAVE] [{0!s}] {1!s} left {2!s}".format(game.uuid, player, game))
		game.remove_player(player)
		if game.is_empty():
			self.events.broadcast('deletegame', game)
			return
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))
		# the creator leaving the game is a hard error too
		if player.protocol >= 1 and player == game.creator:
			self.events.broadcast('terminategame', game, player)
			return


	def terminategame(self, game, player=None):
		logging.debug("[TERMINATE] [{0!s}] (by {1!s})".
			format(game.uuid, player if player is not None else None))
		if game.creator.protocol >= 1 and game.is_open():
			# NOTE: works with protocol >= 1
			for _player in game.players:
				self.error(_player, T("The game has been terminated. The creator has left the game."), ErrorType.TerminateGame)
		else:
			for _player in game.players:
				if _player.peer.state == enet.PEER_STATE_CONNECTED:
					self.fatalerror(_player,
						T("One player has terminated their game. "
						"For technical reasons, this currently means the game cannot continue. "
						"We are very sorry about that."))
		self.events.broadcast('deletegame', game)


	def preparegame(self, game):
		logging.debug("[PREPARE] [{0!s}] Players: {1!s}".
			format(game.uuid, [str(i) for i in game.players]))
		game.state = Game.State.Prepare
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_preparegame())


	def startgame(self, game):
		logging.debug("[START] [{0!s}] Players: {1!s}".
			format(game.uuid, [str(i) for i in game.players]))
		game.state = Game.State.Running
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_startgame())


	def onchat(self, player, packet):
		if player.game is None:
			# just ignore if not inside a game
			self.send(player.peer, packets.cmd_ok())
			return
		game = player.game
		# don't send packets to already started games
		if not game.is_open():
			return
		logging.debug("[CHAT] [{0!s}] {1!s}: {2!s}".format(game.uuid, player, packet.chatmsg))
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_chatmsg(player.name, packet.chatmsg))


	def onchangename(self, player, packet):
		# NOTE: that event _only_ happens inside a lobby
		if player.game is None:
			# just ignore if not inside a game
			self.send(player.peer, packets.cmd_ok())
			return
		# ignore change to existing name
		if player.name == packet.playername:
			return
		game = player.game
		# don't send packets to already started games
		if not game.is_open():
			return

		# make sure player names are unique
		for _player in game.players:
			if _player.name == packet.playername:
				self.error(player, T("There's already a player with your name inside this game.") + " " +
				                   T("Unable to change your name."))
				return

		# ACK the change
		logging.debug("[CHANGENAME] [{0!s}] {1!s} -> {2!s}".
			format(game.uuid, player.name, packet.playername))
		player.name = packet.playername
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))


	def onchangecolor(self, player, packet):
		# NOTE: that event _only_ happens inside a lobby
		if player.game is None:
			# just ignore if not inside a game
			self.send(player.peer, packets.cmd_ok())
			return
		# ignore change to same color
		if player.color == packet.playercolor:
			return
		game = player.game
		# don't send packets to already started games
		if not game.is_open():
			return

		# make sure player colors are unique
		for _player in game.players:
			if _player.color == packet.playercolor:
				self.error(player, T("There's already a player with your color inside this game.") + " " +
				                   T("Unable to change your color."))
				return

		# ACK the change
		logging.debug("[CHANGECOLOR] [{0!s}] Player:{1!s} {2!s} -> {3!s}".
			format(game.uuid, player.name, player.color, packet.playercolor))
		player.color = packet.playercolor
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))


	def gamedata(self, player, data):
		game = player.game
		#logging.debug("[GAMEDATA] [%s] %s" % (game.uuid, player))
		for _player in game.players:
			if _player is player:
				continue
			self.send_raw(_player.peer, data)


	# this event happens after a player is done with loading
	# and ready to start the game. we need to wait for all players
	def onpreparedgame(self, player, packet):
		game = player.game
		if game is None:
			return
		logging.debug("[PREPARED] [{0!s}] {1!s}".format(game.uuid, player))
		player.prepared = True
		count = 0
		for _player in game.players:
			if _player.prepared:
				count += 1
		if count != game.playercnt:
			return
		self.events.broadcast('startgame', game)


	def ontoggleready(self, player, packet):
		game = player.game
		if game is None:
			return
		# don't send packets to already started games
		if not game.is_open():
			return

		# ACK the change
		player.toggle_ready()
		logging.debug("[TOGGLEREADY] [{0!s}] Player:{1!s} {2!s} ready".
			format(game.uuid, player.name, "is not" if not player.ready else "is"))
		for _player in game.players:
			self.send(_player.peer, packets.server.data_gamestate(game))

		# start the game after the ACK
		if game.is_ready():
			self.events.broadcast("preparegame", game)


	def onkick(self, player, packet):
		game = player.game
		if game is None:
			return
		# don't send packets to already started games
		if not game.is_open():
			return
		if player is not game.creator:
			return

		kickplayer = None
		for _player in game.players:
			if _player.sid == packet.kicksid:
				kickplayer = _player
				break
		if kickplayer is None:
			return
		if kickplayer is game.creator:
			return

		logging.debug("[KICK] [{0!s}] {1!s} got kicked".format(game.uuid, kickplayer.name))
		for _player in game.players:
			self.send(_player.peer, packets.server.cmd_kickplayer(kickplayer))
		self.events.broadcast("leavegame", kickplayer)


	#TODO fix
	def onfetchgame(self, player, packet):
		game = player.game

		if game is not None:
			self.error(player, T("You can't fetch a game while in another game"))

		fetch_game = self.__find_game_from_uuid(packet)
		for _player in fetch_game.players:
			if _player.name == fetch_game.creator: #TODO
				self.send(_player.peer, packets.server.cmd_fetch_game(player.sid))


	#TODO fix
	def onsavegamedata(self, player, packet):
		game = player.game

		for _player in game.players:
			if _player.sid == packet.psid:
				self.send(_player.peer, packets.server.savegame_data(packet.data, player.sid, game.mapname))
