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

import platform
import os
import sys


def find_enet_module():
	"""Return the enet module or None.

	We do not raise any errors here, because we still allow clients to play the
	singleplayer.
	If code requires the enet module, it should check if horizons.network.enet is
	not None.
	"""

	# Try to find installed version first
	try:
		import enet
		return enet
	except ImportError:
		pass

	# If not installed, we try to find a suitable library in libs/

	lib_path = os.path.join(os.path.dirname(__file__), "libs")

	type = platform.system().lower()

	arch = platform.architecture()[0]
	if arch == '32bit':
		arch = '86'
	elif arch == '64bit':
		arch = '64'
	else:
		assert False, "Failed to detect system architecture!"

	# Generic identifier, e.g. linux-64
	directory = "{}-x{}".format(type, arch)

	# Python version-specific, e.g. linux-64-27. If this is not found, we fall
	# back to the more generic version.
	version = platform.python_version_tuple()
	directory_pyversion = "{}-{}{}".format(directory, version[0], version[1])

	if os.path.exists(os.path.join(lib_path, directory_pyversion)):
		path = os.path.join(lib_path, directory_pyversion)
	else:
		path = os.path.join(lib_path, directory)

	sys.path.append(path)

	try:
		import enet
		return enet
	except ImportError:
		pass

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
	def __init__(self, message, type):
		super(ClientException, self).__init__(message)
		self.type = type

class FatalError(ClientException):
	pass
