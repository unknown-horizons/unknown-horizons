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

import logging

from horizons.network import packets
from horizons.network.connection import Connection
from horizons import network
from horizons.network.common import *


class ClientMode(object):
	Server = 0
	Game = 1

class Client(object):
	log = logging.getLogger("network")

	def __init__(self, name, version, server_address, client_address=None, color=None, clientid=None):
		self.connection = Connection(self.process_async_packet, server_address, client_address)

		self.name          = name
		self.version       = version
		self.mode          = None
		self.sid           = None
		self.capabilities  = None
		self.game          = None
		self.clientid      = clientid
		self.color         = color
		self.callbacks     = {
			'lobbygame_chat':        [],
			'lobbygame_join':        [],
			'lobbygame_leave':       [],
			'lobbygame_terminate':   [],
			'lobbygame_toggleready': [],
			'lobbygame_changename':  [],
			'lobbygame_kick':        [],
			'lobbygame_changecolor': [],
			'lobbygame_state':       [],
			'lobbygame_starts':      [],
			'game_starts':    [],
			'game_data':      [],
			'savegame_data':  [], #TODO
		}
		self.register_callback('lobbygame_changename',  self.onchangename, True)
		self.register_callback('lobbygame_changecolor', self.onchangecolor, True)

	def register_callback(self, type, callback, prepend=False, unique=True):
		if type in self.callbacks:
			if unique and callback in self.callbacks[type]:
				return
			if prepend:
				self.callbacks[type].insert(0, callback)
			else:
				self.callbacks[type].append(callback)
		else:
			raise TypeError("Unsupported type")

	def call_callbacks(self, type, *args):
		if not type in self.callbacks:
			return
		for callback in self.callbacks[type]:
			callback(*args)

	#-----------------------------------------------------------------------------

	def ping(self):
		return self.connection.ping()

	def connect(self):
		packet = self.connection.connect()
		self.sid = packet[1].sid
		self.capabilities = packet[1].capabilities
		self.mode = ClientMode.Server
		self.log.debug("[CONNECT] done (session=%s)" % (self.sid))

	#-----------------------------------------------------------------------------

	def disconnect(self, **kwargs):
		self.mode = None
		self.connection.disconnect(**kwargs)

	#-----------------------------------------------------------------------------

	def isconnected(self):
		return self.connection.is_connected

	#-----------------------------------------------------------------------------

	def reset(self):
		self.connection.reset()
		self.mode = None
		self.game = None

	#-----------------------------------------------------------------------------

	def send(self, packet, channelid=0):
		if self.mode is ClientMode.Game:
			packet = packets.client.game_data(packet)

		self.connection.send(packet, channelid)

	#-----------------------------------------------------------------------------

	# return True if packet was processed successfully
	# return False if packet should be queue
	def process_async_packet(self, packet):
		if packet is None:
			return True
		if isinstance(packet[1], packets.server.cmd_chatmsg):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.call_callbacks("lobbygame_chat", self.game, packet[1].playername, packet[1].chatmsg)
		elif isinstance(packet[1], packets.server.data_gamestate):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.call_callbacks("lobbygame_state", self.game, packet[1].game)

			oldplayers = list(self.game.players)
			self.game = packet[1].game

			# calculate changeset
			for pnew in self.game.players:
				found = None
				for pold in oldplayers:
					if pnew.sid == pold.sid:
						found = pold
						myself = (pnew.sid == self.sid)
						if pnew.name != pold.name:
							self.call_callbacks("lobbygame_changename", self.game, pold, pnew, myself)
						if pnew.color != pold.color:
							self.call_callbacks("lobbygame_changecolor", self.game, pold, pnew, myself)
						if pnew.ready != pold.ready:
							self.call_callbacks("lobbygame_toggleready", self.game, pold, pnew, myself)
						break
				if found is None:
					self.call_callbacks("lobbygame_join", self.game, pnew)
				else:
					oldplayers.remove(found)
			for pold in oldplayers:
				self.call_callbacks("lobbygame_leave", self.game, pold)
			return True
		elif isinstance(packet[1], packets.server.cmd_preparegame):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.ongameprepare()
		elif isinstance(packet[1], packets.server.cmd_startgame):
			# ignore packet if we are not a game lobby
			if self.game is None:
				return True
			self.ongamestart()
		elif isinstance(packet[1], packets.client.game_data):
			self.log.debug("[GAMEDATA] from %s" % (packet[0].address))
			self.call_callbacks("game_data", packet[1].data)
		elif isinstance(packet[1], packets.server.cmd_kickplayer):
			player = packet[1].player
			game = self.game
			myself = (player.sid == self.sid)
			if myself:
				# this will destroy self.game
				self.leavegame(stealth=True)
			self.call_callbacks("lobbygame_kick", game, player, myself)

		return False

	#-----------------------------------------------------------------------------

	def setprops(self, lang):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[SETPROPS]")
		self.send(packets.client.cmd_sessionprops(lang))
		packet = self.connection.receive_packet(packets.cmd_ok)
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.cmd_ok):
			raise network.CommandError("Unexpected packet")
		return True

	#-----------------------------------------------------------------------------

	def listgames(self, mapname=None, maxplayers=None, only_this_version=False):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[LIST]")
		version = self.version if only_this_version else -1
		self.send(packets.client.cmd_listgames(version, mapname, maxplayers))
		packet = self.connection.receive_packet(packets.server.data_gameslist)
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.data_gameslist):
			raise network.CommandError("Unexpected packet")
		return packet[1].games

	#-----------------------------------------------------------------------------

	def creategame(self, mapname, maxplayers, gamename, maphash="", password=""):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[CREATE] mapname=%s maxplayers=%d" % (mapname, maxplayers))
		self.send(packets.client.cmd_creategame(
			clientver   = self.version,
			clientid    = self.clientid,
			playername  = self.name,
			playercolor = self.color,
			gamename    = gamename,
			mapname     = mapname,
			maxplayers  = maxplayers,
			maphash     = maphash,
			password    = password))
		packet = self.connection.receive_packet(packets.server.data_gamestate)
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.data_gamestate):
			raise network.CommandError("Unexpected packet")
		self.game = packet[1].game
		return self.game

	#-----------------------------------------------------------------------------

	def joingame(self, uuid, password="", fetch=False):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		self.log.debug("[JOIN] %s" % (uuid))
		self.send(packets.client.cmd_joingame(
			uuid        = uuid,
			clientver   = self.version,
			clientid    = self.clientid,
			playername  = self.name,
			playercolor = self.color,
			password    = password,
			fetch       = fetch))
		packet = self.connection.receive_packet(packets.server.data_gamestate)
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.server.data_gamestate):
			raise network.CommandError("Unexpected packet")
		self.game = packet[1].game
		return self.game

	#-----------------------------------------------------------------------------

	def leavegame(self, stealth=False):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		if self.game is None:
			raise network.NotInGameLobby("We are not in a game lobby")
		self.log.debug("[LEAVE]")
		if stealth:
			self.game = None
			return
		self.send(packets.client.cmd_leavegame())
		packet = self.connection.receive_packet(packets.cmd_ok)
		if packet is None:
			raise network.FatalError("No reply from server")
		elif not isinstance(packet[1], packets.cmd_ok):
			raise network.CommandError("Unexpected packet")
		self.game = None
		return True

	#-----------------------------------------------------------------------------

	def chat(self, message):
		if self.mode is None:
			raise network.NotConnected()
		if self.mode is not ClientMode.Server:
			raise network.NotInServerMode("We are not in server mode")
		if self.game is None:
			raise network.NotInGameLobby("We are not in a game lobby")
		self.log.debug("[CHAT] %s" % (message))
		self.send(packets.client.cmd_chatmsg(message))
		return True

	#-----------------------------------------------------------------------------

	def changename(self, name):
		""" NOTE: this returns False if the name must be validated by
		the server. In that case this will trigger a lobbygame_changename-
		event with parameter myself=True. if this functions returns true
		your name has been changed but there was no need to sent it to
		the server."""
		if self.name == name:
			return True
		self.log.debug("[CHANGENAME] %s" % (name))
		if self.mode is None or self.game is None:
			self.name = name
			return True
		self.send(packets.client.cmd_changename(name))
		return False

	#-----------------------------------------------------------------------------

	def onchangename(self, game, plold, plnew, myself):
		self.log.debug("[ONCHANGENAME] %s -> %s" % (plold.name, plnew.name))
		if myself:
			self.name = plnew.name
		return True

	#-----------------------------------------------------------------------------

	def changecolor(self, color):
		""" NOTE: this returns False if the name must be validated by
		 the server. In that case this will trigger a lobbygame_changecolor-
		 event with parameter myself=True. if this functions returns true
		 your name has been changed but there was no need to sent it to
		 the server."""
		if self.color == color:
			return True
		self.log.debug("[CHANGECOLOR] %s" % (color))
		if self.mode is None or self.game is None:
			self.color = color
			return True
		self.send(packets.client.cmd_changecolor(color))
		return False

	#-----------------------------------------------------------------------------

	def onchangecolor(self, game, plold, plnew, myself):
		self.log.debug("[ONCHANGECOLOR] %s: %s -> %s" % (plnew.name, plold.color, plnew.color))
		if myself:
			self.color = plnew.color
		return True

	#-----------------------------------------------------------------------------

	def ongameprepare(self):
		self.log.debug("[GAMEPREPARE]")
		self.game.state = Game.State.Prepare
		self.call_callbacks("lobbygame_starts", self.game)
		self.send(packets.client.cmd_preparedgame())
		return True

	#-----------------------------------------------------------------------------

	def ongamestart(self):
		self.log.debug("[GAMESTART]")
		self.game.state = Game.State.Running
		self.mode = ClientMode.Game
		self.call_callbacks("game_starts", self.game)
		return True

	#-----------------------------------------------------------------------------

	def toggleready(self):
		self.log.debug("[TOGGLEREADY]")
		self.send(packets.client.cmd_toggleready())
		return True

	#-----------------------------------------------------------------------------

	def kick(self, player_sid):
		self.log.debug("[KICK]")
		self.send(packets.client.cmd_kickplayer(player_sid))
		return True

	#-----------------------------------------------------------------------------

	#TODO
	def send_fetch_game(self, clientversion, uuid):
		self.send(packets.client.cmd_fetch_game(clientversion, uuid))
		return True
