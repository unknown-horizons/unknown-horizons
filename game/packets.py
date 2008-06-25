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

class Packet(object):
	"""
	@param address:
	@param port:
	"""
	def __init__(self, address, port):
		self.address, self.port = str(address), int(port)

class TickPacket(Packet):
	"""
	@param address:
	@param port:
	@param tick:
	@param commands:
	"""
	def __init__(self, address, port, tick, commands):
		super(TickPacket, self).__init__(address, port)
		self.tick = tick
		self.commands = commands

class QueryPacket(Packet):
	pass

class ChatPacket(Packet):
	"""
	@param address:
	@param port:
	@param text:
	"""
	def __init__(self, address, port, text):
		super(ChatPacket, self).__init__(address, port)
		self.text = text

class ConnectPacket(Packet):
	pass

class MasterRegisterPacket(Packet):
	pass

class MasterServerListQueryPacket(Packet):
	pass

class MasterServerListAnswerPacket(Packet):
	pass

class MasterVersionPacket(Packet):
	pass

class MasterRegisterPacket(Packet):
	"""
	@param port:
	"""
	def __init__(self, port):
		self.myport = port

class InfoPacket(Packet):
	"""
	@param address:
	@param port:
	@param map:
	@param players:
	@param bots:
	@param maxplayers:
	"""
	def __init__(self, address, port, map, players, bots, maxplayers):
		super(InfoPacket, self).__init__(address, port)
		self.map, self.players, self.bots, self.maxplayers = map, players, bots, maxplayers
