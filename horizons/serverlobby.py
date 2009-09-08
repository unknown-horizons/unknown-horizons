# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import horizons.main
from horizons.util.color import Color
from horizons.network import MPPlayer, ClientConnection, ServerConnection
from horizons.packets import *


# FIXME: update the values by using widget.capture, not by polling

class ServerLobby(object):
	"""Manages the data for the serverlobby

	Data includes information about players, map, etc.
	Infos about the player that plays on this machine
	(local_player) are also stored here
	"""
	guiUpdateInterval = 1

	def __init__(self, gui):
		self.gui = gui

		#horizons.main.ext_scheduler.add_new_object(self._update_gui, self, self.guiUpdateInterval, -1)
		#horizons.main.fife.pump.append(self._update_gui)

	def end(self):
		#horizons.main.ext_scheduler.rem_all_classinst_calls(self)
		#horizons.main.fife.pump.remove(self._update_gui)
		pass

	def _update_gui(self):
		""" Updates elements that are common for every lobby and
		calls lobbyspecific update
		"""
		self.update_gui()

		o = horizons.main.connection.mpoptions

		self.gui.distributeInitialData({
			'playerlist' : o['players'],
		})

		if len(o['players']) > 0: # just display colors when playerlist is received
			self.gui.distributeInitialData({
				# display colors that are not taken by a player
				'playercolors' : [ i.name for i in Color if i not in [ j.color for j in o['players'] if j.color != None ] ]
			})

		if not o['bots'] is None:
			self.gui.distributeData({'bots' : o['bots']})

class MasterServerLobby(ServerLobby):
	"""Serverlobby from the view of the game server

	This class has the privileges to change important game settings
	"""
	def __init__(self, gui):
		super(MasterServerLobby, self).__init__(gui)
		o = horizons.main.connection.mpoptions
		o['maps'] = horizons.main.getMaps(showOnlySaved = False)
		o['bots'] = 0
		self.gui.distributeInitialData({
			'server_slots' : range(2, 9),
			'maplist' : o['maps'][1],
			'bots' : range(0, 1)
		})
		self.gui.distributeData({
			'server_slots' : 2, # 2 means 4 slots
			'bots' : o['bots']
		})
		o['players'].append(horizons.main.connection.local_player)

	def update_gui(self):
		o = horizons.main.connection.mpoptions
		o['slots'] = self.gui.collectData('server_slots')+2

		horizons.main.connection.local_player.name = self.gui.collectData('playername')
		horizons.main.connection.local_player.color = Color[self.gui.collectData('playercolor')+1]
		o['bots'] = self.gui.collectData('bots')

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
		o = horizons.main.connection.mpoptions
		self.gui.distributeInitialData({
			'bots' : [] if o['bots'] is None else [o['bots']],
			'server_slots' : [] if o['slots'] is None else [o['slots']],
			'maplist' : [] if len(o['maps']) == 0 else o['maps'][1]
		})

		self.gui.distributeData({
			'bots' : 0,
			'server_slots' : 0,
			'maplist' : o['selected_map']
		})

		newName = self.gui.collectData('playername')
		newColor = Color[self.gui.collectData('playercolor')+1]

		if horizons.main.connection.local_player.name != newName or \
			horizons.main.connection.local_player.color != newColor:
				horizons.main.connection.local_player.name = newName
				horizons.main.connection.local_player.color = newColor
				horizons.main.connection.sendToServer(LobbyPlayerModifiedPacket(None, None, horizons.main.connection.local_player))
