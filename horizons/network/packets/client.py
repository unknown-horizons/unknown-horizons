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

from horizons.network import NetworkException, SoftNetworkException
from horizons.network.packets import SafeUnpickler, packet


class cmd_creategame(packet):
	clientversion = None # type: str
	clientid = None # type: str
	playername = None # type: str
	playercolor = None # type: int
	gamename = "Unnamed Game"
	mapname = None # type: str
	maxplayers = None # type: int
	maphash = ""
	password = ""

	def __init__(self, clientver, clientid, playername, playercolor,
			gamename, mapname, maxplayers, maphash="", password=""):
		self.clientversion = clientver
		self.clientid = clientid
		self.playername = playername
		self.playercolor = playercolor
		self.name = gamename
		self.mapname = mapname
		self.maxplayers = maxplayers
		self.maphash = maphash
		self.password = password

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.clientversion, str):
			raise NetworkException("Invalid datatype: clientversion")
		if not pkt.clientversion:
			raise SoftNetworkException("Invalid client version")

		if protocol == 0:
			pkt.clientid = uuid.uuid4().hex
		if not isinstance(pkt.clientid, str):
			raise NetworkException("Invalid datatype: clientid")
		if len(pkt.clientid) != 32:
			raise SoftNetworkException("Invalid unique player ID")

		if not isinstance(pkt.playername, str):
			raise NetworkException("Invalid datatype: playername")
		if not pkt.playername:
			raise SoftNetworkException("Your player name cannot be empty")

		if protocol == 0:
			# hardcoded playercolor
			pkt.playercolor = 1
		else:
			if not isinstance(pkt.playercolor, int):
				raise NetworkException("Invalid datatype: playercolor")
			if pkt.playercolor < 1:
				raise SoftNetworkException("Your color is invalid")

		if not isinstance(pkt.name, str):
			raise NetworkException("Invalid datatype: name")
		if not pkt.name:
			pkt.name = "Unnamed Game"

		if not isinstance(pkt.mapname, str):
			raise NetworkException("Invalid datatype: mapname")
		if not pkt.mapname:
			raise SoftNetworkException("You can't run a game with an empty mapname")

		if not isinstance(pkt.maxplayers, int):
			raise NetworkException("Invalid datatype: maxplayers")

		if protocol == 0:
			if pkt.load is None:
				pkt.maphash = ""
			elif isinstance(pkt.load, str):
				pkt.maphash = pkt.load
		if not isinstance(pkt.maphash, str):
			raise NetworkException("Invalid datatype: maphash")

		if not isinstance(pkt.password, str):
			raise NetworkException("Invalid datatype: password")


SafeUnpickler.add('client', cmd_creategame)


#-------------------------------------------------------------------------------
class cmd_listgames(packet):
	clientversion = 0
	mapname = None # type: str
	maxplayers = None # type: int

	def __init__(self, clientver, mapname=None, maxplayers=None):
		self.clientversion = clientver
		self.mapname = mapname
		self.maxplayers = maxplayers

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.clientversion, (int, str)):
			raise NetworkException("Invalid datatype: clientversion")
		if pkt.mapname is not None and not isinstance(pkt.mapname, str):
			raise NetworkException("Invalid datatype: mapname")
		if pkt.maxplayers is not None and not isinstance(pkt.maxplayers, int):
			raise NetworkException("Invalid datatype: maxplayers")


SafeUnpickler.add('client', cmd_listgames)


#-------------------------------------------------------------------------------
class cmd_joingame(packet):
	uuid = None # type: str
	clientid = None # type: str
	clientversion = None # type: str
	playername = None # type: str
	playercolor = None # type: int
	password = ""
	fetch = False

	def __init__(self, uuid, clientver, clientid, playername, playercolor, password="", fetch=False):
		self.uuid = uuid
		self.clientversion = clientver
		self.clientid = clientid
		self.playername = playername
		self.playercolor = playercolor
		self.password = password
		self.fetch = fetch

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.uuid, str):
			raise NetworkException("Invalid datatype: uuid")
		if len(pkt.uuid) != 32:
			raise SoftNetworkException("Invalid game UUID")

		if not isinstance(pkt.clientversion, str):
			raise NetworkException("Invalid datatype: clientversion")
		if not pkt.clientversion:
			raise SoftNetworkException("Invalid client version")

		if protocol == 0:
			pkt.clientid = uuid.uuid4().hex
		if not isinstance(pkt.clientid, str):
			raise NetworkException("Invalid datatype: clientid")
		if len(pkt.clientid) != 32:
			raise SoftNetworkException("Invalid unique player ID")

		if not isinstance(pkt.playername, str):
			raise NetworkException("Invalid datatype: playername")
		if not pkt.playername:
			raise SoftNetworkException("Your player name cannot be empty")

		if protocol == 0:
			# assign playercolor in packet handler
			pkt.playercolor = None
		else:
			if not isinstance(pkt.playercolor, int):
				raise NetworkException("Invalid datatype: playercolor")
			if pkt.playercolor < 1:
				raise SoftNetworkException("Your color is invalid")

		if not isinstance(pkt.password, str):
			raise NetworkException("Invalid datatype: password")

		if not isinstance(pkt.fetch, bool):
			raise NetworkException("Invalid datatype: fetch")


SafeUnpickler.add('client', cmd_joingame)


#-------------------------------------------------------------------------------
class cmd_leavegame(packet):
	def __init__(self):
		"""ctor"""


SafeUnpickler.add('client', cmd_leavegame)


#-------------------------------------------------------------------------------
class cmd_chatmsg(packet):
	chatmsg = None # type: str

	def __init__(self, msg):
		self.chatmsg = msg

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.chatmsg, str):
			raise NetworkException("Invalid datatype: chatmsg")
		if not pkt.chatmsg:
			raise SoftNetworkException("Chat message cannot be empty")


SafeUnpickler.add('client', cmd_chatmsg)


#-------------------------------------------------------------------------------
class cmd_changename(packet):
	playername = None # type: str

	def __init__(self, playername):
		self.playername = playername

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.playername, str):
			raise NetworkException("Invalid datatype: playername")
		if not pkt.playername:
			raise SoftNetworkException("You must have a non empty name")


SafeUnpickler.add('client', cmd_changename)


#-------------------------------------------------------------------------------
class cmd_changecolor(packet):
	playercolor = None # type: int

	def __init__(self, playercolor):
		self.playercolor = playercolor

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.playercolor, int):
			raise NetworkException("Invalid datatype: playercolor")
		if pkt.playercolor < 1:
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

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.kicksid, str):
			raise NetworkException("Invalid datatype: player sid")
		if len(pkt.kicksid) != 32:
			raise SoftNetworkException("Invalid player sid")


SafeUnpickler.add('client', cmd_kickplayer)


#-------------------------------------------------------------------------------
class cmd_sessionprops(packet):
	def __init__(self, props):
		if 'lang' in props:
			self.lang = props['lang']

	@staticmethod
	def validate(pkt, protocol):
		if hasattr(pkt, 'lang'):
			if not isinstance(pkt.lang, str):
				raise NetworkException("Invalid datatype: lang")
			if not pkt.lang:
				raise SoftNetworkException("Invalid language property")


SafeUnpickler.add('client', cmd_sessionprops)


#-------------------------------------------------------------------------------
#TODO
class cmd_mapdata(packet):
	def __init__(self, data):
		self.data = data

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.data, str):
			raise NetworkException("Invalid datatype: data")


SafeUnpickler.add('client', cmd_mapdata)
