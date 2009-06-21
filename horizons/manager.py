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

import horizons.timer
import horizons.main
from horizons.packets import TickPacket


from util import decode
from util.living import LivingObject

class SPManager(LivingObject):
	"""The manager class takes care of command issuing to the timermanager, sends tick-packets
	over the network, and syncronisation of network games."""

	def __init__(self):
		self.recording = False
		self.commands = []

	def execute(self, command):
		"""Executes a command
		@param command: Command the command to be executed
		"""
		# if we are in demo playback mode, every incoming command has to be thrown away.
		if len(self.commands) > 0:
			return
		if self.recording:
			horizons.main.db("INSERT INTO demo.command (tick, issuer, data) VALUES (?, ?, ?)", horizons.main.session.timer.tick_next_id, horizons.main.session.world.player.getId(), horizons.util.encode(command))
		command(issuer = horizons.main.session.world.player)

	def load(self, db):
		self.commands = []
		for tick, issuer, data in db("SELECT tick, issuer, data from command"):
			self.commands.append((int(tick), horizons.main.session.world.player, decode(data))) #TODO: just until we have correct player saving
			#self.commands.append((int(tick), WorldObject.get_object_by_id(issuer), decode(data)))
		if len(self.commands) > 0:
			horizons.main.session.timer.add_call(self.tick)

	def tick(self, tick):
		remove = []
		for cmd in self.commands:
			if tick == cmd[0]:
				cmd[2](issuer = cmd[1])
				remove.append(cmd)
		for cmd in remove:
			self.commands.remove(cmd)
		if len(self.commands) == 0:
			horizons.main.session.timer.remove_call(self.tick)

	def end(self):
		self.commands = None
		super(SPManager, self).end()

class MPManager(LivingObject):
	COMMAND_RATE = 1
	def __init__(self):
		"""Initialize the Multiplayer Manager"""
		super(MPManager, self).__init__()
		horizons.timer.add_test(self.can_tick)
		horizons.timer.add_call(self.tick)
		self.commands = []
		self.packets = {}

	def end(self):
		self.commands = None
		self.packets = None
		super(MPManager, self).end()

	def tick(self, tick):
		"""Executes a tick
		@param tick: the
		"""
		if tick % self.__class__.COMMAND_RATE == 0:
			if self.packets.has_key(tick):
				self.packets[tick] = {}
			self.packets[tick][horizons.main.session.players[0]] = TickPacket(tick, self.commands)
			self.commands = []
			if self.packets.has_key(tick - 2):
				for p in horizons.main.session.players[(tick - 2) % len(horizons.main.session.players):] + horizons.main.session.players[:((tick - 2) % len(horizons.main.session.players)) - 1]:
					for c in self.packets[tick - 2][p].commands:
						c(issuer = p)

	def can_tick(self, tick):
		"""
		@param tick:
		"""
		return horizons.timer.TEST_PASS if ((tick % self.__class__.COMMAND_RATE != 0) or (not self.packets.has_key(tick - 2)) or (len(self.packets[tick - 2]) == len(horizons.main.session.player))) else horizons.timer.TEST_RETRY_KEEP_NEXT_TICK_TIME

	def execute(self, command):
		"""Executes a command
		@param command: Command the command to be executed
		"""
		self.commands.append(command)
