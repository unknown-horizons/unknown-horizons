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
from game.network import Socket
from game.packets import QueryPacket, InfoPacket
import time

class Server(object):
	re_ip_port = re.compile("^((?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5])))(?::((?:[0-5]?[0-9]{1,4}|6(?:[0-4][0-9]{3}|5(?:[0-4][0-9]{2}|5(?:[0-2][0-9]|3[0-5]))))))?$")

	"""This represents a server in the serverlist
	@param address: the address
	@param port: and the port :)
	"""
	def __init__(self, address, port = None):
		if port is None:
			match = Server.re_ip_port.match(address)
			if match:
				address = match.group(1)
				port = match.group(2) or game.main.settings.network.port
			else:
				port = game.main.settings.network.port
		self.address = address
		self.port = int(port)
		self.ping, self.map, self.players, self.bots, self.maxplayers, self.timeLastQuery, self.timeLastResponse = None, None, None, None, None, None, None

	def __eq__(self, other):
		"""check if the server is the same (only address & port have to match)
		@param other: the other one
		"""
		return self.address == other.address and self.port == other.port

	def __str__(self):
		"""A nice representation we can show in the list
		"""
		info = ['timeout' if self.ping is None else 'ping: ' + str(self.ping) + 'ms']
		if self.map is not None:
			info.append('map: ' + str(self.map))
		if self.players is not None or self.maxplayers is not None or self.bots is not None:
			info.append('players: ' + str(self.players) + '+' + str(self.bots) + '/' + str(self.maxplayers))
		return str(self.address) + ':' + str(self.port) + ' (' + ', '.join(info) + ')'

class ServerList(object):
	queryIntervall = 1
	queryTimeout = 2

	"""A basic Serverlist, should be extended to implement more functionality
	"""
	def __init__(self):
		self._servers = []
		self._socket = Socket()
		self._socket.receive = self._response
		game.main.ext_scheduler.add_new_object(self._pump, self, self.queryIntervall, -1)

	def end(self):
		"""
		"""
		game.main.ext_scheduler.rem_all_classinst_calls(self)
		self._socket.receive = lambda x : None
		self._socket.end()

	def _pump(self):
		"""internal function, regularly called to ping the contained servers etc
		"""
		for server in self:
			if server.ping is not None and int(server.timeLastResponse or 0) + self.__class__.queryTimeout <= server.timeLastQuery:
				server.ping = None
				self.changed()
			self._query(server.address, server.port)
			return

	def _clear(self):
		"""remove all servers from the list
		"""
		self._servers = []
		self.changed()

	def _add(self, server):
		"""add a server to the list
		@param server: the server to add
		"""
		if server in self:
			self._servers.remove(server)
		self._servers.append(server)
		self.changed()

	def _remove(self, server):
		"""remove a server from the list
		@param server: the server to remove
		"""
		self._servers.remove(server)

	def _query(self, address, port):
		"""query(ask for an InfoPacket) a address port combination and update the corresponding server
		@param address: the address to query
		@param port: and the port
		"""
		tmp_server = Server(address, port)
		for server in self:
			if server == tmp_server:
				server.timeLastQuery = time.time()
		self._request(address, port)

	def _request(self, address, port):
		"""query(ask for an InfoPacket) a address port combination
		@param address: the address to query
		@param port: and the port
		"""
		self._socket.send(QueryPacket(address, port))

	def _response(self, packet):
		"""internal function, called when a server responded
		@param packet: the received packet
		"""
		if not isinstance(packet, InfoPacket):
			return
		for server in self:
			if server.address == packet.address and server.port == packet.port:
				server.timeLastResponse = time.time()
				server.ping = int(round(((server.timeLastResponse - server.timeLastQuery) * 1000)))
				server.map, server.players, server.bots, server.maxplayers = packet.map, packet.players, packet.bots, packet.maxplayers
				self.changed()

	def changed(self):
		"""callback, called when the list changed
		"""
		pass

	def __getitem__(self, *args, **kwargs): return self._servers.__getitem__(*args, **kwargs)
	def __getslice__(self, *args, **kwargs): return self._servers.__getslice__(*args, **kwargs)
	def __iter__(self, *args, **kwargs): return self._servers.__iter__(*args, **kwargs)
	def __len__(self, *args, **kwargs): return self._servers.__len__(*args, **kwargs)
	def __contains__(self, *args, **kwargs): return self._servers.__contains__(*args, **kwargs)

class WANServerList(ServerList):
	updateIntervall = 60

	"""a specialized serverlist, gets its content from an url
	"""
	def __init__(self):
		super(WANServerList, self).__init__()
		self.update()
		if self.__class__.updateIntervall > 0:
			game.main.ext_scheduler.add_new_object(self.update, self, self.updateIntervall, -1)

	def end(self):
		"""
		"""
		game.main.ext_scheduler.rem_all_classinst_calls(self)
		super(WANServerList, self).end()

	def update(self):
		"""manually update the serverlist from the url
		"""
		self._clear()

		wan_servers = []
		try:
			wan_servers = (urllib.urlopen(game.main.settings.network.url_servers))
		except IOError,e:
			game.main.showPopup("Network Error", "Error: "+e.strerror[1])

		for server in wan_servers:
			match = Server.re_ip_port.match(server)
			if match:
				server = Server(match.group(1), match.group(2) or game.main.settings.network.port)
				if not server in self:
					self._add(server)
					self._query(server.address, server.port)

class LANServerList(ServerList):
	updateIntervall = 3

	"""a serverlist which regularly searches the lan for servers (sends a broadcast)
	"""
	def __init__(self):
		super(LANServerList, self).__init__()
		self.update()
		if self.__class__.updateIntervall > 0:
			game.main.ext_scheduler.add_new_object(self.update, self, self.updateIntervall, -1)

	def end(self):
		"""
		"""
		game.main.ext_scheduler.rem_all_classinst_calls(self)
		super(LANServerList, self).end()

	def update(self):
		"""manually update the list, search for servers (send the broadcast)
		"""
		for server in self:
			server.timeLastQuery = time.time()
		self._request('255.255.255.255', game.main.settings.network.port)
		#self._request('192.168.2.255', game.main.settings.network.port)

	def _response(self, packet):
		"""overwritten function of the base class, ensures that the server is in the list when a packet is received
		@param packet: the packet
		"""
		if not isinstance(packet, InfoPacket):
			return
		for server in self:
			if server.address == packet.address and server.port == packet.port:
				break
		else:
			self._add(Server(packet.address, packet.port))
			self._query(packet.address, packet.port)
		super(LANServerList, self)._response(packet)

class FavoriteServerList(ServerList):
	"""a specialzed serverlist, which holds a static set of servers and just regularly updates them
	"""
	def __init__(self):
		super(FavoriteServerList, self).__init__()
		for serverstr in game.main.settings.network.favorites:
			server = Server(serverstr)
			self._add(server)
			self._query(server.address, server.port)

	def update(self):
		"""manually update
		"""
		for server in self:
			self._query(server.address, server.port)

	def add(self, serverstr):
		"""add a server
		@param serverstr: a string in "address[:port]" notion
		"""
		server = Server(serverstr)
		self._add(server)
		self._query(server.address, server.port)
		game.main.settings.network.favorites = game.main.settings.network.favorites + [serverstr]

	def remove(self, serverstr):
		"""remove a server
		@param serverstr: a string in "address[:port]" notion
		"""
		self._remove(Server(serverstr))
		favorites = game.main.settings.network.favorites
		favorites.remove(serverstr)
		game.main.settings.network.favorites = favorites

	def clear(self):
		"""make the list empty
		"""
		self._clear()
		game.main.settings.network.favorites = []
