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

class cmd_creategame(packet):
	def __init__(self, clientver, mapname, maxplayers, playername, load=False):
		"""
		@param load: whether it's a loaded game
		"""
		self.clientversion = clientver
		self.mapname       = mapname
		self.maxplayers    = maxplayers
		self.playername    = playername
		self.load          = load

SafeUnpickler.add('client', cmd_creategame)

#-------------------------------------------------------------------------------

class cmd_listgames(packet):
	def __init__(self, clientver, mapname = None, maxplayers = None):
		self.clientversion = clientver
		self.mapname       = mapname
		self.maxplayers    = maxplayers

SafeUnpickler.add('client', cmd_listgames)

#-------------------------------------------------------------------------------

class cmd_joingame(packet):
	def __init__(self, uuid, clientver, playername):
		self.uuid = uuid
		self.clientversion = clientver
		self.playername    = playername

SafeUnpickler.add('client', cmd_joingame)

#-------------------------------------------------------------------------------

class cmd_leavegame(packet):
	def __init__(self):
		"""ctor"""

SafeUnpickler.add('client', cmd_leavegame)

#-------------------------------------------------------------------------------

class cmd_chatmsg(packet):
	def __init__(self, msg):
		self.chatmsg = msg

SafeUnpickler.add('client', cmd_chatmsg)

#-------------------------------------------------------------------------------

class cmd_changename(packet):
	def __init__(self, playername):
		self.playername = playername

SafeUnpickler.add('client', cmd_changename)

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

