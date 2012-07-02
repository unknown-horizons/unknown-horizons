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

import copy

class cmd_session(packet):
	def __init__(self, sid):
		self.sid = sid

SafeUnpickler.add('server', cmd_session)

#-------------------------------------------------------------------------------

class data_gameslist(packet):
	def __init__(self):
		self.games = []

	def addgame(self, game):
		newgame = copy.copy(game)
		newgame.players = []
		self.games.append(newgame)

SafeUnpickler.add('server', data_gameslist)

#-------------------------------------------------------------------------------

class data_gamestate(packet):
	def __init__(self, game):
		self.game = game

SafeUnpickler.add('server', data_gamestate)

#-------------------------------------------------------------------------------

class cmd_chatmsg(packet):
	def __init__(self, playername, msg):
		self.playername = playername
		self.chatmsg    = msg

SafeUnpickler.add('server', cmd_chatmsg)

#-------------------------------------------------------------------------------

class cmd_preparegame(packet):
	def __init__(self):
		"""prepare game packet"""

SafeUnpickler.add('server', cmd_preparegame)

#-------------------------------------------------------------------------------

class cmd_startgame(packet):
	def __init__(self):
		"""start game packet"""

SafeUnpickler.add('server', cmd_startgame)

#-------------------------------------------------------------------------------

class cmd_kick_player(packet):
	def __init__(self, player):
		self.player = player

SafeUnpickler.add('server', cmd_kick_player)

#-------------------------------------------------------------------------------

class cmd_fetch_game(packet):
	def __init__(self, psid):
		"""fetch game packet"""
		self.psid = psid

SafeUnpickler.add('server', cmd_fetch_game)

#-------------------------------------------------------------------------------

class savegame_data(packet):
	def __init__(self, data, psid, mapname):
		self.data = data
		self.psid = psid
		self.mapname = mapname

SafeUnpickler.add('server', savegame_data)