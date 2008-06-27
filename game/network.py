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

if sys.argv[0].lower().endswith('openanno.py'):
	import game.main

class Socket(object):
	"""
	@param port:
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
		"""
		"""
		self._socket.close()

	def end(self):
		"""
		"""
		if sys.argv[0].lower().endswith('openanno.py'):
			game.main.fife.pump.remove(self._pump)

	def _pump(self, forever = False):
		"""
		@param forever:
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
		"""
		@param packet:
		"""
		data = pickle.dumps(packet)
		self._socket.sendto('OA' + struct.pack('I',len(data)) + data, (packet.address, packet.port))

	def receive(self, packet):
		"""
		@param packet:
		"""
		pass

class MPPlayer(object):
	"""
	@param name:
	"""
	def __init__(self, name):
		self.name = name
		self.color, self.team = None, None

class ClientConnection(object):
	connectTimeout = 5

	"""
	@param address:
	@param port:
	"""
	def __init__(self, address, port):
		self.players = {}

		self._socket = Socket()
		self._socket.receive = self._receive

		self.address, self.port = address, port
		self.reconnect()

	def _pump(self):
		"""
		"""
		if self.connectTime + self.__class__.connectTimeout <= time.time():
			self.onTimeout()

	def _receive(self, packet):
		"""
		@param packet:
		"""
		if isinstance(packet, ConnectedPacket):
			self.onConnected(packet.players, packet.map, packet.settings)


	def reconnect(self):
		"""
		"""
		if self.state not in (self.__class__.STATE_CONNECTING, self.__class__.STATE_DISCONNECTED):
			self.doDisconnect()
		if self._pump not in game.main.fife.pump:
			game.main.fife.pump.append(self._pump)
		self.send(ConnectPacket(self.address, self.port))
		self.connectTime = time.time()
		self.state = self.__class__.STATE_CONNECTING

	def end(self):
		"""
		"""
		self.socket.receive = lambda : None
		if self._pump in game.main.fife.pump:
			game.main.fife.pump.remove(self._pump)

	def send(self, packet):
		"""
		@param packet:
		"""
		if packet.address == None and packet.port == None:
			for packet.address, packet.port in self.players:
				if packet.address == None and packet.port == None:
					self._receive(packet)
				else:
					game.main.connection.send(packet)
		else:
			game.main.connection.send(packet)


	def doChat(self, text):
		"""
		@param text:
		"""
		self.send(ChatPacket(text))

	def doDisconnect(self):
		"""
		"""
		self.send(DisconnectPacket(self.address, self.port))

	def doPlayerModify(self, **settings):
		"""
		@param **settings:
		"""
		for name, value in settings.items():
			self.send(PlayerModify(name, value))


	def onTimeout(self):
		"""
		"""
		pass

	def onConnected(self, players, map, settings):
		"""
		@param players:
		@param map:
		@param settings:
		"""
		pass

	def onDisconnect(self):
		"""
		"""
		pass

	def onChat(self, player, text):
		"""
		@param player:
		@param text:
		"""
		pass

	def onPlayerJoin(self, player):
		"""
		@param player:
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

	def onServerMap(self, map):
		"""
		@param map:
		"""
		pass

	def onTickPacket(self, tick, commands):
		"""
		@param tick:
		@param commands:
		"""
		pass

class ServerConnection(object):
	registerTimeout = 120

	"""
	@param port:
	"""
	def __init__(self, port = None):
		if self._pump not in game.main.fife.pump:
			game.main.fife.pump.append(self._pump)
		self._socket = Socket(port or game.main.settings.network.port)
		self._socket.receive = self.onPacket

		self.register()

	def _pump(self):
		"""
		"""
		if self.registerTime + self.__class__.registerTimeout <= time.time():
			self.register()

	def register(self):
		"""
		"""
		self._socket.send(MasterRegisterPacket(self._socket.port))
		self.registerTime = time.time()

	def end(self):
		"""
		"""
		self._socket.receive = lambda : None

	def send(self, packet):
		"""
		@param packet:
		"""
		if packet.address == None and packet.port == None:
			for packet.address, packet.port in self.players:
				game.main.connection.send(packet)
		else:
			game.main.connection.send(packet)
