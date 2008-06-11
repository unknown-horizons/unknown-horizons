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

class Server(object):
	re_ip_port = re.compile("^((?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5]))[.](?:[0-1]?[0-9]{1,2}|2(?:[0-4][0-9]|5[0-5])))(?::((?:[0-5]?[0-9]{1,4}|6(?:[0-4][0-9]{3}|5(?:[0-4][0-9]{2}|5(?:[0-2][0-9]|3[0-5]))))))?$")
	def __init__(self, address, port):
		self.address = address
		self.port = port
		self.ping, self.map, self.players, self.bots, self.maxplayers = None, None, None, None, None

	def __eq__(self, other):
		return self.address == other.address and self.port == other.port

	def __str__(self):
		return str(self.address) + ':' + str(self.port) + '(ping: ' + str(self.ping) + ', map: ' + str(self.map) + ', players: ' + str(self.players) + '+' + str(self.bots) + '/' + str(self.maxplayers) + ')'

class ServerList(object):
	def __init__(self):
		self._servers = []
		#todo: setup socket

	def _clear(self):
		self._servers = []

	def _present(self, server):
		return server in self._servers

	def _add(self, server):
		if self._present(server):
			self._servers.remove(server)
		self._servers.append(server)
		self._query(server.address, server.port)

	def _remove(self, server):
		self._servers.remove(server)

	def _query(self, address, port):
		print 'query:',address,port
		#todo: query server

	def _response(self, server):
		if self._present(server):
			#todo: update server
			pass

	def __getitem__(self, *args, **kwargs): return self._servers.__getitem__(*args, **kwargs)
	def __getslice__(self, *args, **kwargs): return self._servers.__getslice__(*args, **kwargs)
	def __iter__(self, *args, **kwargs): return self._servers.__iter__(*args, **kwargs)
	def __len__(self, *args, **kwargs): return self._servers.__len__(*args, **kwargs)

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
				if not self._present(server):
					self._add(server)

class LANServerList(ServerList):
	def __init__(self):
		super(LANServerList, self).__init__()
		self.update()

	def update(self):
		self._query('255.255.255.255', game.main.settings.network.port)

	def _response(self, server):
		if not self._present(server):
			self._add(server)
		super(LANServerList, self)._response(server)

class FavoriteServerList(ServerList):
	def __init__(self):
		super(FavoriteServerList, self).__init__()
		#load from settings

	def update(self):
		for server in self:
			self._query(server.address, server.port)

	def add(self, address, port):
		self._add(Server(address, port))
		#save to setings

	def remove(self, address, port):
		self._remove(Server(address, port))
		#save to setings

	def clear(self):
		self._clear()
		#save to setings
