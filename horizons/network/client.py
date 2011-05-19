# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
import time


from horizons.network import packets
from horizons import network
from horizons.network.common import *
from horizons.constants import MULTIPLAYER
from horizons.network import find_enet_module
import socket # needed for socket.fromfd

enet = find_enet_module()
# during pyenets move to cpython they renamed a few constants...
if not hasattr(enet, 'PEER_STATE_DISCONNECTED') and hasattr(enet, 'PEER_STATE_DISCONNECT'):
	enet.PEER_STATE_DISCONNECTED = enet.PEER_STATE_DISCONNECT

# maximal peers enet should handle
# this must be at least maxplayers (supported by the game) + 1
MAX_PEERS = MULTIPLAYER.MAX_PLAYER_COUNT + 1
SERVER_TIMEOUT = 5000
CLIENT_TIMEOUT = SERVER_TIMEOUT * 3
UPNP_TIMEOUT = 200
NATPMP_TIMEOUT = 200
NATPMP_LIFETIME = 8 * 60 * 60 # max 24 hours

class ClientMode:
	Server = 0
	Peer2Peer = 1

class Client(object):
	log = logging.getLogger("network")

	def __init__(self, name, version, server_address, client_address = None):
		try:
			clientaddress = enet.Address(client_address[0], client_address[1]) if client_address is not None else None
			self.host = enet.Host(clientaddress, MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError):
			raise network.NetworkException("Unable to create network structure. Maybe invalid or irresolvable client address.")
		self.name          = name
		self.version       = version
		self.serveraddress = Address(server_address[0], server_address[1])
		self.serverpeer    = None
		self.mode          = ClientMode.Server
		self.game          = None
		self.packetqueue   = []
		self.callbacks     = {
			'lobbygame_chat':   [],
			'lobbygame_join':   [],
			'lobbygame_leave':  [],
			'lobbygame_state':  [],
			'lobbygame_starts': [],
			'p2p_ready':        [],
			'p2p_data':         [],
		}

		self.localport = client_address[1] if client_address is not None else None
		self.extport   = None
		self.upnp      = None
		self.natpmp    = None
		self.upnp_init()
		self.natpmp_init()
		pass

	def register_callback(self, type, callback, prepend = False, unique = True):
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

	def upnp_init(self):
		try:
			import miniupnpc
			self.upnp = miniupnpc.UPnP()
			self.upnp.discoverdelay = UPNP_TIMEOUT
			self.log.debug("[UPNP] Module available")
			devices = self.upnp.discover()
			if devices > 0:
				self.log.debug("[UPNP] %s device(s) detected" % (devices))
			else:
				self.log.debug("[UPNP] No devices detected. Disabling")
				self.upnp = None
		except ImportError:
			self.log.debug("[UPNP] Module not available")
			pass

	def natpmp_init(self):
		try:
			import libnatpmp
			self.natpmp = True
			self.log.debug("[NATPMP] Module available")
		except ImportError:
			self.log.debug("[NATPMP] Module not available")
			pass

	#-----------------------------------------------------------------------------

	def connect(self):
		if self.serverpeer is not None:
			raise network.AlreadyConnected("We are already connected to a server")
		if self.mode is None:
			self.mode = ClientMode.Server
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("You can't connect to a server while client is not in server mode")
		self.log.debug("[CONNECT] to server %s" % (self.serveraddress))
		try:
			self.serverpeer = self.host.connect(enet.Address(self.serveraddress.host, self.serveraddress.port), 1, 0)
		except (IOError, MemoryError):
			raise network.NetworkException("Unable to connect to server. Maybe invalid or irresolvable server address.")
		self.mode = ClientMode.Server
		event = self.host.service(SERVER_TIMEOUT)
		if event.type != enet.EVENT_TYPE_CONNECT:
			self.reset()
			raise network.UnableToConnect("Unable to connect to server")
		self.log.debug("[CONNECT] done")

		if self.localport is None and hasattr(socket, 'fromfd'):
			s = socket.fromfd(self.host.socket.fileno(), socket.AF_INET, socket.SOCK_DGRAM)
			self.localport = s.getsockname()[1]
		if self.localport is not None:
			self.log.debug("[CONNECT] localport=%s" % (self.localport))
			if self.extport is None:
				self.extport = self.upnp_connect(self.localport)
			if self.extport is None:
				self.extport = self.natpmp_connect(self.localport)
		else:
			self.log.debug("[CONNECT] Unable to determine local port");

	def p2p_connect(self):
		if self.mode is not ClientMode.Peer2Peer:
			raise network.NotInServerMode("You can't create the p2p network while client is not in p2p mode")
		start = False
		for player in self.game.players:
			if self.name == player.name:
				start = True
				continue
			if not start:
				continue
			self.log.debug("[P2P CONNECT] to player %s (%s)" % (player.name, player.address))
			player.peer = self.host.connect(enet.Address(player.address.host, player.address.port), 1, 0)

		self.log.debug("[P2P CONNECT] Waiting")
		waiting = len(self.game.players) -1
		while waiting > 0:
			event = self.host.service(CLIENT_TIMEOUT)
			if event.type == enet.EVENT_TYPE_NONE:
				break
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				break
			elif event.type == enet.EVENT_TYPE_CONNECT:
				player = None
				for _player in self.game.players:
					if _player.address == event.peer.address:
						player = _player
				if player is None:
					event.peer.disconnect()
					self.flush()
					event.peer.reset()
					continue
				if player.peer is None:
					player.peer = event.peer
				if not player.ready:
					player.ready = True
					waiting -= 1
				self.log.debug("[P2P CONNECT] Got connection from %s (%s)" % (player.name, player.address))

		for player in self.game.players:
			if self.name == player.name:
				continue
			if not player.ready:
				self.reset()
				self.log.warning("Unable to connect to %s (%s)" % (player.name, player.address))
				raise network.UnableToConnect("Unable to connect to %s (%s)" % (player.name, player.address))
		self.log.debug("[P2P CONNECT] done")

	def upnp_connect(self, localport):
		if self.upnp is None:
			return None
		if localport == 0:
			self.log.debug("[UPNP] Unable to fetch local port (port can't be 0)")
			return None
		try:
			self.upnp.selectigd()

			# search for free port
			extport = localport
			mapping = self.upnp.getspecificportmapping(extport, 'UDP')
			while mapping != None and extport < 65536:
				extport = extport + 1
				mapping = self.upnp.getspecificportmapping(extport, 'UDP')

			b = self.upnp.addportmapping(extport, 'UDP', self.upnp.lanaddr, localport, 'Unknown-Horizons', '')
			if b:
				self.log.debug("[UPNP] Redirect udp://%s:%s => udp://%s:%s successfully" % (self.upnp.externalipaddress(), extport, self.upnp.lanaddr, localport))
				return extport
			else:
				self.log.debug("[UPNP] Redirect failed")
		except Exception, e:
			self.log.debug("[UPNP] Exception: %s" % (e))
			self.upnp = None
			pass
		return None

	def natpmp_connect(self, localport):
		if self.natpmp is None:
			return None
		if localport == 0:
			self.log.debug("[NATPMP] Unable to fetch local port (port can't be 0)")
			return None
		try:
			# always create a new instance for NATPMP
			import libnatpmp
			natpmp = libnatpmp.NATPMP()
			natpmp.discoverdelay = NATPMP_TIMEOUT
			# search for free port
			extport = natpmp.addportmapping(localport, 'UDP', localport, NATPMP_LIFETIME)
			if extport is not None:
				self.log.debug("[NATPMP] Redirect udp://%s:%s => udp://<local>:%s successfully" % (natpmp.externalipaddress(), extport, localport))
				return extport
			else:
				self.log.debug("[NATPMP] Redirect failed")
		except Exception, e:
			self.log.debug("[NATPMP] Exception: %s" % (e))
			self.natpmp = None
			pass
		return None


	#-----------------------------------------------------------------------------

	def disconnect(self, later = False):
		if self.extport is not None:
			self.upnp_disconnect(self.extport) or self.natpmp_disconnect(self.extport, self.localport)
			self.extport = None
		if self.mode is ClientMode.Server:
			return self.server_disconnect(later)
		elif self.mode is ClientMode.Peer2Peer:
			return self.p2p_disconnect(later)
		raise network.NotConnected()

	def server_disconnect(self, later = False):
		if self.serverpeer is None:
			return
		if self.serverpeer.state == enet.PEER_STATE_DISCONNECTED:
			self.serverpeer = None
			return
		try:
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
			self.log.debug("Error while disconnecting from server. Maybe server isn't answering any more")
			self.reset()
		self.reset()
		self.log.debug("[DISCONNECT] done")

	def p2p_disconnect(self, later = False):
		for player in self.game.players:
			if player.peer is None:
				continue
			if player.peer.state == enet.PEER_STATE_DISCONNECTED:
				player.peer = None
				continue
			try:
				if later:
					player.peer.disconnect_later()
				else:
					player.peer.disconnect()
				while True:
					event = self.host.service(SERVER_TIMEOUT)
					if event.type == enet.EVENT_TYPE_DISCONNECT:
						break
					elif event.type == enet.EVENT_TYPE_NONE:
						raise IOError("No packet from server")
			except IOError:
				self.log.debug("Error while disconnecting from player: %s" % (player.name))
				player.peer.reset()
			player.peer = None
		self.reset()
		self.log.debug("[P2P DISCONNECT] done")

	def upnp_disconnect(self, extport):
		if self.upnp is None:
			return False
		try:
			b = self.upnp.deleteportmapping(extport, 'UDP')
			if b:
				self.log.debug("[UPNP] Successfully deleted port mapping")
				return True
			else:
				self.log.debug("[UPNP] Failed to remove port mapping")
		except Exception, e:
			self.log.debug("[UPNP] Exception: %s" % (e))
			self.upnp = None
			pass
		return False


	def natpmp_disconnect(self, extport, localport):
		if self.natpmp is None:
			return False
		try:
			# always create a new instance for NATPMP
			import libnatpmp
			natpmp = libnatpmp.NATPMP()
			natpmp.discoverdelay = NATPMP_TIMEOUT
			natpmp.deleteportmapping(extport, 'UDP', localport)
			self.log.debug("[NATPMP] Successfully deleted port mapping")
			return True
		except Exception, e:
			self.log.debug("[NATPMP] Exception: %s" % (e))
			self.natpmp = None
			pass
		return False


	#-----------------------------------------------------------------------------

	def isconnected(self):
		if self.mode is ClientMode.Server:
			return self.server_isconnected()
		elif self.mode is ClientMode.Peer2Peer:
			return self.p2p_isconnected()

	def server_isconnected(self):
		if self.serverpeer is None:
			return False
		return True

	def p2p_isconnected(self):
		connected = True
		for player in self.game.players:
			if player.name == self.name:
				continue
			if player.peer is None:
				connected = False
		return connected

	#-----------------------------------------------------------------------------

	def reset(self):
		self.log.debug("[RESET]")
		if self.mode is ClientMode.Server:
			return self.server_reset()
		elif self.mode is ClientMode.Peer2Peer:
			return self.p2p_reset()

	def server_reset(self):
		if self.serverpeer is not None:
			self.serverpeer.reset()
			self.serverpeer = None
		self.game = None
		self.flush()

	def p2p_reset(self):
		for player in self.game.players:
			if player.peer is None:
				continue
			player.peer.reset()
			player.peer = None
		self.server_reset()
		self.mode = ClientMode.Server

	#-----------------------------------------------------------------------------

	def flush(self):
		self.host.flush()

	#-----------------------------------------------------------------------------

	# enet doesn't need to send pings. instead we need to call enet_host_service
	# on a regular basis. we call this ping and save received events
	def ping(self):
		if self.mode is ClientMode.Server:
			return self.server_ping()
		elif self.mode is ClientMode.Peer2Peer:
			return self.p2p_ping()

	def server_ping(self):
		if self.serverpeer is None:
			raise network.NotConnected()
		packet = self.recv(0)
		if packet is not None:
			if not self.process_async_packet(packet):
				self.packetqueue.append(packet)
			return True
		return False

	def p2p_ping(self):
		packet = self.recv(0)
		if packet is not None:
			if not self.process_async_packet(packet):
				self.packetqueue.append(packet)
			return True
		return False

	#-----------------------------------------------------------------------------

	def send(self, packet, channelid = 0):
		if self.mode is ClientMode.Server:
			self.server_send(packet, channelid)
		elif self.mode is ClientMode.Peer2Peer:
			self.p2p_send(packet, channelid)

	def server_send(self, packet, channelid = 0):
		if self.serverpeer is None:
			raise network.NotConnected()
		packet.send(self.serverpeer, channelid)

	def p2p_send(self, data, channelid = 0):
		self.log.debug("[P2P SEND]")
		packet = packets.p2p.data(data)
		for player in self.game.players:
			if self.name == player.name:
				continue
			if player.peer is None:
				continue
			packet.send(player.peer, channelid)

	#-----------------------------------------------------------------------------

	# wait for event from network
	def recv_event(self, timeout = SERVER_TIMEOUT):
		if self.mode is ClientMode.Server:
			return self.server_recv_event(timeout)
		elif self.mode is ClientMode.Peer2Peer:
			return self.p2p_recv_event(timeout)

	def server_recv_event(self, timeout = SERVER_TIMEOUT):
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
			# ignore connect events during holepunching
			if self.game is not None:
				for player in self.game.players:
					if player.address == event.peer.address:
						self.log.debug("[HOLEPUNCH CONNECTION] %s" % (event.peer.address))
						event.peer.disconnect()
						event.peer.reset()
						return None
			self.reset()
			self.log.warning("Unexpected connection from %s" % (event.peer.address))
			raise network.CommandError("Unexpected connection from %s" % (event.peer.address))
		return event

	def p2p_recv_event(self, timeout = SERVER_TIMEOUT):
		event = self.host.service(timeout)
		if event.type == enet.EVENT_TYPE_NONE:
			return None
		elif event.type == enet.EVENT_TYPE_DISCONNECT:
			# ignore disconnect from server
			if self.serverpeer is not None and Address(self.serverpeer.address) == event.peer.address:
				self.log.debug("[DISCONNECT] done")
				self.serverpeer = None
				return None
			self.reset()
			self.log.warning("Unexpected disconnect from %s" % (event.peer.address))
			raise network.CommandError("Unexpected disconnect from %s" % (event.peer.address))
		elif event.type == enet.EVENT_TYPE_CONNECT:
			event.peer.disconnect()
			event.peer.reset()
			self.log.warning("Unexpected connection from %s" % (event.peer.address))
			raise network.CommandError("Unexpected connection from %s" % (event.peer.address))
		return event

	# receives event from network and returns the unpacked packet
	def recv(self, timeout = SERVER_TIMEOUT):
		event = self.recv_event(timeout)
		if event is None:
			return None
		elif event.type == enet.EVENT_TYPE_RECEIVE:
			packet = packets.unserialize(event.packet.data)
			if packet is None:
				self.log.error("Unknown packet from %s!" % (event.peer.address))
				self.disconnect()
				return None
			#elif isinstance(packet, packets.cmd_error):
			#  raise network.CommandError(packet.errorstr)
			elif isinstance(packet, packets.cmd_fatalerror):
				self.log.error("[FATAL] Network message: %s" % (packet.errorstr))
				self.disconnect()
				raise network.FatalError(packet.errorstr)
			return [event.peer, packet]

	# return the first received packet of type [in packettypes]
	def recv_packet(self, packettypes = None, timeout = SERVER_TIMEOUT):
		if len(self.packetqueue) > 0:
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
			oldset = set(self.game.players)
			newset = set(packet[1].game.players)
			self.game = packet[1].game
			for x in oldset - newset:
				self.call_callbacks("lobbygame_leave", self.game, x.name)
			for x in newset - oldset:
				self.call_callbacks("lobbygame_join", self.game, x.name)
			return True
		elif isinstance(packet[1], packets.server.cmd_holepunching):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.onholepunching()
		elif isinstance(packet[1], packets.server.cmd_startgame):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.ongamestart()
		elif isinstance(packet[1], packets.p2p.data):
			self.log.debug("[P2P RECV] from %s" % (packet[0].address))
			self.call_callbacks("p2p_data", packet[0].address, packet[1].data)

		return False

	#-----------------------------------------------------------------------------

	def listgames(self, mapname = None, maxplayers = None, onlyThisVersion = False):
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not connected to any server")
		self.log.debug("[LIST]")
		self.send(packets.client.cmd_listgames(self.version if onlyThisVersion else -1, mapname, maxplayers))
		packet = self.recv_packet([packets.cmd_error, packets.server.data_gameslist])
		if packet is None:
			raise network.CommandError("No reply from server")
		elif isinstance(packet[1], packets.cmd_error):
			raise network.CommandError(packet[1].errorstr)
		elif not isinstance(packet[1], packets.server.data_gameslist):
			raise network.CommandError("Unexpected packet")
		return packet[1].games

	#-----------------------------------------------------------------------------

	def creategame(self, mapname, maxplayers):
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not connected to any server")
		self.log.debug("[CREATE] mapname=%s maxplayers=%d" % (mapname, maxplayers))
		self.send(packets.client.cmd_creategame(self.version, mapname, maxplayers, self.name))
		packet = self.recv_packet([packets.cmd_error, packets.server.data_gamestate])
		if packet is None:
			raise network.CommandError("No reply from server")
		elif isinstance(packet[1], packets.cmd_error):
			raise network.CommandError(packet[1].errorstr)
		elif not isinstance(packet[1], packets.server.data_gamestate):
			raise network.CommandError("Unexpected packet")
		self.game = packet[1].game
		return self.game

	#-----------------------------------------------------------------------------

	def joingame(self, uuid):
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not connected to any server")
		if not isinstance(uuid, UUID):
			uuid = UUID(uuid)
		self.log.debug("[JOIN] %s" % (uuid))
		self.send(packets.client.cmd_joingame(uuid, self.version, self.name))
		packet = self.recv_packet([packets.cmd_error, packets.server.data_gamestate])
		if packet is None:
			raise network.CommandError("No reply from server")
		elif isinstance(packet[1], packets.cmd_error):
			raise network.CommandError(packet[1].errorstr)
		elif not isinstance(packet[1], packets.server.data_gamestate):
			raise network.CommandError("Unexpected packet")
		self.game = packet[1].game
		return self.game

	#-----------------------------------------------------------------------------

	def leavegame(self):
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not connected to any server")
		if self.game is None:
			raise network.NotInGameLobby("We are not in a game lobby")
		self.log.debug("[LEAVE]")
		self.send(packets.client.cmd_leavegame())
		packet = self.recv_packet([packets.cmd_error, packets.cmd_ok])
		if packet is None:
			raise network.CommandError("No reply from server")
		elif isinstance(packet[1], packets.cmd_error):
			raise network.CommandError(packet[1].errorstr)
		elif not isinstance(packet[1], packets.cmd_ok):
			raise network.CommandError("Unexpected packet")
		self.game = None
		return True

	#-----------------------------------------------------------------------------

	def chat(self, message):
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not connected to any server")
		if self.game is None:
			raise network.NotInGameLobby("We are not in a game lobby")
		self.log.debug("[CHAT] %s" % (message))
		self.send(packets.client.cmd_chatmsg(message))
		return True

	#-----------------------------------------------------------------------------

	def onholepunching(self):
		for player in self.game.players:
			if self.name == player.name:
				continue
			self.log.debug("[HOLEPUNCHING] Player %s (%s)" % (player.name, player.address))
			temp = self.host.connect(enet.Address(player.address.host, player.address.port), 1)
			self.flush()
			temp.reset()
		self.send(packets.client.cmd_holepunchingok())

	#-----------------------------------------------------------------------------

	def ongamestart(self):
		self.game.gamestarts = True
		self.log.debug("[GAMESTART]")
		self.mode = ClientMode.Peer2Peer
		self.call_callbacks("lobbygame_starts", self.game)
		self.p2p_connect()
		# disconnect from server
		# dont use self.disconnect as we need to catch the event in p2p_recv_event
		self.serverpeer.disconnect()
		self.call_callbacks("p2p_ready")

