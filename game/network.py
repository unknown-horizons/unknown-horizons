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
import game.main

class Packet(object):
	def __init__(self, address, port):
		self.address, self.port = str(address), int(port)

class TickPacket(Packet):
	def __init__(self, address, port, tick, commands):
		super(TickPacket, self).__init__(address, port)
		self.tick = tick
		self.commands = commands

class QueryPacket(Packet):
	pass

class ConnectPacket(Packet):
	pass

class RegisterPacket(Packet):
	pass

class InfoPacket(Packet):
	def __init__(self, address, port, map, players, bots, maxplayers):
		super(TickPacket, self).__init__(address, port)
		self.map, self.players, self.bots, self.maxplayers = map, players, bots, maxplayers

class Socket(object):
	def __init__(self, port = 0):
		game.main.fife.pump.append(self._pump)
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._socket.bind(('', port))
		self.port = self._socket.getsockname()[1]

	def __del__(self):
		self._socket.close()

	def end(self):
		game.main.fife.pump.remove(self._pump)

	def _pump(self):
		while 1:
			read, write, error = select.select([self._socket], [], [], 0)
			if len(read) == 0:
				break
			try:
				data, address = self._socket.recvfrom(1024)
			except socket.error:
				continue
			print '[incoming] bytes:', len(data), 'address:', address
			if len(data) > 0:
				packet = pickle.loads(data)
				packet.address, packet.port = address
				self.receive(packet)

	def send(self, packet):
		self._socket.sendto(pickle.dumps(packet), (packet.address, packet.port))

	def receive(self, packet):
		pass

class NetworkClient(object):
	connectTimeout = 5

	def __init__(self, address, port):
		self._socket = Socket()
		self._socket.receive = self.onPacket
		game.main.fife.pump.append(self._pump)

		self.address, self.port = address, port
		self.reconnect()

	def reconnect(self):
		self._socket.send(ConnectPacket(self.address, self.port))
		self.connectTime = time.time()

	def end(self):
		self.socket.receive = lambda : None
		if self._pump in game.main.fife.pump:
			game.main.fife.pump.remove(self._pump)

	def _pump(self):
		if self.connectTime + self.__class__.connectTimeout <= time.time():
			self.onTimeout()

	def send(self, packet):
		self._socket.send(packet)

	def onTimeout(self):
		pass

	def onPacket(self, packet):
		pass

class NetworkServer(NetworkClient):
	def __init__(self, port = None):
		self._socket = Socket(port or game.main.settings.network.port)
		self._socket.receive = self.onPacket

		self.register()

	def register(self):
		self._socket.send(RegisterPacket(self._socket.port))

	def end(self):
		self._socket.receive = lambda : None

class ServerLobby(object):
	pass
