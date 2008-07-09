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

import game.main
import time


# There are two ways of sending packets without specifing target ip/port:
# 1. Server sends with address and port == None, then it gets sent to all players
# 2. Client uses sendToServer



class Packet(object):
	"""
	@param address:
	@param port:
	"""
	def __init__(self, address, port):
		""" This can just set address and port

		If you want to extend this function, you have to update most of the Packet-classes
		"""
		(self.address,) = None if address is None else str(address),
		self.port = None if port is None else int(port)

	def handleOnServer(self):
		"""Defines how packet is handled when received on game server

		Gets overwritten in every packet subclass, that has to be
		handled on a server
		TIP: you can access (Server|Client)connection via game.main.connection
		"""
		print "Warning: unhandled packet on server:",self

	def handleOnClient(self):
		"""Defines how packet is handled when received on game client

		Gets overwritten in every packet subclass, that has to be
		handled on a client
		"""
		print "Warning: unhandled packet on client:",self


class TickPacket(Packet):
	"""
	@param address:
	@param port:
	@param tick:
	@param commands:
	"""
	def __init__(self, address, port, tick, commands):
		super(TickPacket, self).__init__(address, port)
		self.tick = tick
		self.commands = commands

class QueryPacket(Packet):
	"""Client sends this to discover servers
	"""
	def handleOnServer(self):
		o = game.main.connection.mpoptions
		game.main.connection.send(InfoPacket(self.address, self.port, 'unknown map' if o['selected_map'] == -1 else o['maps'][1][o['selected_map']], len(o['players']), 0 if o['bots'] is None else o['bots'], 0 if o['slots'] is None else o['slots']))


class LobbyChatPacket(Packet):
	"""
	@param address:
	@param port:
	@param text:
	"""
	def __init__(self, address, port, text):
		super(ChatPacket, self).__init__(address, port)
		self.text = text

class ConnectPacket(Packet):
	pass

class LobbyJoinPacket(Packet):
	"""Use this to join a game
	"""
	def __init__(self, address, port, player):
		super(LobbyJoinPacket, self).__init__(address, port)
		self.player = player

	def handleOnServer(self):
		self.player.address, self.player.port = self.address, self.port
		game.main.connection.mpoptions['players'].append(self.player)
		game.main.connection.last_client_message[(self.player.address, self.player.port)] = time.time()
		print 'JOIN BY', self.player.address, self.player.port
		game.main.connection.notifyClients()

class LeaveServerPacket(Packet):
	"""Use this to leave a server
	"""
	def __init__(self):
		pass

	def handleOnServer(self):
		for player in game.main.connection.mpoptions['players']:
			if player.address == self.address and player.port == self.port:
				print 'LEAVE BY', self.address, self.port
				game.main.connection.mpoptions['players'].remove(player)

class LobbyPlayerModifiedPacket(Packet):
	"""Notifes server about changes to the local player
	"""
	def __init__(self, address, port, player):
		super(LobbyPlayerModifiedPacket, self).__init__(address, port)
		self.player = player

	def handleOnServer(self):
		self.player.address, self.player.port = self.address, self.port
		players = game.main.connection.mpoptions['players']
		for i in xrange(0, len(players)):
			if players[i].address == self.address and players[i].port == self.port:
				players[i] = self.player
				break
		game.main.connection.notifyClients()

class LobbyKeepAlivePacket(Packet):
	"""Sent regularly to master server to tell it that we are still there"""
	def __init__(self):
		pass

	def handleOnServer(self):
		game.main.connection.last_client_message[(self.address, self.port)] = time.time()


# MAYBE:
# try to tell client when he got disconnected
# packet might not arrive
# but he could be kicked for another reason
# so include a parameter in the packet which tells the client why he got disconnected

# packet when server is closed. probably packet above can be used

class MasterRegisterPacket(Packet):
	pass

class MasterServerListQueryPacket(Packet):
	pass

class MasterServerListAnswerPacket(Packet):
	pass

class MasterVersionPacket(Packet):
	pass

class MasterRegisterPacket(Packet):
	"""
	@param port: port on which local game server runs
	"""
	def __init__(self, port):
		super(MasterRegisterPacket, self).__init__(game.main.settings.network.url_master, game.main.settings.network.port)
		self.myport = port

class InfoPacket(Packet):
	"""
	@param address:
	@param port:
	@param map:
	@param players:
	@param bots:
	@param maxplayers:
	"""
	def __init__(self, address, port, map, players, bots, maxplayers):
		super(InfoPacket, self).__init__(address, port)
		self.map, self.players, self.bots, self.maxplayers = map, players, bots, maxplayers


class LobbyServerInfoPacket(Packet):
	""" Contains info about multiplayer game

	The game server sends this packet to clients
	to notify them about game settings
	NOTE: address & port are none, because this way the packet gets sent to all clients
	"""
	def __init__(self, mpoptions, address = None, port = None):
		super(LobbyServerInfoPacket, self).__init__(address, port)
		self.mpoptions = mpoptions

	def handleOnClient(self):
		game.main.connection.mpoptions = self.mpoptions

	def handleOnServer(self):
		# server sent this, so it can ignore it
		pass

