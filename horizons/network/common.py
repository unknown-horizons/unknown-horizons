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

import uuid
from horizons.network import packets, find_enet_module
enet = find_enet_module()

__all__ = [
  'Address',
  'Player',
  'Game',
]

class Address(object):
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

class Player(object):
	def __init__(self, peer, sid, protocol = 0):
		self.peer     = peer
		assert(isinstance(self.peer, enet.Peer))
		self.address  = Address(self.peer.address)
		self.sid      = sid
		self.protocol = protocol
		self.name     = None
		self.game     = None
		self.ready    = False

	def __hash__(self):
		return hash((self.address))

	def __eq__(self, other):
		if not isinstance(other, Player):
			return NotImplemented
		# server only cares about address
		if self.address is not None or other.address is not None:
			return (self.address == other.address)
		else:
			return (self.sid == other.sid)

	def __ne__(self, other):
		if not isinstance(other, Player):
			return NotImplemented
		return not self.__eq__(other)

	# for pickle: return only relevant data to the player
	def __getstate__(self):
		return { 'sid': self.sid, 'address': None, 'name': self.name }

	def __str__(self):
		if self.name:
			return "Player(addr=%s;proto=%d;name=%s)" % (self.address, self.protocol, self.name)
		else:
			return "Player(addr=%s;proto=%d)" % (self.address, self.protocol)

packets.SafeUnpickler.add('server', Player)

#-----------------------------------------------------------------------------

class Game(object):
	class State(object):
		Open = 0
		Prepare = 1
		Running = 2

		def __init__(self, state = Open):
			self.state = state

		def __str__(self):
			strvals = [ "Open", "Prepare", "Running" ]
			return "%s" % (strvals[self.state])

	def __init__(self, packet, creator):
		assert(isinstance(packet, packets.client.cmd_creategame))
		self.uuid          = uuid.uuid1().hex
		self.clientversion = packet.clientversion
		self.mapname       = packet.mapname
		self.maxplayers    = packet.maxplayers
		self.load          = packet.load
		self.creator       = creator.name
		self.creator_sid   = creator.sid
		self.players       = []
		self.playercnt     = 0
		self.state         = Game.State.Open
		self.add_player(creator)

	def add_player(self, player):
		player.game = self
		self.players.append(player)
		self.playercnt += 1
		return player

	def remove_player(self, player):
		if player not in self.players:
			return None
		self.players.remove(player)
		self.playercnt -= 1
		player.game = None
		return player

	def clear(self):
		for player in self.players:
			player.game = None
		del self.players[:]
		self.playercnt = 0

	def __str__(self):
		return "Game(uuid=%s;maxpl=%d;plcnt=%d;state=%s)" % (self.uuid, self.maxplayers, self.playercnt, Game.State(self.state))

packets.SafeUnpickler.add('server', Game)
