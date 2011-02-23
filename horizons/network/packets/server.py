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

import copy

class data_gameslist(packet):
	def __init__(self):
		self.games = []

	def addgame(self, game):
		newgame = copy.copy(game)
		newgame.players = []
		self.games.append(newgame)

packetlist.append(data_gameslist)

#-------------------------------------------------------------------------------

class data_gamestate(packet):
	def __init__(self, game):
		self.game = game;

packetlist.append(data_gamestate)

#-------------------------------------------------------------------------------

class cmd_chatmsg(packet):
	def __init__(self, playername, msg):
		self.playername = playername
		self.chatmsg    = msg

packetlist.append(cmd_chatmsg)

#-------------------------------------------------------------------------------

class cmd_holepunching(packet):
	def __init__(self):
		"""start hole punching"""

packetlist.append(cmd_holepunching)

#-------------------------------------------------------------------------------

class cmd_startgame(packet):
	def __init__(self):
		"""start game packet"""

packetlist.append(cmd_startgame)

