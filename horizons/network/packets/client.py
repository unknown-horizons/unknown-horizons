# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

class cmd_creategame(packet):
	def __init__(self, clientver, mapname, maxplayers, playername):
		self.clientversion = clientver
		self.mapname       = mapname
		self.maxplayers    = maxplayers
		self.playername    = playername

packetlist.append(cmd_creategame)

#-------------------------------------------------------------------------------

class cmd_listgames(packet):
	def __init__(self, clientver, mapname = None, maxplayers = None):
		self.clientversion = clientver
		self.mapname       = mapname
		self.maxplayers    = maxplayers

packetlist.append(cmd_listgames)

#-------------------------------------------------------------------------------

class cmd_joingame(packet):
	def __init__(self, uuid, clientver, playername):
		if type(uuid) == str:
			self.uuid = UUID(uuid)
		else:
			self.uuid = uuid
		self.clientversion = clientver
		self.playername    = playername

packetlist.append(cmd_joingame)

#-------------------------------------------------------------------------------

class cmd_leavegame(packet):
	def __init__(self):
		"""ctor"""

packetlist.append(cmd_leavegame)

#-------------------------------------------------------------------------------

class cmd_chatmsg(packet):
	def __init__(self, msg):
		self.chatmsg = msg

packetlist.append(cmd_chatmsg)

#-------------------------------------------------------------------------------

class cmd_holepunchingok(packet):
	def __init__(self):
		"""hole punching done"""

packetlist.append(cmd_holepunchingok)

