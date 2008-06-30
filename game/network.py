# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import time
import socket
import select
import pickle
import struct
import sys
from game.packets import *


# TODO: make networking robust
#       (i.e. GUI freezes sometimes when waiting for timeout)

if sys.argv[0].lower().endswith('openanno.py'):
	import game.main

class Socket(object):
	"""A socket which handles network communication, it sends and receives packets (packets=Objects of (sub)type Packet)
	@param port: the port to listen on or 0 for auto choosing a port
	"""
	def __init__(self, port = 0):
		if sys.argv[0].lower().endswith('openanno.py'):
			game.main.fife.pump.append(self._pump)
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._socket.bind(('', port))
		self.port = self._socket.getsockname()[1]
		self.buffers = {}

	def __del__(self):
		self._socket.close()

	def end(self):
		if sys.argv[0].lower().endswith('openanno.py'):
			game.main.fife.pump.remove(self._pump)

	def _pump(self, forever = False):
		"""internal function which gets regularly called and checks for incoming packets
		@param forever: used internally in masterserver, to not waste ressources
		"""
		#a packet is: OA<len><data>
		while 1:
			read, write, error = select.select([self._socket], [], [], *([] if forever else [0]))
			if len(read) == 0:
				break
			try:
				data, address = self._socket.recvfrom(1024)
			except socket.error:
				continue
			if len(data) == 0:
				continue
			self.buffers[address] = (self.buffers[address]  + data) if address in self.buffers else data
			while 1:
				if self.buffers[address][0:2] != 'OA':
					del self.buffers[address]
					break
				if len(self.buffers[address]) < 6:
					break
				length = struct.unpack('I', self.buffers[address][2:6])[0]
				if length + 6 > len(self.buffers[address]):
					break
				data = self.buffers[address][6:6 + length]
				self.buffers[address] = self.buffers[address][6 + length:]
				try:
					packet = pickle.loads(data)
				except pickle.PickleError:
					continue
				packet.address, packet.port = address
				self.receive(packet)
				if len(self.buffers[address]) == 0:
					del self.buffers[address]
					break

	def send(self, packet):
		"""Send a packet
		@param packet: the packet to send (packet = object of (sub)type Packet) (see packet.py
		"""
		data = pickle.dumps(packet)
		#print 'SEND', packet, 'TO', packet.address, packet.port
		self._socket.sendto('OA' + struct.pack('I',len(data)) + data, (packet.address, packet.port))

	def receive(self, packet):
		"""Hook this function to receive packets
		@param packet: the incoming packet
		"""
		pass

class MPPlayer(object):
	"""
	@param name:
	"""
	def __init__(self, address = None, port = None):
		self.address, self.port = address, port 
		self.name, self.color, self.team = "unknown player", -1, None
		self.ready = False


class Connection(object):
	""" Base Class for network connection
	"""
	def __init__(self, port = 0):
		self._socket = Socket(port)
		self._socket.receive = self.onPacket

		self.local_player = None
		self.mpoptions = {}
		self.mpoptions['players'] = []
		self.mpoptions['slots'] = None
		self.mpoptions['bots'] = None
		self.mpoptions['maps'] = {}
		self.mpoptions['selected_map'] = -1

	def onPacket(self, packet):
		"""Called on packet receive
		"""
		pass

	def send(self, packet):
		# if no address, send to all players 
		if packet.address == None and packet.port == None:
			for player in self.mpoptions['players']:
				packet.address, packet.port = player.address, player.port
				if packet.address == None and packet.port == None:
					self.onPacket(packet)
				else:
					self._socket.send(packet)
		else:
			self._socket.send(packet)


class ClientConnection(Connection):
	""" Connection for a client

	Use an instance of this class for 
	game.main.connectin on a client machine
	"""
	connectTimeout = 5

	STATE_DISCONNECTED, STATE_CONNECTING, STATE_CONNECTED = range(0,3)

	def __init__(self):
		super(ClientConnection, self).__init__()

		self.local_player = MPPlayer()

		self.state = self.__class__.STATE_DISCONNECTED

	def join(self, address, port):
		self.address, self.port = address, port
		self.sendToServer(LobbyJoinPacket(self.address, self.port, self.local_player))

	def _pump(self):
		if self.connectTime + self.__class__.connectTimeout <= time.time():
			self.onTimeout()

	def onPacket(self, packet):
		#print 'RECV', packet,'FROM',packet.address,packet.port
		packet.handleOnClient()

	def reconnect(self):
		if self.state not in (self.__class__.STATE_CONNECTING, self.__class__.STATE_DISCONNECTED):
			self.doDisconnect()
		if self._pump not in game.main.fife.pump:
			game.main.fife.pump.append(self._pump)
		self.send(ConnectPacket(self.address, self.port))
		self.connectTime = time.time()
		self.state = self.__class__.STATE_CONNECTING

	def sendToServer(self, packet):
		packet.address, packet.port = self.address, self.port
		self.send(packet)

	def end(self):
		self._socket.receive = lambda a: None
		if self._pump in game.main.fife.pump:
			game.main.fife.pump.remove(self._pump)

	def doChat(self, text):
		"""
		@param text:
		"""
		self.send(ChatPacket(text))

	def doDisconnect(self):
		self.send(DisconnectPacket(self.address, self.port))

	def doPlayerModify(self, **settings):
		"""
		@param **settings:
		"""
		for name, value in settings.items():
			self.send(PlayerModify(name, value))

	def onTimeout(self):
		pass

	def onConnected(self):
		"""Called when connection to server is confirmed
		"""
		pass

	def onDisconnect(self):
		pass

	def onChat(self, player, text):
		"""
		@param player:
		@param text:
		"""
		pass

	def onPlayerPart(self, player):
		"""
		@param player:
		"""
		pass

	def onPlayerModify(self, player):
		"""
		@param player:
		"""
		pass

	def onServerSetting(self, settings):
		"""
		@param settings:
		"""
		pass

	def onTickPacket(self, tick, commands):
		"""
		@param tick:
		@param commands:
		"""
		pass

class ServerConnection(Connection):
	""" Connection on a server

	Use an instance of this class for 
	game.main.connectin on a game server
	"""

	clientUpdateInterval = 2
	registerTimeout = 120

	def __init__(self, port = None):
		super(ServerConnection, self).__init__(game.main.settings.network.port)
		self.registerTime = 0
		if self._pump not in game.main.fife.pump:
			game.main.fife.pump.append(self._pump)

		self.local_player = MPPlayer("127.0.0.1", port)

		self.register()

		self.clientLastUpdate = 0

		game.main.fife.pump.append(self.notifyClients)

	def end(self):
		game.main.fife.pump.remove(self.notifyClients)
		self._socket.receive = lambda a: None

	def notifyClients(self, force = False):
		if not force and self.clientLastUpdate + self.__class__.clientUpdateInterval > time.time():
			return
		self.clientLastUpdate = time.time()
		self.send(LobbyServerInfoPacket(self.mpoptions))

	def _pump(self):
		if self.registerTime + self.__class__.registerTimeout <= time.time():
			self.register()

	def register(self):
		""" Registers game server on master game server
		"""
		self._socket.send(MasterRegisterPacket(self._socket.port))
		self.registerTime = time.time()

	def onPacket(self, packet):
		#print 'RECV', packet,'FROM',packet.address,packet.port
		packet.handleOnServer()

