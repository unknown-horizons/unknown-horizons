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
from fife import Color
from game.network import MPPlayer, ClientConnection, ServerConnection
from game.packets import *


# TODO: serverlobby doesn't get deleted
# the problem lies in main.(join|create)Server

class ServerLobby(object):
	"""Manages the data for the serverlobby

	Data includes information about players, map, etc.
	Infos about the player that plays on this machine
	(local_player) are also stored here
	"""
	guiUpdateInterval = 1

	def __init__(self, gui):
		self.gui = gui

		self.colors = {}
		for (name, r, g, b, alpha) in game.main.db("SELECT name, red, green, blue, alpha from colors"):
			self.colors[name] = Color(r,g,b,alpha)

		game.main.ext_scheduler.add_new_object(self._update_gui, self, self.guiUpdateInterval, -1)
		#game.main.fife.pump.append(self._update_gui)

	def end(self):
		game.main.ext_scheduler.rem_all_classinst_calls(self)
		#game.main.fife.pump.remove(self._update_gui)

	def _update_gui(self):
		""" Updates elements that are common for every lobby and
		calls lobbyspecific update
		"""
		self.update_gui()
		
		o = game.main.connection.mpoptions

		self.gui.distributeInitialData({
			'playerlist' : [ player.name for player in o['players'] ],
		})

		if len(o['players']) > 0: # just display colors when playerlist is received
			self.gui.distributeInitialData({
				# display colors that are not taken by a player
				# try to write this in one line in c++ ;)
				'playercolors' : [ i for i in self.colors.keys() if self.colors[i] not in [ j.color for j in o['players'] if j.color != -1 ] ]
			})

		if not o['bots'] is None:
			self.gui.distributeData({'bots' : o['bots']})


class MasterServerLobby(ServerLobby):
	"""Serverlobby from the view of the game server

	This class has the privileges to change important game settings
	"""
	def __init__(self,gui):
		super(MasterServerLobby, self).__init__(gui)
		o = game.main.connection.mpoptions
		o['maps'] = game.main.getMaps(False)
		o['bots'] = 0
		self.gui.distributeInitialData({
			'server_slots' : range(2,9),
			'maplist' : o['maps'][1],
			'bots' : range(0,1)
		})
		self.gui.distributeData({
			'server_slots' : 2, # 2 means 4 slots
			'bots' : o['bots']
		})
		o['players'].append(game.main.connection.local_player);

	def update_gui(self):
		o = game.main.connection.mpoptions
		o['slots'] = self.gui.collectData('server_slots')+2

		game.main.connection.local_player.name, game.main.connection.local_player.color, o['bots'] = self.gui.collectData('playername','playercolor', 'bots')

		# sanity check for bot count
		if o['bots'] > (o['slots'] - len(o['players'])):
			o['bots'] = o['slots'] - len(o['players'])

		o['selected_map'] = self.gui.collectData('maplist')

		self.gui.distributeInitialData({
			'bots' : range(0, o['slots'] - len(o['players'])+1) # +1 cause to upper limit isn't included
		})
		self.gui.distributeData({
			'bots' : o['bots']
		})

class ClientServerLobby(ServerLobby):
	"""Serverlobby from the view of a client
	"""
	def __init__(self, gui):
		super(ClientServerLobby, self).__init__(gui)
		

	def update_gui(self):
		newName, newColor =  self.gui.collectData('playername','playercolor')
		o = game.main.connection.mpoptions
		self.gui.distributeInitialData({
			'bots' : [] if o['bots'] is None else [o['bots']],
			'server_slots' : [] if o['slots'] is None else [o['slots']],
			'maplist' : [] if len(o['maps']) is 0 else o['maps'][1]
		})

		self.gui.distributeData({
			'bots' : 0,
			'server_slots' : 0,
			'maplist' : o['selected_map']
		})

		if game.main.connection.local_player.name != newName or \
			game.main.connection.local_player.color != newColor:
				game.main.connection.local_player.name = newName
				game.main.connection.local_player.color = newColor
				game.main.connection.sendToServer(LobbyPlayerModifiedPacket(None, None, game.main.connection.local_player))



