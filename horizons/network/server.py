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
from typing import Dict, List, Optional, Text

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

logging.basicConfig(format='[%(asctime)-15s] [%(levelname)s] %(message)s',
		level=logging.DEBUG)


EVENTS = [
	'on_connect',
	'on_disconnect',
	'on_receive_data',
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
		self.host = None # type: Optional[enet.Host]
		self.hostname = hostname
		self.port = port
		self.statistic = {
			'file':      statistic_file,
			'timestamp': 0,
			'interval':  1 * 60 * 1000,
		}
		self.capabilities = {
			'minplayers': 2,
			'maxplayers': 8,
			# NOTE: this defines the global packet size maximum.
			# there's still a per packet maximum defined in the
			# individual packet classes
			'maxpacketsize': 2 * 1024 * 1024,
		}
		self.events = SimpleMessageBus(EVENTS)

		callbacks = {
			'on_connect': self.on_connect,
			'on_disconnect': self.on_disconnect,
			'on_receive_data': self.on_receive_data,
			packets.cmd_error: self.on_error,
			packets.cmd_fatalerror: self.on_fatalerror,
			packets.client.cmd_sessionprops: self.on_sessionprops,
			packets.client.cmd_creategame: self.on_creategame,
			packets.client.cmd_listgames: self.on_listgames,
			packets.client.cmd_joingame: self.on_joingame,
			packets.client.cmd_leavegame: self.on_leavegame,
			packets.client.cmd_chatmsg: self.on_chat,
			packets.client.cmd_changename: self.on_changename,
			packets.client.cmd_changecolor: self.on_changecolor,
			packets.client.cmd_preparedgame: self.on_preparedgame,
			packets.client.cmd_toggleready: self.on_toggleready,
			packets.client.cmd_kickplayer: self.on_kick,
			#TODO packets.client.cmd_fetch_game: self.on_fetchgame,
			#TODO packets.client.savegame_data: self.on_savegamedata,
			'preparegame': self.preparegame,
			'startgame': self.startgame,
			'leavegame': self.leavegame,
			'deletegame': self.deletegame,
			'terminategame': self.terminategame,
			'gamedata': self.gamedata,
		}

		for event_name, callback in callbacks.items():
			self.events.subscribe(event_name, callback)

		self.games = [] # type: List[Game]
		self.players = {} # type: Dict[bytes, Player]
		self.i18n = {} # type: Dict[str, gettext.GNUTranslations]
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
				self.events.broadcast("on_connect", event)
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				self.events.broadcast("on_disconnect", event)
			elif event.type == enet.EVENT_TYPE_RECEIVE:
				self.events.broadcast("on_receive_data", event)
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

	def send_to_game(self, game: Game, packet: packets.packet):
		"""
		Send a packet to all players of a game.
		"""
		for player in game.players:
			self.send(player.peer, packet)

	def disconnect(self, peer: 'enet.Peer', later=True):
		"""
		Disconnect a client.
		"""
		logging.debug("[DISCONNECT] Disconnecting client {0!s}".format(peer.address))
		try:
			if later:
				peer.disconnect_later()
			else:
				peer.disconnect()
		except IOError:
			peer.reset()

	def error(self, player: Player, message: Text, _type=ErrorType.NotSet):
		"""
		Send an error message to a player.
		"""
		self._error(player.peer, player.gettext(message), _type)

	def _error(self, peer: 'enet.Peer', message: Text, _type=ErrorType.NotSet):
		"""
		Send an error message to a client.
		"""
		self.send(peer, packets.cmd_error(message, _type))

	def fatal_error(self, player: Player, message: Text):
		"""
		Send an error message to a player and disconnect.
		"""
		self._fatal_error(player.peer, player.gettext(message))

	def _fatal_error(self, peer: 'enet.Peer', message: Text):
		"""
		Send an error message to a client and disconnect.
		"""
		self.send(peer, packets.cmd_fatalerror(message))
		self.disconnect(peer, later=True)

	# Basic event handling

	def on_connect(self, event: 'enet.Event'):
		"""
		When a client connect, add it to the list of players.

		NOTE: We can't look at `event.peer.data` to figure out whether or not we know this
		      client already since the access will segfault the interpreter.
		"""
		peer = event.peer
		player = Player(event.peer, self.generate_session_id(), event.data)
		logging.debug("[CONNECT] New Client: {}".format(player))

		# NOTE: ALWAYS initialize peer.data
		session_id = bytes(player.sid, 'ascii')
		event.peer.data = session_id

		if player.protocol not in PROTOCOLS:
			logging.warning("[CONNECT] {} runs old or unsupported protocol".format(player))
			self.fatal_error(player, T("Old or unsupported multiplayer protocol. Please check your game version"))
			return

		# NOTE: copying bytes or int doesn't work here
		self.players[session_id] = player
		self.send(event.peer, packets.server.cmd_session(player.sid, self.capabilities))

	def on_disconnect(self, event: 'enet.Event'):
		"""
		When a client closes the connection, remove it from the player list.
		"""
		peer = event.peer
		# check need for early disconnects (e.g. old protocol)
		if peer.data not in self.players:
			return
		player = self.players.pop(peer.data)
		logging.debug("[DISCONNECT] {} disconnected".format(player))
		if player.game is not None:
			self.events.broadcast("leavegame", player)

	def on_receive_data(self, event: 'enet.Event'):
		"""
		Handle received packets from the client.
		"""
		peer = event.peer
		if peer.data not in self.players:
			logging.warning("[RECEIVE] Packet from unknown player {}!".format(peer.address))
			self._fatal_error(event.peer, "I don't know you")
			return

		player = self.players[peer.data]

		# check packet size
		if len(event.packet.data) > self.capabilities['maxpacketsize']:
			logging.warning("[RECEIVE] Global packet size exceeded from {}: size={}".
				format(peer.address, len(event.packet.data)))
			self.fatal_error(player, T("You've exceeded the global packet size.") + " " +
			                         T("This should never happen. "
			                           "Please contact us or file a bug report."))
			return

		# shortpath if game is running
		if player.game and player.game.state is Game.State.Running:
			self.events.broadcast('gamedata', player, event.packet.data)
			return

		packet = None
		try:
			packet = packets.unserialize(event.packet.data, True, player.protocol)
		except network.SoftNetworkException as e:
			self.error(player, str(e))
			return
		except network.PacketTooLarge as e:
			logging.warning("[RECEIVE] Per packet size exceeded from {}: {}".
				format(player, e))
			self.fatal_error(player, T("You've exceeded the per packet size.") + " " +
			                         T("This should never happen. "
			                           "Please contact us or file a bug report.") +
			                           " " + str(e))
			return
		except Exception as e:
			logging.warning("[RECEIVE] Unknown or malformed packet from {}: {}".
				format(player, e))
			self.fatal_error(player, T("Unknown or malformed packet. Please check your game version"))
			return

		# session id check
		if packet.sid != player.sid:
			logging.warning(
				"[RECEIVE] Invalid session id for player {} ({} vs {})!".
				format(peer.address, packet.sid, player.sid))
			self.fatal_error(player, T("Invalid/Unknown session"))
			return

		if not self.events.is_message_type_known(packet.__class__):
			logging.warning("[RECEIVE] Unhandled network packet from {} - Ignoring!".
				format(peer.address))
			return

		self.events.broadcast(packet.__class__, player, packet)

	def on_error(self, player: Player, packet: packets.cmd_error):
		"""
		We shouldn't receive any errors from client, so ignore them all.
		"""
		logging.debug("[ERROR] Client Message: {}".format(packet.errorstr))

	def on_fatalerror(self, player: Player, packet: packets.cmd_fatalerror):
		"""
		We shouldn't receive any fatal errors from client, so just disconnect them.
		"""
		logging.debug("[FATAL] Client Message: {}".format(packet.errorstr))
		self.disconnect(player.peer)

	# Game specific event handling

	def on_sessionprops(self, player: Player, packet: packets.client.cmd_sessionprops):
		"""
		Client sends us specific settings / preferences for this session, for example the
		language.
		"""
		logging.debug("[PROPS] {}".format(player))
		if hasattr(packet, 'lang'):
			if packet.lang in self.i18n:
				player.gettext = self.i18n[packet.lang].gettext
		self.send(player.peer, packets.cmd_ok())

	def on_creategame(self, player: Player, packet: packets.client.cmd_creategame):
		"""
		A client wants to create a new game.
		"""
		if packet.maxplayers < self.capabilities['minplayers']:
			raise network.SoftNetworkException(
				"You can't run a game with less than {} players".
				format(self.capabilities['minplayers']))
		if packet.maxplayers > self.capabilities['maxplayers']:
			raise network.SoftNetworkException(
				"You can't run a game with more than {} players".
				format(self.capabilities['maxplayers']))
		game = Game(packet, player)
		logging.debug("[CREATE] [{}] {} created {}".format(game.uuid, player, game))
		self.games.append(game)
		self.send(player.peer, packets.server.data_gamestate(game))

	def on_listgames(self, player: Player, packet: packets.client.cmd_listgames):
		"""
		Send the client a list of all available games on this server.
		"""
		logging.debug("[LIST]")
		response = packets.server.data_gameslist()
		for game in self.games:
			if game.creator.protocol != player.protocol:
				continue
			if not game.is_open():
				continue
			if game.is_full():
				continue
			if packet.clientversion != -1 and packet.clientversion != game.creator.version:
				continue
			if packet.mapname and packet.mapname != game.mapname:
				continue
			if packet.maxplayers and packet.maxplayers != game.maxplayers:
				continue
			response.addgame(game)

		self.send(player.peer, response)

	def on_joingame(self, player: Player, packet: packets.client.cmd_joingame):
		"""
		A player wants to join a game.
		"""
		if player.game is not None:
			self.error(player, T("You can't join a game while in another game"))
			return

		game = self._find_game_from_uuid(packet.uuid, packet.clientversion)
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

		# make sure player names, colors and clientids are unique
		for other_player in game.players:
			if other_player.name == packet.playername:
				self.error(player, T("There's already a player with your name inside this game.") + " " +
				                   T("Please change your name."))
				return
			if other_player.color == packet.playercolor:
				self.error(player, T("There's already a player with your color inside this game.") + " " +
				                   T("Please change your color."))
				return
			if other_player.clientid == packet.clientid:
				self.error(player, T("There's already a player with your unique player ID inside this game. "
				                     "This should never occur."))
				return

		logging.debug("[JOIN] [{}] {} joined {}".format(game.uuid, player, game))
		game.add_player(player, packet)
		self.send_to_game(game, packets.server.data_gamestate(game))

	def on_leavegame(self, player: Player, packet: packets.client.cmd_leavegame):
		"""
		Player wants to leave the current game.
		"""
		if player.game is None:
			self.error(player, T("You are not inside a game"))
			return
		self.events.broadcast("leavegame", player)
		self.send(player.peer, packets.cmd_ok())

	def on_chat(self, player: Player, packet: packets.client.cmd_chatmsg):
		"""
		Player send a chat message.
		"""
		if player.game is None:
			# just ignore if not inside a game
			self.send(player.peer, packets.cmd_ok())
			return

		game = player.game
		# don't send packets to already started games
		if not game.is_open():
			return

		logging.debug("[CHAT] [{}] {}: {}".format(game.uuid, player, packet.chatmsg))
		self.send_to_game(game, packets.server.cmd_chatmsg(player.name, packet.chatmsg))

	def on_changename(self, player: Player, packet: packets.client.cmd_changename):
		"""
		Player wants to change its name.

		NOTE: that event _only_ happens inside a lobby
		"""
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
		if packet.playername in [p.name for p in game.players]:
			self.error(player, T("There's already a player with your name inside this game.") + " " +
					   T("Unable to change your name."))
			return

		# ACK the change
		logging.debug("[CHANGENAME] [{}] {} -> {}".
			format(game.uuid, player.name, packet.playername))
		player.name = packet.playername
		self.send_to_game(game, packets.server.data_gamestate(game))

	def on_changecolor(self, player: Player, packet: packets.client.cmd_changecolor):
		"""
		Player wants to change its color.

		NOTE: that event _only_ happens inside a lobby
		"""
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
		if packet.playercolor in [p.color for p in game.players]:
			self.error(player, T("There's already a player with your color inside this game.") + " " +
					   T("Unable to change your color."))
			return

		# ACK the change
		logging.debug("[CHANGECOLOR] [{}] Player:{} {} -> {}".
			format(game.uuid, player.name, player.color, packet.playercolor))
		player.color = packet.playercolor
		self.send_to_game(game, packets.server.data_gamestate(game))

	def on_preparedgame(self, player: Player, packet: packets.client.cmd_preparedgame):
		"""
		This event happens after a player is done with loading and ready to start the
		game. We need to wait for all players.
		"""
		game = player.game
		if game is None:
			return

		logging.debug("[PREPARED] [{}] {}".format(game.uuid, player))
		player.prepared = True

		if not all(p.prepared for p in game.players):
			return

		self.events.broadcast('startgame', game)

	def on_toggleready(self, player: Player, packet: packets.client.cmd_toggleready):
		"""
		Player signals whether it is ready to start the game.
		"""
		game = player.game
		if game is None:
			return

		# don't send packets to already started games
		if not game.is_open():
			return

		# ACK the change
		player.toggle_ready()
		logging.debug("[TOGGLEREADY] [{}] Player:{} is{} ready".
			format(game.uuid, player.name, "is not" if not player.ready else "is"))
		self.send_to_game(game, packets.server.data_gamestate(game))

		# start the game after the ACK
		if game.is_ready():
			self.events.broadcast("preparegame", game)

	def on_kick(self, player: Player, packet: packets.client.cmd_kickplayer):
		"""
		A player should should be kicked from the game.
		"""
		game = player.game
		if game is None:
			return
		# don't send packets to already started games
		if not game.is_open():
			return
		if player is not game.creator:
			return

		kickplayer = game.find_player_by_sid(packet.kicksid)
		if kickplayer is None:
			return
		if kickplayer is game.creator:
			return

		logging.debug("[KICK] [{}] {} got kicked".format(game.uuid, kickplayer.name))
		self.send_to_game(game, packets.server.cmd_kickplayer(kickplayer))
		self.events.broadcast("leavegame", kickplayer)

	#TODO fix
	def onfetchgame(self, player, packet):
		game = player.game

		if game is not None:
			self.error(player, T("You can't fetch a game while in another game"))

		fetch_game = self._find_game_from_uuid(packet.uuid, packet.clientversion)
		for _player in fetch_game.players:
			if _player.name == fetch_game.creator: #TODO
				self.send(_player.peer, packets.server.cmd_fetch_game(player.sid))

	#TODO fix
	def onsavegamedata(self, player, packet):
		game = player.game

		for _player in game.players:
			if _player.sid == packet.psid:
				self.send(_player.peer, packets.server.savegame_data(packet.data, player.sid, game.mapname))

	def _find_game_from_uuid(self, uuid: str, client_version: str) -> Optional[Game]:
		"""
		Returns a game with a given uuid.
		"""
		for game in self.games:
			if client_version != game.creator.version:
				continue
			if uuid != game.uuid:
				continue

			return game

	def deletegame(self, game: Game):
		"""
		Remove the game from the server.
		"""
		logging.debug("[REMOVE] [{}] {} removed".format(game.uuid, game))
		game.clear()
		self.games.remove(game)

	def leavegame(self, player: Player):
		"""
		Remove player from the active game.
		"""
		game = player.game
		# leaving the game if game has already started is a hard error
		if not game.is_open():
			self.events.broadcast('terminategame', game, player)
			return

		logging.debug("[LEAVE] [{}] {} left {}".format(game.uuid, player, game))
		game.remove_player(player)
		if game.is_empty():
			self.events.broadcast('deletegame', game)
			return
		for player in game.players:
			self.send(player.peer, packets.server.data_gamestate(game))

		# the creator leaving the game is a hard error too
		if player.protocol >= 1 and player == game.creator:
			self.events.broadcast('terminategame', game, player)
			return

	def terminategame(self, game: Game, player=None):
		"""
		Forcefully end the game.
		"""
		logging.debug("[TERMINATE] [{}] (by {})".
			format(game.uuid, player if player is not None else None))
		if game.creator.protocol >= 1 and game.is_open():
			# NOTE: works with protocol >= 1
			for p in game.players:
				self.error(p, T("The game has been terminated. The creator has left the game."), ErrorType.TerminateGame)
		else:
			for p in game.players:
				if p.peer.state == enet.PEER_STATE_CONNECTED:
					self.fatal_error(p,
						T("One player has terminated their game. "
						"For technical reasons, this currently means the game cannot continue. "
						"We are very sorry about that."))
		self.events.broadcast('deletegame', game)

	def preparegame(self, game: Game):
		"""
		Instruct all players to start loading the game.
		"""
		logging.debug("[PREPARE] [{}] Players: {}".
			format(game.uuid, [str(i) for i in game.players]))
		game.state = Game.State.Prepare
		self.send_to_game(game, packets.server.cmd_preparegame())

	def startgame(self, game: Game):
		"""
		Instruct all players to start the game.
		"""
		logging.debug("[START] [{}] Players: {}".
			format(game.uuid, [str(i) for i in game.players]))
		game.state = Game.State.Running
		self.send_to_game(game, packets.server.cmd_startgame())

	def gamedata(self, player: Player, data: bytes):
		"""
		Broadcast game data from a single client to all others in the game.
		"""
		game = player.game
		for p in game.players:
			if p is player:
				continue
			self.send_raw(p.peer, data)
