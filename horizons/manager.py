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

import operator
import logging
import itertools

from horizons.timer import Timer
from horizons.scheduler import Scheduler
from horizons.util import WorldObject
from horizons.util.living import LivingObject
from horizons.command.building import Build
from horizons.network import CommandError, packets

class SPManager(LivingObject):
	"""The manager class takes care of command issuing to the timermanager, sends tick-packets
	over the network, and syncronisation of network games."""

	def __init__(self, session):
		super(SPManager, self).__init__()
		self.session = session
		self.commands = []

	def execute(self, command, local=False):
		"""Executes a command
		@param command: Command the command to be executed
		@param local: Whether to only execute command here (doesn't make sense in singleplayer
		"""
		# if we are in demo playback mode, every incoming command has to be thrown away.
		if self.commands:
			return
		ret = command(issuer = self.session.world.player) # actually execute the command
		# some commands might have a return value, so forward it
		return ret

	def load(self, db):
		pass

	def end(self):
		self.commands = None
		super(SPManager, self).end()

class MPManager(LivingObject):
	"""Handler for commands.
	Initiates sending commands over the network for multiplayer games and their correct
	execution time and is also responsible for handling lags"""
	log = logging.getLogger("mpmanager")
	command_log = logging.getLogger("mpmanager.commands") # command executions
	EXECUTIONDELAY = 4
	HASHDELAY = 4
	HASH_EVAL_DISTANCE = 2 # interval, check hash every nth tick

	def __init__(self, session, networkinterface):
		"""Initialize the Multiplayer Manager"""
		super(MPManager, self).__init__()
		self.session = session
		self.networkinterface = networkinterface
		self.commandsmanager = MPCommandsManager(self)
		self.localcommandsmanager = MPCommandsManager(self)
		self.checkuphashmanager = MPCheckupHashManager(self)
		self.gamecommands = [] # commands from the local user, that will be part of next CommandPacket
		self.localcommands = [] # (only local) commands from the local user (e.g. sounds only this user should hear)

		self.session.timer.add_test(self.can_tick)
		self.session.timer.add_call(self.tick)

		self.session.timer.add_test(self.can_hash_value_check)
		self.session.timer.add_call(self.hash_value_check)

		self._last_local_commands_send_tick = -1 # last tick, where local commands got sent

	def end(self):
		pass

	def can_tick(self, tick):
		"""Checks if we can execute this tick via return value"""
		# get new packages fom networkinteface
		packets_received = None
		try:
			packets_received = self.networkinterface.receive_all()
		except CommandError:
			return Timer.TEST_SKIP

		for packet in packets_received:
			if isinstance(packet, CommandPacket):
				self.log.debug("Got command packet from " + str(packet.player_id) + " for tick " + str(packet.tick))
				self.commandsmanager.add_packet(packet)
			elif isinstance(packet, CheckupHashPacket):
				self.log.debug("Got checkuphash packet from " + str(packet.player_id) + " for tick " + str(packet.tick))
				self.checkuphashmanager.add_packet(packet)
			else:
				self.log.warn("invalid packet: "+str(packet))

		# send out new commands
		# check if we already sent commands for this tick (only 1 packet per tick is allowed,
		# in case of lags this code would be executed multiple times for the same tick)
		if self._last_local_commands_send_tick < tick:
			self._last_local_commands_send_tick = tick
			commandpacket = CommandPacket(self.calculate_execution_tick(tick),
					self.session.world.player.worldid, self.gamecommands)
			self.gamecommands = []
			self.commandsmanager.add_packet(commandpacket)
			self.log.debug("sending command for tick %d" % (commandpacket.tick))
			self.networkinterface.send_to_all_clients(commandpacket)

			self.localcommandsmanager.add_packet(CommandPacket(self.calculate_execution_tick(tick),
					self.session.world.player.worldid, self.localcommands))
			self.localcommands = []

			# check if we have to evaluate a hash value
			if self.calculate_hash_tick(tick) % self.HASH_EVAL_DISTANCE == 0:
				hash_value = self.session.world.get_checkup_hash()
				#self.log.debug("MPManager: Checkup hash for tick %s is %s", tick, hash_value)
				checkuphashpacket = CheckupHashPacket(self.calculate_hash_tick(tick),
			                              self.session.world.player.worldid, hash_value)
				self.checkuphashmanager.add_packet(checkuphashpacket)
				self.log.debug("sending checkuphash for tick %d" % (checkuphashpacket.tick))
				self.networkinterface.send_to_all_clients(checkuphashpacket)

		# decide if tick can be calculated
		# in the first few ticks, no data is available
		if self.commandsmanager.is_tick_ready(tick) or tick < (Scheduler.FIRST_TICK_ID + self.EXECUTIONDELAY):
			#self.log.debug("MPManager: check tick %s ready: yes", tick)
			return Timer.TEST_PASS
		else:
			self.log.debug("MPManager: check tick %s ready: no", tick)
			return Timer.TEST_SKIP

	def tick(self, tick):
		"""Do the tick (execute all commands for this tick)
		This code may only be reached if we are allowed to tick now (@see can_tick)"""
		# calculate command packets for this tick
		command_packets = self.commandsmanager.get_packets_for_tick(tick)
		command_packets.extend(self.localcommandsmanager.get_packets_for_tick(tick))
		# sort by player, so that the packets get executed in the same order in every client
		# (packets are already in a special order within the packets, so no further sorting is necessary)
		command_packets.sort(key=operator.attrgetter('player_id'))

		for command_packet in command_packets:
			for command in command_packet.commandlist:
				self.log.debug("MPManager: calling command (tick %s): %s", tick, command)
				self.command_log.debug("MPManagerCommand: (tick %s): %s", tick, command)
				command(WorldObject.get_object_by_id(command_packet.player_id))

	def can_hash_value_check(self, tick):
		if self.checkuphashmanager.is_tick_ready(tick) or tick < self.HASHDELAY:
			return Timer.TEST_PASS
		else:
			return Timer.TEST_SKIP

	def hash_value_check(self, tick):
		if tick % self.HASH_EVAL_DISTANCE == 0:
			if self.checkuphashmanager.are_checkup_hash_values_equal(tick, self.hash_value_diff) == False:
				self.log.error("MPManager: Hash values generated in tick %s are not equal" % str(tick - self.HASHDELAY))
				# if this is reached, we are screwed. Something went wrong in the simulation,
				# but we don't know what. Stop the game.
				msg = _("The games have run out of sync. This indicates an unknown internal error, the game cannot continue.") + "\n" + \
				  _("We are very sorry and hope to have this bug fixed in a future version.")
				self.session.gui._on_error(msg, fatal=True)
			else:
				#self.log.debug("MPManager: Hash values are equal")
				pass

	def hash_value_diff(self, player1, hash1, player2, hash2):
		"""Called when a divergence has been detected"""
		self.log.error("MPManager: Hash diff:\n%s hash1: %s\n%s hash2: %s" % (player1, hash1, player2, hash2))
		self.log.error("------------------")
		self.log.error("Differences:")
		if len(hash1) != len(hash2):
			self.log.error("Different length")
		items1 = sorted(hash1.iteritems())
		items2 = sorted(hash2.iteritems())
		for i in xrange(min(len(hash1), len(hash2))):
			if (items1[i] != items2[i]):
				self.log.error(str(i)+": "+str(items1[i]))
				self.log.error(str(i)+": "+str(items2[i]))
		self.log.error("------------------")

	def calculate_execution_tick(self, tick):
		return tick + self.EXECUTIONDELAY

	def calculate_hash_tick(self, tick):
		return tick + self.HASHDELAY

	def execute(self, command, local=False):
		"""Receive commands to be executed from local player
		@param command: Command instance
		@param local: commands that don't need to be sent over the wire"""
		self.log.debug('MPManager: adding command (next tick: ' + str(self.session.timer.tick_next_id) + ')'+str(command))
		if local:
			self.localcommands.append(command)
		else:
			self.gamecommands.append(command)

	def get_player_count(self):
		return len(self.session.world.players)

	def get_builds_in_construction(self):
		"""Returns all Build-commands by the local player, that are executed in the next ticks"""
		commandpackets = self.commandsmanager.get_packets_from_player(self.session.world.player.worldid)

		# check commands already sent
		l1 = itertools.chain.from_iterable( (pkg.commandlist for pkg in commandpackets) )
		# and the ones that haven't been sent yet (this are of course only commands by the local player)
		commandlist = itertools.chain(l1, self.gamecommands)

		return filter(lambda x: isinstance(x, Build), commandlist)

	def load(self, db):
		"""Execute outstanding commands, loaded from db.
		Currently not supported for MP"""
		# NOTE: it is supported now, and such outstanding commands are dropped right now
		pass

# Packagemanagers storing Packages for later use
################################################

class MPPacketmanager(object):
	log =  logging.getLogger("mpmanager")
	def __init__(self, mpmanager):
		self.mpmanager = mpmanager
		self.command_packet_list = []

	def is_tick_ready(self, tick):
		"""Check if packets from all players have arrived (necessary for tick to begin)"""
		ready = len(self.get_packets_for_tick(tick, remove_returned_commands=False)) == self.mpmanager.get_player_count()
		if not ready:
			self.log.debug("tick not ready, packets: " + str(list(str(x) for x in self.get_packets_for_tick(tick, remove_returned_commands=False))))
		return ready

	def get_packets_for_tick(self, tick, remove_returned_commands=True):
		"""Returns packets that are to be executed at a certain tick"""
		command_packets = filter(lambda x: x.tick==tick, self.command_packet_list)
		if remove_returned_commands:
			self.command_packet_list = filter(lambda x: x.tick!=tick, self.command_packet_list)
		return command_packets

	def get_packets_from_player(self, player_id):
		"""
		Returns all command this player has issued, that are not yet executed
		@param player_id: worldid of player
		"""
		return filter(lambda x: x.player_id==player_id, self.command_packet_list)

	def add_packet(self, command_packet):
		"""Receive a packet"""
		self.command_packet_list.append(command_packet)

class MPCommandsManager(MPPacketmanager):
	pass

class MPCheckupHashManager(MPPacketmanager):
	def is_tick_ready(self, tick):
		# we only check hash for every HASH_EVAL_DISTANCE tick
		# if the current tick isn't checked we don't need any packets and are always ready
		if tick % self.mpmanager.HASH_EVAL_DISTANCE != 0:
			return True
		return super(MPCheckupHashManager, self).is_tick_ready(tick)

	def are_checkup_hash_values_equal(self, tick, cb_diff=None):
		"""
		@param packages for tick
		@param cb_diff: called in case hashes differ
		@return False if they are not equal
		"""
		pkges = self.get_packets_for_tick(tick)
		for pkg in pkges[1:]:
			if pkges[0].checkup_hash != pkg.checkup_hash:
				if cb_diff is not None:
					localplayerid = self.mpmanager.session.world.player.worldid
					cb_diff("local" if pkges[0].player_id==localplayerid else "pl#%02d" % (pkges[0].player_id),
						pkges[0].checkup_hash,
						"local" if pkg.player_id==localplayerid else "pl#%02d" % (pkg.player_id),
						pkg.checkup_hash)
				return False
		return True

# Packages transmitted over the network
#######################################

class MPPacket(object):
	"""Packet to be sent from every player to every player"""
	def __init__(self, tick, player_id):
		"""
		@param player_id: worldid of player
		"""
		self.tick = tick
		self.player_id = player_id

	@classmethod
	def allow_network(self, klass):
		"""
		NOTE: this is a security related method and may lead to
		execution of arbritary code if used in a wrong way
		see documentation inside horizons.network.packets.SafeUnpickler
		"""
		packets.SafeUnpickler.add('server', klass)

	def __str__(self):
		return "packet " + str(self.__class__)  + " from player " + str(WorldObject.get_object_by_id(self.player_id)) + " for tick " + str(self.tick)

class CommandPacket(MPPacket):
	"""Packet to be sent from every player to every player every tick.
	Contains list of packets to be executed as well as the designated execution time.
	Also acts as ping (game will stop if a packet for a certain tick hasn't arrived)"""
	def __init__(self, tick, player_id, commandlist):
		super(CommandPacket, self).__init__(tick, player_id)
		self.commandlist = commandlist

MPPacket.allow_network(CommandPacket)

class CheckupHashPacket(MPPacket):
	def __init__(self, tick, player_id, checkup_hash):
		super(CheckupHashPacket, self).__init__(tick, player_id)
		self.checkup_hash = checkup_hash

MPPacket.allow_network(CheckupHashPacket)
