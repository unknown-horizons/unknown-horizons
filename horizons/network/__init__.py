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

import os
import platform
import sys


def find_enet_module():
	"""Return the enet module or None.

	We do not raise any errors here, because we still allow clients to play the
	singleplayer.
	If code requires the enet module, it should check if horizons.network.enet is
	not None.
	"""

	try:
		import enet
		return enet
	except ImportError:
		return None


enet = find_enet_module()

# during pyenets move to cpython they renamed a few constants...
if not hasattr(enet, 'PEER_STATE_DISCONNECTED') and hasattr(enet, 'PEER_STATE_DISCONNECT'):
	enet.PEER_STATE_DISCONNECTED = enet.PEER_STATE_DISCONNECT


class NetworkException(Exception):
	pass


class SoftNetworkException(NetworkException):
	pass


class PacketTooLarge(NetworkException):
	pass


class NotConnected(NetworkException):
	def __str__(self):
		return "Client is not connected"


class ClientException(NetworkException):
	pass


class AlreadyConnected(ClientException):
	pass


class NotInGameLobby(ClientException):
	pass


class NotInServerMode(ClientException):
	pass


class UnableToConnect(ClientException):
	pass


class CommandError(ClientException):
	def __init__(self, message, cmd_type):
		super().__init__(message)
		self.cmd_type = cmd_type


class FatalError(ClientException):
	pass
