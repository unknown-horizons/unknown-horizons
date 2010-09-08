# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from horizons.network import util, packets, find_enet_module
enet = find_enet_module()

__all__ = [
  'Address',
  'Player',
  'Game',
  'UUID'
]

class Address():
	def __init__(self, address, port = None):
		if isinstance(address, enet.Address):
			self.host = address.host
			self.port = address.port
		else:
			self.host = address
			self.port = int(port)

	def __str__(self):
		return "%s:%u" % (self.host, self.port)

	def __hash__(self):
		return hash((self.host, self.port))

	def __eq__(self, other):
		if isinstance(other, Address):
			return (self.host == other.host and self.port == other.port)
		if isinstance(other, enet.Address):
			return self.__eq__(Address(other))
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, Address) or isinstance(other, enet.Address):
			return not self.__eq__(other)
		return NotImplemented

#-----------------------------------------------------------------------------

class Player():
	def __init__(self, name, peer = None):
		self.ready = False
		self.name  = name
		self.peer  = peer
		# we can't pickle self.peer (it's c code)
		# so we need to copy the unique address
		self.address = None
		if isinstance(self.peer, enet.Peer):
			self.address = Address(self.peer.address)

	def __hash__(self):
		return hash((self.address, self.name))

	def __eq__(self, other):
		if not isinstance(other, Player):
			return NotImplemented
		return (self.address == other.address and self.name == other.name)

	def __ne__(self, other):
		if not isinstance(other, Player):
			return NotImplemented
		return not self.__eq__(other)

	# omit self.peer during pickling
	def __getstate__(self):
		return { 'name': self.name, 'address': self.address, 'peer': None, 'ready': False }

#-----------------------------------------------------------------------------

class Game():
	def __init__(self, packet, creator_peer):
		assert(isinstance(packet, packets.client.cmd_creategame))
		self.uuid          = UUID()
		self.clientversion = packet.clientversion
		self.mapname       = packet.mapname
		self.maxplayers    = packet.maxplayers
		self.creator       = packet.playername
		self.players       = []
		self.playercnt     = 1
		self.gamestarts    = False
		self.addplayer(Player(packet.playername, creator_peer))

	def addplayer(self, player):
		self.players.append(player)

#-----------------------------------------------------------------------------

class UUID():
	def __init__(self, uuid = None):
		if uuid is None:
			self.uuid = util.randomUUID()
		elif isinstance(uuid, UUID):
			self.uuid = uuid.uuid
		else:
			self.uuid = util.uuidFromString(uuid)

	def __str__(self):
		return util.uuidToString(self.uuid)

	def __eq__(self, other):
		if isinstance(other, UUID):
			return (self.uuid == other.uuid)
		return NotImplemented

	def __ne__(self, other):
		return not self.__eq__(other)

