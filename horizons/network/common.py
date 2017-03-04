# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
from gettext import NullTranslations

from horizons.network import enet, packets


class Address(object):
	def __init__(self, address, port=None):
		if isinstance(address, enet.Address):
			self.host = address.host
			self.port = address.port
		else:
			self.host = address
			self.port = int(port)

	def __str__(self):
		return "{}:{:d}".format(self.host, self.port)

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

nulltranslation = NullTranslations()
class Player(object):
	def __init__(self, peer, sid, protocol=0):
		# pickle doesn't use all of these attributes
		# for more detail check __getstate__()
		self.peer     = peer
		assert isinstance(self.peer, enet.Peer)
		self.address  = Address(self.peer.address)
		self.sid      = sid
		# there's a difference between player.protocol and player.version:
		# - player.protocol is the network protocol version used by the
		#   client while talking to the server
		# - player.version is the game version which all players in a game
		#   must match. player.version gets set during oncreate/onjoin
		self.protocol = protocol
		self.version  = None
		self.name     = None
		self.color    = None
		self.clientid = None
		self.game     = None
		self.ready    = False
		self.prepared = False
		self.fetch    = False
		self.gettext  = nulltranslation

	# for pickle: return only relevant data to the player
	def __getstate__(self):
		return {
				'sid':      self.sid,
				'address':  None,
				'name':     self.name,
				'color':    self.color,
				'ready':    self.ready,
				'clientid': self.clientid
			}

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

	def __str__(self):
		if self.name:
			return "Player(addr={};proto={:d};name={})".format(self.address, self.protocol, self.name)
		else:
			return "Player(addr={};proto={:d})".format(self.address, self.protocol)

	def join(self, game, packet):
		""" assigns player data sent by create/join-command to the player """
		assert (isinstance(packet, packets.client.cmd_creategame)
		        or isinstance(packet, packets.client.cmd_joingame))
		self.game     = game
		self.version  = packet.clientversion
		self.name     = packet.playername
		self.color    = packet.playercolor
		self.clientid = packet.clientid
		self.ready    = False
		if isinstance(packet, packets.client.cmd_joingame):
			self.fetch = packet.fetch

	def toggle_ready(self):
		self.ready = not self.ready
		return self.ready

packets.SafeUnpickler.add('server', Player)

#-----------------------------------------------------------------------------

class Game(object):
	class State(object):
		Open      = 0
		Prepare   = 1
		Running   = 2

		def __init__(self, state=Open):
			self.state = state

		def __str__(self):
			strvals = ["Open", "Prepare", "Running"]
			return strvals[self.state]

	def __init__(self, packet, creator):
		# pickle doesn't use all of these attributes
		# for more detail check __getstate__()
		assert isinstance(packet, packets.client.cmd_creategame)
		self.uuid          = uuid.uuid1().hex
		self.mapname       = packet.mapname
		self.maphash       = packet.maphash
		self.maxplayers    = packet.maxplayers
		self.name          = packet.name
		self.password      = packet.password
		self.creator       = creator
		self.players       = []
		self.playercnt     = 0 # needed for privacy for gamelist-requests
		self.state         = Game.State.Open
		self.add_player(self.creator, packet)

	# for pickle: return only relevant data to the player
	def __getstate__(self):
		# NOTE: don't return _ANY_ private data here as these object
		# will be used to build the public game list. if really necessary remove
		# the private data in packets.data_gameslist.addgame
		# NOTE: this classes are used on the client too, so beware of
		# datatype changes
		state = self.__dict__.copy()

		# overwrite private data
		state['password'] = bool(self.password)

		# make data backwards compatible
		state['creator'] = self.creator.name
		state['clientversion'] = self.creator.version
		if self.creator.protocol == 0:
			state['load'] = self.maphash if self.maphash else None
			del state['maphash']

		return state

	def make_public_copy(self):
		# NOTE: __getstate__ will be called afterwards, so don't delete
		# or overwrite data that will be overwritten/deleted by __getstate__
		game = object.__new__(type(self))
		game.__dict__ = self.__dict__.copy()
		game.players = []
		return game

	# add player to game. packet should be packet received in oncreate/onjoin
	def add_player(self, player, packet):
		player.join(self, packet)
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

	def is_full(self):
		return (self.playercnt == self.maxplayers)

	def is_empty(self):
		return (self.playercnt == 0)

	def is_ready(self):
		count = 0
		for player in self.players:
			if player.ready:
				count += 1
		return (count == self.maxplayers)

	def is_open(self):
		return (self.state == Game.State.Open)

	def has_password(self):
		return bool(self.password)

	def clear(self):
		for player in self.players:
			player.game = None
		del self.players[:]
		self.playercnt = 0

	def __str__(self):
		return "Game(uuid={};maxpl={:d};plcnt={:d};pw={:d};state={})" \
			.format(self.uuid, self.maxplayers, self.playercnt, self.has_password(), Game.State(self.state))

packets.SafeUnpickler.add('server', Game)

#-----------------------------------------------------------------------------

# types of soft errors used by cmd_error
# this way we don't have to create a new packet for every type of error
class ErrorType(object):
	NotSet = 0
	TerminateGame = 1

	def __init__(self, state=NotSet):
		self.state = state

	def __str__(self):
		strvals = ["NotSet", "TerminateGame"]
		return strvals[self.state]

packets.SafeUnpickler.add('common', ErrorType)
