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

from horizons.network.packets import *
from horizons.network import NetworkException

class cmd_creategame(packet):
	clientversion = None
	mapname       = None
	maxplayers    = None
	playername    = None
	playercolor   = None
	clientid      = None
	name          = u"Unnamed Game"
	load          = None
	password      = None

	def __init__(self, clientver, mapname, maxplayers, playername, name, load=None, password=None, playercolor=None, clientid=None):
		"""
		@param load: whether it's a loaded game
		"""
		self.clientversion = clientver
		self.mapname       = mapname
		self.maxplayers    = maxplayers
		self.playername    = playername
		self.name          = name
		self.load          = load
		self.password      = None if password == "" else password
		self.playercolor   = playercolor
		self.clientid      = clientid

	def validate(self):
		if not isinstance(self.clientversion, unicode):
			raise NetworkException("Invalid datatype: clientversion")
		if not isinstance(self.mapname, unicode):
			raise NetworkException("Invalid datatype: mapname")
		if not isinstance(self.maxplayers, int):
			raise NetworkException("Invalid datatype: maxplayers")
		if not isinstance(self.playername, unicode):
			raise NetworkException("Invalid datatype: playername")
		if not isinstance(self.name, unicode):
			raise NetworkException("Invalid datatype: name")
		if self.load is not None and not isinstance(self.load, str):
			raise NetworkException("Invalid datatype: load")
		if not isinstance(self.playercolor, int):
			raise NetworkException("Invalid datatype: playercolor")

SafeUnpickler.add('client', cmd_creategame)

#-------------------------------------------------------------------------------

class cmd_listgames(packet):
	clientversion = 0
	mapname       = None
	maxplayers    = None

	def __init__(self, clientver, mapname=None, maxplayers=None):
		self.clientversion = clientver
		self.mapname       = mapname
		self.maxplayers    = maxplayers

	def validate(self):
		if not isinstance(self.clientversion, (int, unicode)):
			raise NetworkException("Invalid datatype: clientversion")
		if self.mapname is not None and not isinstance(self.mapname, unicode):
			raise NetworkException("Invalid datatype: mapname")
		if self.maxplayers is not None and not isinstance(self.maxplayers, int):
			raise NetworkException("Invalid datatype: maxplayers")

SafeUnpickler.add('client', cmd_listgames)

#-------------------------------------------------------------------------------

class cmd_joingame(packet):
	uuid          = None
	clientversion = None
	playername    = None
	playercolor   = None
	clientid      = None

	def __init__(self, uuid, clientver, playername, playercolor, clientid):
		self.uuid          = uuid
		self.clientversion = clientver
		self.playername    = playername
		self.playercolor   = playercolor
		self.clientid      = clientid

	def validate(self):
		if not isinstance(self.uuid, str):
			raise NetworkException("Invalid datatype: uuid")
		if not isinstance(self.clientversion, unicode):
			raise NetworkException("Invalid datatype: clientversion")
		if not isinstance(self.playername, unicode):
			raise NetworkException("Invalid datatype: playername")
		if not isinstance(self.playercolor, int):
			raise NetworkException("Invalid datatype: playercolor")

SafeUnpickler.add('client', cmd_joingame)

#-------------------------------------------------------------------------------

class cmd_leavegame(packet):
	def __init__(self):
		"""ctor"""

SafeUnpickler.add('client', cmd_leavegame)

#-------------------------------------------------------------------------------

class cmd_chatmsg(packet):
	chatmsg = None

	def __init__(self, msg):
		self.chatmsg = msg

	def validate(self):
		if not isinstance(self.chatmsg, unicode):
			raise NetworkException("Invalid datatype: chatmsg")

SafeUnpickler.add('client', cmd_chatmsg)

#-------------------------------------------------------------------------------

class cmd_changename(packet):
	playername = None

	def __init__(self, playername):
		self.playername = playername

	def validate(self):
		if not isinstance(self.playername, unicode):
			raise NetworkException("Invalid datatype: playername")

SafeUnpickler.add('client', cmd_changename)

#-------------------------------------------------------------------------------

class cmd_changecolor(packet):
	playercolor = None

	def __init__(self, playercolor):
		self.playercolor = playercolor

	def validate(self):
		if not isinstance(self.playercolor, int):
			raise NetworkException("Invalid datatype: playercolor")

SafeUnpickler.add('client', cmd_changecolor)

#-------------------------------------------------------------------------------

class cmd_preparedgame(packet):
	def __init__(self):
		"""ctor"""

SafeUnpickler.add('client', cmd_preparedgame)

#-------------------------------------------------------------------------------

class game_data(packet):
	def __init__(self, data):
		self.data = data

# origin is 'server' as clients will send AND receive them
SafeUnpickler.add('server', game_data)

#-------------------------------------------------------------------------------

class cmd_toggle_ready(packet):
	def __init__(self, player):
		self.player = player

	def validate(self):
		if not isinstance(self.player, unicode):
			raise NetworkException("Invalid datatype: player")

SafeUnpickler.add('client', cmd_toggle_ready)

#-------------------------------------------------------------------------------

class cmd_kick_player(packet):
	def __init__(self, player):
		self.player = player

	def validate(self):
		if not isinstance(self.player, unicode):
			raise NetworkException("Invalid datatype: player")

SafeUnpickler.add('client', cmd_kick_player)

#-------------------------------------------------------------------------------

class cmd_fetch_game(packet):
	def __init__(self, clientversion, uuid):
		self.clientversion = clientversion
		self.uuid = uuid

	def validate(self):
		if not isinstance(self.uuid, str):
			raise NetworkException("Invalid datatype: uuid")
		if not isinstance(self.clientversion, unicode):
			raise NetworkException("Invalid datatype: clientversion")

SafeUnpickler.add('client', cmd_fetch_game)

#-------------------------------------------------------------------------------

class savegame_data(packet):
	def __init__(self, data, psid):
		self.data = data
		self.psid = psid

SafeUnpickler.add('client', savegame_data)
