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

import urllib
import re
import game.main
import time

class Packet(object):
	def __init__(self, address, port):
		self.address, self.port = None, None

class TickPacket(Packet):
	def __init__(self, address, port, tick, commands):
		super(TickPacket, self).__init__(address, port)
		self.tick = tick
		self.commands = commands

class QueryPacket(Packet):
	pass

class Socket(object):
	def __init__(self, port = None):
		game.main.fife.pump.append(self._pump)
		#todo: add socket

	def __del__(self):
		#todo: remove socket
		pass

	def end(self):
		game.main.fife.pump.remove(self._pump)

	def _pump(self):
		#todo: check socket; call receive
		pass

	def send(self, packet):
		#todo: send packet
		pass

	def receive(self, packet):
		pass

class Server(object):
	re_ip_port = re.compile("^((?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5])))(?::((?:[0-5]?[0-9]{1,4}|6(?:[0-4][0-9]{3}|5(?:[0-4][0-9]{2}|5(?:[0-2][0-9]|3[0-5]))))))?$")
	def __init__(self, address, port):
		self.address = address
		self.port = port
		self.ping, self.map, self.players, self.bots, self.maxplayers = None, None, None, None, None

	def __eq__(self, other):
		return self.address == other.address and self.port == other.port

	def __str__(self):
		info = []
		if self.ping != None:
			info.append('ping: ' + str(self.ping))
		if self.map != None:
			info.append('map: ' + str(self.map))
		if self.players != None or self.maxplayers != None or self.bots != None:
			info.append('players: ' + str(self.players) + '+' + str(self.bots) + '/' + str(self.maxplayers))
		return str(self.address) + ':' + str(self.port) + ('' if len(info) == 0 else ' (' + ', '.join(info) + ')')

class ServerList(object):
	def __init__(self):
		self._servers = []
		self.socket = Socket()
		self.socket.receive = self._response

	def __del__(self):
		self.socket.end()

	def _clear(self):
		self._servers = []

	def _add(self, server):
		if server in self:
			self._servers.remove(server)
		self._servers.append(server)

	def _remove(self, server):
		self._servers.remove(server)

	def _query(self, address, port):
		tmp_server = Server(address, port)
		for server in self:
			if server == tmp_server:
				server.timeLastQuery = time.time()
		self._request(address, port)

	def _request(self, address, port):
		self.socket.send(QueryPacket(address, port))

	def _response(self, packet):
		for server in self:
			if server.address == packet.address and server.port == packet.port:
				server.timeLastResponse = time.time()
				server.ping = int(((server.timeLastResponse - server.timeLastQuery) * 1000) + 0.5)
				self.changed()

	def changed(self):
		pass

	def __getitem__(self, *args, **kwargs): return self._servers.__getitem__(*args, **kwargs)
	def __getslice__(self, *args, **kwargs): return self._servers.__getslice__(*args, **kwargs)
	def __iter__(self, *args, **kwargs): return self._servers.__iter__(*args, **kwargs)
	def __len__(self, *args, **kwargs): return self._servers.__len__(*args, **kwargs)
	def __contains__(self, *args, **kwargs): return self._servers.__contains__(*args, **kwargs)

class WANServerList(ServerList):
	def __init__(self):
		super(WANServerList, self).__init__()
		self.update()

	def update(self):
		self._clear()
		for server in urllib.urlopen(game.main.settings.network.url_servers):
			match = Server.re_ip_port.match(server)
			if match:
				server = Server(match.group(1), match.group(2) or game.main.settings.network.port)
				if not server in self:
					self._add(server)
					self._query(server.address, server.port)

class LANServerList(ServerList):
	def __init__(self):
		super(LANServerList, self).__init__()
		self.update()

	def update(self):
		for server in self:
			server.timeLastQuery = time.time()
		self._request('255.255.255.255', game.main.settings.network.port)

	def _response(self, packet):
		for server in self:
			if server.address == packet.address and server.port == packet.port:
				break
		else:
			self._add(Server(packet.address, packet.port))
			self._query(packet.address, packet.port)
		super(LANServerList, self)._response(packet)

class FavoriteServerList(ServerList):
	def __init__(self):
		super(FavoriteServerList, self).__init__()
		#load from settings

	def update(self):
		for server in self:
			self._query(server.address, server.port)

	def add(self, address, port):
		self._add(Server(address, port))
		self._query(server.address, server.port)
		#save to setings

	def remove(self, address, port):
		self._remove(Server(address, port))
		#save to setings

	def clear(self):
		self._clear()
		#save to setings
