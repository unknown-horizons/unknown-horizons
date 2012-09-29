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
import datetime
import bz2

from horizons.network import packets
from horizons import network
from horizons.network.common import *
from horizons.network import find_enet_module
from horizons.savegamemanager import SavegameManager

enet = find_enet_module()
# during pyenets move to cpython they renamed a few constants...
if not hasattr(enet, 'PEER_STATE_DISCONNECTED') and hasattr(enet, 'PEER_STATE_DISCONNECT'):
	enet.PEER_STATE_DISCONNECTED = enet.PEER_STATE_DISCONNECT

# maximal peers enet should handle
MAX_PEERS = 1
# time in ms the client will wait for a packet
# on error client may wait twice that time
SERVER_TIMEOUT = 5000
# current server/client protocol the client understands
# increment that after incompatible protocol changes
SERVER_PROTOCOL = 1

class ClientMode(object):
	Server = 0
	Game = 1

class Client(object):
	log = logging.getLogger("network")

	def __init__(self, name, version, server_address, client_address=None, color=None, clientid=None):
		try:
			clientaddress = enet.Address(client_address[0], client_address[1]) if client_address is not None else None
			self.host = enet.Host(clientaddress, MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError):
			# these exceptions do not provide any information.
			raise network.NetworkException("Unable to create network structure. Maybe invalid or irresolvable client address.")

		self.name          = name
		self.version       = version
		self.serveraddress = Address(server_address[0], server_address[1])
		self.serverpeer    = None
		self.mode          = None
		self.sid           = None
		self.capabilities  = None
		self.game          = None
		self.clientid      = clientid
		self.color         = color
		self.packetqueue   = []
		self.callbacks     = {
			'lobbygame_chat':        [],
			'lobbygame_join':        [],
			'lobbygame_leave':       [],
			'lobbygame_terminate':   [],
			'lobbygame_toggleready': [],
			'lobbygame_changename':  [],
			'lobbygame_kick':        [],
			'lobbygame_changecolor': [],
			'lobbygame_state':       [],
			'lobbygame_starts':      [],
			'game_starts':    [],
			'game_data':      [],
			'savegame_data':  [], #TODO
		}
		self.register_callback('lobbygame_changename',  self.onchangename, True)
		self.register_callback('lobbygame_changecolor', self.onchangecolor, True)
		pass

	def register_callback(self, type, callback, prepend=False, unique=True):
		if type in self.callbacks:
			if unique and callback in self.callbacks[type]:
				return
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

	#-----------------------------------------------------------------------------

	def connect(self):
		if self.serverpeer is not None:
			raise network.AlreadyConnected("We are already connected to a server")
		self.log.debug("[CONNECT] to server %s" % (self.serveraddress))
		try:
			self.serverpeer = self.host.connect(enet.Address(self.serveraddress.host,
			                                                 self.serveraddress.port),
			                                    1, SERVER_PROTOCOL)
		except (IOError, MemoryError):
			raise network.NetworkException("Unable to connect to server. Maybe invalid or irresolvable server address.")
		self.mode = ClientMode.Server
		event = self.host.service(SERVER_TIMEOUT)
		if event.type != enet.EVENT_TYPE_CONNECT:
			self.reset()
			raise network.UnableToConnect("Unable to connect to server")
		# wait for session id
		packet = self.recv_packet([packets.server.cmd_session])
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.cmd_session):
			raise network.CommandError("Unexpected packet")
		self.sid = packet[1].sid
		self.capabilities = packet[1].capabilities
		self.log.debug("[CONNECT] done (session=%s)" % (self.sid))

	#-----------------------------------------------------------------------------

	def disconnect(self, server_may_disconnect=False, later=False):
		""" disconnect should _never_ throw an exception """
		self.mode = None
		if self.serverpeer is None:
			return

		if self.serverpeer.state == enet.PEER_STATE_DISCONNECTED:
			self.reset()
			return

		try:
			# wait for a disconnect event or empty event
			if server_may_disconnect:
				while True:
					event = self.host.service(SERVER_TIMEOUT)
					if event.type == enet.EVENT_TYPE_DISCONNECT:
						break
					elif event.type == enet.EVENT_TYPE_NONE:
						break

			# disconnect from server if we're still connected
			if self.serverpeer.state != enet.PEER_STATE_DISCONNECTED:
				if later:
					self.serverpeer.disconnect_later()
				else:
					self.serverpeer.disconnect()
				while True:
					event = self.host.service(SERVER_TIMEOUT)
					if event.type == enet.EVENT_TYPE_DISCONNECT:
						break
					elif event.type == enet.EVENT_TYPE_NONE:
						raise IOError("No packet from server")
		except IOError:
			self.log.debug("[DISCONNECT] Error while disconnecting from server. Maybe server isn't answering any more")
		self.reset()
		self.log.debug("[DISCONNECT] done")

	#-----------------------------------------------------------------------------

	def isconnected(self):
		if self.serverpeer is None:
			return False
		return True

	#-----------------------------------------------------------------------------

	def reset(self):
		self.log.debug("[RESET]")
		if self.serverpeer is not None:
			self.serverpeer.reset()
			self.serverpeer = None
		self.mode = None
		self.game = None
		self.flush()

	#-----------------------------------------------------------------------------

	def flush(self):
		self.host.flush()

	#-----------------------------------------------------------------------------

	# enet doesn't need to send pings. instead we need to call enet_host_service
	# on a regular basis. we call this ping and save received events
	def ping(self):
		if self.serverpeer is None:
			raise network.NotConnected()
		packet = self.recv(0)
		if packet is not None:
			if not self.process_async_packet(packet):
				self.packetqueue.append(packet)
			return True
		return False

	#-----------------------------------------------------------------------------

	def send(self, packet, channelid=0):
		if self.serverpeer is None:
			raise network.NotConnected()
		if self.mode is ClientMode.Game:
			packet = packets.client.game_data(packet)
		packet.send(self.serverpeer, self.sid, channelid)

	#-----------------------------------------------------------------------------

	# wait for event from network
	def _recv_event(self, timeout=SERVER_TIMEOUT):
		if self.serverpeer is None:
			raise network.NotConnected()
		event = self.host.service(timeout)
		if event.type == enet.EVENT_TYPE_NONE:
			return None
		elif event.type == enet.EVENT_TYPE_DISCONNECT:
			self.reset()
			self.log.warning("Unexpected disconnect from %s" % (event.peer.address))
			raise network.CommandError("Unexpected disconnect from %s" % (event.peer.address))
		elif event.type == enet.EVENT_TYPE_CONNECT:
			self.reset()
			self.log.warning("Unexpected connection from %s" % (event.peer.address))
			raise network.CommandError("Unexpected connection from %s" % (event.peer.address))
		return event

	# receives event from network and returns the unpacked packet
	def recv(self, timeout=SERVER_TIMEOUT):
		event = self._recv_event(timeout)
		if event is None:
			return None
		elif event.type == enet.EVENT_TYPE_RECEIVE:
			packet = None
			try:
				packet = packets.unserialize(event.packet.data)
			except Exception as e:
				self.log.error("Unknown packet from %s!" % (event.peer.address))
				errstr = "Pickle/Security: %s" % (e)
				print "[FATAL] %s" % (errstr) # print that even when no logger is enabled!
				self.log.error("[FATAL] %s" % (errstr))
				self.disconnect()
				raise network.FatalError(errstr)

			if isinstance(packet, packets.cmd_error):
				# handle special errors here
				# FIXME: it's better to pass that to the interface,
				# but our ui error handler currently can't handle that

				# the game got terminated by the client
				if packet.type == ErrorType.TerminateGame:
					game = self.game
					# this will destroy self.game
					self.leavegame(stealth=True)
					self.call_callbacks("lobbygame_terminate", game, packet.errorstr)
					return None
				raise network.CommandError(packet.errorstr)
			elif isinstance(packet, packets.cmd_fatalerror):
				self.log.error("[FATAL] Network message: %s" % (packet.errorstr))
				self.disconnect(True)
				raise network.FatalError(packet.errorstr)
			return [event.peer, packet]

	# return the first received packet of type [in packettypes]
	def recv_packet(self, packettypes=None, timeout=SERVER_TIMEOUT):
		if self.packetqueue:
			if packettypes is None:
				return self.packetqueue.pop(0)
			for packettype in packettypes:
				for _packet in self.packetqueue:
					if not isinstance(_packet[1], packettype):
						continue
					self.packetqueue.remove(_packet)
					return _packet
		if packettypes is None:
			return self.recv(timeout)
		start = datetime.datetime.now()
		timeleft = timeout
		while timeleft > 0:
			packet = self.recv(timeleft)
			if packet is None:
				return None
			for packettype in packettypes:
				if isinstance(packet[1], packettype):
					return packet
			if not self.process_async_packet(packet):
				self.packetqueue.append(packet)
			timeleft -= (datetime.datetime.now() - start).seconds

	#-----------------------------------------------------------------------------

	# return True if packet was processed successfully
	# return False if packet should be queue
	def process_async_packet(self, packet):
		if packet is None:
			return True
		if isinstance(packet[1], packets.server.cmd_chatmsg):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.call_callbacks("lobbygame_chat", self.game, packet[1].playername, packet[1].chatmsg)
		elif isinstance(packet[1], packets.server.data_gamestate):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.call_callbacks("lobbygame_state", self.game, packet[1].game)

			oldplayers = list(self.game.players)
			self.game = packet[1].game

			# calculate changeset
			for pnew in self.game.players:
				found = None
				for pold in oldplayers:
					if pnew.sid == pold.sid:
						found = pold
						myself = (pnew.sid == self.sid)
						if pnew.name != pold.name:
							self.call_callbacks("lobbygame_changename", self.game, pold, pnew, myself)
						if pnew.color != pold.color:
							self.call_callbacks("lobbygame_changecolor", self.game, pold, pnew, myself)
						if pnew.ready != pold.ready:
							self.call_callbacks("lobbygame_toggleready", self.game, pold, pnew, myself)
						break
				if found is None:
					self.call_callbacks("lobbygame_join", self.game, pnew)
				else:
					oldplayers.remove(found)
			for pold in oldplayers:
				self.call_callbacks("lobbygame_leave", self.game, pold)
			return True
		elif isinstance(packet[1], packets.server.cmd_preparegame):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.ongameprepare()
		elif isinstance(packet[1], packets.server.cmd_startgame):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.ongamestart()
		elif isinstance(packet[1], packets.client.game_data):
			self.log.debug("[GAMEDATA] from %s" % (packet[0].address))
			self.call_callbacks("game_data", packet[1].data)
		elif isinstance(packet[1], packets.server.cmd_kickplayer):
			player = packet[1].player
			game = self.game
			myself = (player.sid == self.sid)
			if myself:
				# this will destroy self.game
				self.leavegame(stealth=True)
			self.call_callbacks("lobbygame_kick", game, player, myself)
		#TODO elif isinstance(packet[1], packets.server.cmd_fetch_game):
		#	if self.game is None:
		#		return True
		#	path = SavegameManager.get_multiplayersave_map(self.game.mapname)
		#	compressed_data = bz2.compress(open(path).read())
		#	self.send(packets.client.savegame_data(compressed_data, packet[1].psid))
		#elif isinstance(packet[1], packets.server.savegame_data):
		#	with open(SavegameManager.get_multiplayersave_map(packet[1].mapname), "w") as f:
		#		f.write(bz2.decompress(packet[1].data))
		#	self.call_callbacks("savegame_data", self.game)

		return False

	#-----------------------------------------------------------------------------

	def setprops(self, lang):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[SETPROPS]")
		self.send(packets.client.cmd_sessionprops(lang))
		packet = self.recv_packet([packets.cmd_ok])
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.cmd_ok):
			raise network.CommandError("Unexpected packet")
		return True

	#-----------------------------------------------------------------------------

	def listgames(self, mapname=None, maxplayers=None, only_this_version=False):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[LIST]")
		version = self.version if only_this_version else -1
		self.send(packets.client.cmd_listgames(version, mapname, maxplayers))
		packet = self.recv_packet([packets.server.data_gameslist])
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.data_gameslist):
			raise network.CommandError("Unexpected packet")
		return packet[1].games

	#-----------------------------------------------------------------------------

	def creategame(self, mapname, maxplayers, gamename, maphash="", password=""):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[CREATE] mapname=%s maxplayers=%d" % (mapname, maxplayers))
		self.send(packets.client.cmd_creategame(
			clientver   = self.version,
			clientid    = self.clientid,
			playername  = self.name,
			playercolor = self.color,
			gamename    = gamename,
			mapname     = mapname,
			maxplayers  = maxplayers,
			maphash     = maphash,
			password    = password))
		packet = self.recv_packet([packets.server.data_gamestate])
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.data_gamestate):
			raise network.CommandError("Unexpected packet")
		self.game = packet[1].game
		return self.game

	#-----------------------------------------------------------------------------

	def joingame(self, uuid, password="", fetch=False):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[JOIN] %s" % (uuid))
		self.send(packets.client.cmd_joingame(
			uuid        = uuid,
			clientver   = self.version,
			clientid    = self.clientid,
			playername  = self.name,
			playercolor = self.color,
			password    = password,
			fetch       = fetch))
		packet = self.recv_packet([packets.server.data_gamestate])
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.data_gamestate):
			raise network.CommandError("Unexpected packet")
		self.game = packet[1].game
		return self.game

	#-----------------------------------------------------------------------------

	def leavegame(self, stealth=False):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		if self.game is None:
			raise network.NotInGameLobby("We are not in a game lobby")
		self.log.debug("[LEAVE]")
		if stealth:
			self.game = None
			return
		self.send(packets.client.cmd_leavegame())
		packet = self.recv_packet([packets.cmd_ok])
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.cmd_ok):
			raise network.CommandError("Unexpected packet")
		self.game = None
		return True

	#-----------------------------------------------------------------------------

	def chat(self, message):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		if self.game is None:
			raise network.NotInGameLobby("We are not in a game lobby")
		self.log.debug("[CHAT] %s" % (message))
		self.send(packets.client.cmd_chatmsg(message))
		return True

	#-----------------------------------------------------------------------------

	def changename(self, name):
		""" NOTE: this returns False if the name must be validated by
		the server. In that case this will trigger a lobbygame_changename-
		event with parameter myself=True. if this functions returns true
		your name has been changed but there was no need to sent it to
		the server."""
		if self.name == name:
			return True
		self.log.debug("[CHANGENAME] %s" % (name))
		if self.mode is None or self.game is None:
			self.name = name
			return True
		self.send(packets.client.cmd_changename(name))
		return False

	#-----------------------------------------------------------------------------

	def onchangename(self, game, plold, plnew, myself):
		self.log.debug("[ONCHANGENAME] %s -> %s" % (plold.name, plnew.name))
		if myself:
			self.name = plnew.name
		return True

	#-----------------------------------------------------------------------------

	def changecolor(self, color):
		""" NOTE: this returns False if the name must be validated by
		 the server. In that case this will trigger a lobbygame_changecolor-
		 event with parameter myself=True. if this functions returns true
		 your name has been changed but there was no need to sent it to
		 the server."""
		if self.color == color:
			return True
		self.log.debug("[CHANGECOLOR] %s" % (color))
		if self.mode is None or self.game is None:
			self.color = color
			return True
		self.send(packets.client.cmd_changecolor(color))
		return False

	#-----------------------------------------------------------------------------

	def onchangecolor(self, game, plold, plnew, myself):
		self.log.debug("[ONCHANGECOLOR] %s: %s -> %s" % (plnew.name, plold.color, plnew.color))
		if myself:
			self.color = plnew.color
		return True

	#-----------------------------------------------------------------------------

	def ongameprepare(self):
		self.log.debug("[GAMEPREPARE]")
		self.game.state = Game.State.Prepare
		self.call_callbacks("lobbygame_starts", self.game)
		self.send(packets.client.cmd_preparedgame())
		return True

	#-----------------------------------------------------------------------------

	def ongamestart(self):
		self.log.debug("[GAMESTART]")
		self.game.state = Game.State.Running
		self.mode = ClientMode.Game
		self.call_callbacks("game_starts", self.game)
		return True

	#-----------------------------------------------------------------------------

	def toggleready(self):
		self.log.debug("[TOGGLEREADY]")
		self.send(packets.client.cmd_toggleready())
		return True

	#-----------------------------------------------------------------------------

	def kick(self, player_sid):
		self.log.debug("[KICK]")
		self.send(packets.client.cmd_kickplayer(player_sid))
		return True

	#-----------------------------------------------------------------------------

	#TODO
	def send_fetch_game(self, clientversion, uuid):
		self.send(packets.client.cmd_fetch_game(clientversion, uuid))
		return True
