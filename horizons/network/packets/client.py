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
from horizons.network import NetworkException, SoftNetworkException
import uuid

class cmd_creategame(packet):
	clientversion = None
	clientid      = None
	playername    = None
	playercolor   = None
	gamename      = u"Unnamed Game"
	mapname       = None
	maxplayers    = None
	maphash       = ""
	password      = ""

	def __init__(self, clientver, clientid, playername, playercolor,
			gamename, mapname, maxplayers, maphash="", password=""):
		self.clientversion = clientver
		self.clientid      = clientid
		self.playername    = playername
		self.playercolor   = playercolor
		self.name          = gamename
		self.mapname       = mapname
		self.maxplayers    = maxplayers
		self.maphash       = maphash
		self.password      = password

	def validate(self, protocol):
		if not isinstance(self.clientversion, unicode):
			raise NetworkException("Invalid datatype: clientversion")
		if not len(self.clientversion):
			raise SoftNetworkException("Invalid client version")

		if protocol == 0:
			self.clientid = uuid.uuid4().hex
		if not isinstance(self.clientid, str):
			raise NetworkException("Invalid datatype: clientid")
		if len(self.clientid) != 32:
			raise SoftNetworkException("Invalid unique player ID")

		if not isinstance(self.playername, unicode):
			raise NetworkException("Invalid datatype: playername")
		if not len(self.playername):
			raise SoftNetworkException("Your player name cannot be empty")

		if protocol == 0:
			self.playercolor = 1
		else:
			if not isinstance(self.playercolor, int):
				raise NetworkException("Invalid datatype: playercolor")
			if self.playercolor < 1:
				raise SoftNetworkException("Your color is invalid")

		if not isinstance(self.name, unicode):
			raise NetworkException("Invalid datatype: name")
		if not len(self.name):
			self.name = u"Unnamed Game"

		if not isinstance(self.mapname, unicode):
			raise NetworkException("Invalid datatype: mapname")
		if not len(self.mapname):
			raise SoftNetworkException("You can't run a game with an empty mapname")

		if not isinstance(self.maxplayers, int):
			raise NetworkException("Invalid datatype: maxplayers")

		if not isinstance(self.maphash, str):
			raise NetworkException("Invalid datatype: maphash")

		if not isinstance(self.password, str):
			raise NetworkException("Invalid datatype: password")

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

	def validate(self, protocol):
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
	clientid      = None
	clientversion = None
	playername    = None
	playercolor   = None
	password      = ""
	fetch         = False

	def __init__(self, uuid, clientver, clientid, playername, playercolor, password="", fetch=False):
		self.uuid          = uuid
		self.clientversion = clientver
		self.clientid      = clientid
		self.playername    = playername
		self.playercolor   = playercolor
		self.password      = password
		self.fetch         = fetch

	def validate(self, protocol):
		if not isinstance(self.uuid, str):
			raise NetworkException("Invalid datatype: uuid")
		if len(self.uuid) != 32:
			raise SoftNetworkException("Invalid game UUID")

		if not isinstance(self.clientversion, unicode):
			raise NetworkException("Invalid datatype: clientversion")
		if not len(self.clientversion):
			raise SoftNetworkException("Invalid client version")

		if protocol == 0:
			self.clientid = uuid.uuid4().hex
		if not isinstance(self.clientid, str):
			raise NetworkException("Invalid datatype: clientid")
		if len(self.clientid) != 32:
			raise SoftNetworkException("Invalid unique player ID")

		if not isinstance(self.playername, unicode):
			raise NetworkException("Invalid datatype: playername")
		if not len(self.playername):
			raise SoftNetworkException("Your player name cannot be empty")

		if protocol == 0:
			# assign playercolor in packet handler
			self.playercolor = None
		else:
			if not isinstance(self.playercolor, int):
				raise NetworkException("Invalid datatype: playercolor")
			if self.playercolor < 1:
				raise SoftNetworkException("Your color is invalid")

		if not isinstance(self.password, str):
			raise NetworkException("Invalid datatype: password")

		if not isinstance(self.fetch, bool):
			raise NetworkException("Invalid datatype: fetch")

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

	def validate(self, protocol):
		if not isinstance(self.chatmsg, unicode):
			raise NetworkException("Invalid datatype: chatmsg")
		if not len(self.chatmsg):
			raise SoftNetworkException("Chat message cannot be empty")

SafeUnpickler.add('client', cmd_chatmsg)

#-------------------------------------------------------------------------------

class cmd_changename(packet):
	playername = None

	def __init__(self, playername):
		self.playername = playername

	def validate(self, protocol):
		if not isinstance(self.playername, unicode):
			raise NetworkException("Invalid datatype: playername")
		if not len(self.playername):
			raise SoftNetworkException("You must have a non empty name")

SafeUnpickler.add('client', cmd_changename)

#-------------------------------------------------------------------------------

class cmd_changecolor(packet):
	playercolor = None

	def __init__(self, playercolor):
		self.playercolor = playercolor

	def validate(self, protocol):
		if not isinstance(self.playercolor, int):
			raise NetworkException("Invalid datatype: playercolor")
		if self.playercolor < 1:
			raise SoftNetworkException("Your color is invalid")

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

class cmd_toggleready(packet):
	def __init__(self):
		"""ctor"""

SafeUnpickler.add('client', cmd_toggleready)

#-------------------------------------------------------------------------------

class cmd_kickplayer(packet):
	def __init__(self, kicksid):
		# NOTE: self.sid is used for session mgmt
		self.kicksid = kicksid

	def validate(self, protocol):
		if not isinstance(self.kicksid, str):
			raise NetworkException("Invalid datatype: player sid")
		if len(self.kicksid) != 32:
			raise SoftNetworkException("Invalid player sid")

SafeUnpickler.add('client', cmd_kickplayer)

#-------------------------------------------------------------------------------

#TODO
class cmd_mapdata(packet):
	def __init__(self, data):
		self.data = data

	def validate(self, protocol):
		if not isinstance(self.data, str):
			raise NetworkException("Invalid datatype: data")

SafeUnpickler.add('client', cmd_mapdata)
