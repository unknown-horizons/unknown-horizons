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

from __future__ import print_function

import logging
import time

from horizons import network
from horizons.i18n import gettext as T
from horizons.network import enet, packets

# maximal peers enet should handle
MAX_PEERS = 1

# current server/client protocol the client understands
# increment that after incompatible protocol changes
SERVER_PROTOCOL = 1

# time in ms the client will wait for a packet
# on error client may wait twice that time
SERVER_TIMEOUT = 5000


class Connection(object):
	"""Low-level interface to enet.

	Handles sending and receiving packets.
	"""
	log = logging.getLogger("network")

	def __init__(self, process_async_packet, server_address, client_address=None):
		try:
			if client_address:
				client_address = enet.Address(*client_address)

			self.host = enet.Host(client_address, MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError):
			# these exceptions do not provide any information.
			raise network.NetworkException("Unable to create network structure."
			                               "Maybe invalid or irresolvable client address.")

		self.server_address_parameters = server_address
		self.server_address = None
		self.server_peer = None
		self.packetqueue = []
		self.process_async_packet = process_async_packet

	# Connection setup / keepalive

	@property
	def is_connected(self):
		return self.server_peer is not None

	def connect(self):
		"""Connect to master server.

		After this, you can use `send_packet` and `receive_packet` to communicate
		with the server.
		"""
		if self.is_connected:
			raise network.AlreadyConnected("We are already connected to a server")

		self.log.debug("[CONNECT] to server {}".format(self.server_address))
		try:
			if self.server_address is None:
				# can only construct address now, as it resolves the target and requires internet connection
				self.server_address = enet.Address(*self.server_address_parameters)
			self.server_peer = self.host.connect(self.server_address, 1, SERVER_PROTOCOL)
		except (IOError, MemoryError):
			raise network.NetworkException(T("Unable to connect to server.") + u" " +
			                               T("Maybe invalid or irresolvable server address."))

		event = self.host.service(SERVER_TIMEOUT)
		if event.type != enet.EVENT_TYPE_CONNECT:
			self._reset()
			raise network.UnableToConnect(T("Unable to connect to server."))

	def disconnect(self, server_may_disconnect=False):
		"""End connection to master server.

		This function should _never_ throw an exception.
		"""
		if not self.is_connected:
			return

		if self.server_peer.state == enet.PEER_STATE_DISCONNECTED:
			self._reset()
			return

		try:
			# wait for a disconnect event or empty event
			if server_may_disconnect:
				while True:
					event = self.host.service(SERVER_TIMEOUT)
					if event.type == enet.EVENT_TYPE_DISCONNECT:
						break
					elif event.type == enet.EVENT_TYPE_NONE:
						break

			# disconnect from server if we're still connected
			if self.server_peer.state != enet.PEER_STATE_DISCONNECTED:
				self.server_peer.disconnect()
				while True:
					event = self.host.service(SERVER_TIMEOUT)
					if event.type == enet.EVENT_TYPE_DISCONNECT:
						break
					elif event.type == enet.EVENT_TYPE_NONE:
						raise IOError("No packet from server")
		except IOError:
			self.log.debug("[DISCONNECT] Error while disconnecting from server. Maybe server isn't answering any more")

		self._reset()
		self.log.debug("[DISCONNECT] done")

	def ping(self):
		"""Handle incoming packets.

		Enet doesn't need to send pings. Call this regularly. Incoming packets can be
		handled by process_async_packet, otherwise will be added to a queue.
		"""
		if not self.is_connected:
			raise network.NotConnected()

		packet = self._receive(0)
		if packet is not None:
			if not self.process_async_packet(packet):
				self.packetqueue.append(packet)
			return True

		return False

	# Send / Receive

	def send_packet(self, packet):
		"""Send a packet to the server.

		packet has to be a subclass of `horizons.network.packets.packet`.
		"""
		if self.server_peer is None:
			raise network.NotConnected()

		packet = enet.Packet(packet.serialize(), enet.PACKET_FLAG_RELIABLE)
		self.server_peer.send(0, packet)

	def receive_packet(self, packet_type=None, timeout=SERVER_TIMEOUT):
		"""Return the first received packet.

		If packet_type is given, only a packet of that type will be returned.
		"""

		if self.packetqueue:
			if packet_type is None:
				return self.packetqueue.pop(0)

			for p in self.packetqueue:
				if not isinstance(p[1], packet_type):
					continue
				self.packetqueue.remove(p)
				return p

		if packet_type is None:
			return self._receive(timeout)

		start = time.time()
		timeleft = timeout
		while timeleft > 0:
			packet = self._receive(timeleft)
			# packet type is None -> return whatever we received
			if packet_type is None:
				return packet
			# otherwise only process non-None packets
			if packet is not None:
				if isinstance(packet[1], packet_type):
					return packet
				if not self.process_async_packet(packet):
					self.packetqueue.append(packet)
			timeleft -= time.time() - start
		raise network.FatalError("No reply from server")

	def _receive_event(self, timeout=SERVER_TIMEOUT):
		"""Receives next event of type NONE or RECEIVE."""
		if self.server_peer is None:
			raise network.NotConnected()
		try:
			event = self.host.service(timeout)

			if event.type == enet.EVENT_TYPE_NONE:
				return None
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				self._reset()
				self.log.warning("Unexpected disconnect from %s", event.peer.address)
				raise network.CommandError("Unexpected disconnect from {}".format(event.peer.address))
			elif event.type == enet.EVENT_TYPE_CONNECT:
				self._reset()
				self.log.warning("Unexpected connection from %s", event.peer.address)
				raise network.CommandError("Unexpected connection from {}".format(event.peer.address))

			return event
		except IOError as e:
			raise network.FatalError(e)

	def _receive(self, timeout=SERVER_TIMEOUT):
		"""Receive event and return unpacked packet."""
		try:
			event = self._receive_event(timeout)
			if event is None or event.type != enet.EVENT_TYPE_RECEIVE:
				return None

			packet = packets.unserialize(event.packet.data)
		except Exception as e:
			try:
				event
			except NameError:
				pass
			else:
				self.log.error("Unknown packet from %s!", event.peer.address)
			errstr = "Pickle/Security: {}".format(e)
			print("[FATAL] {}".format(errstr)) # print that even when no logger is enabled!
			self.log.error("[FATAL] %s", errstr)
			self.disconnect()
			raise network.FatalError(errstr)

		if isinstance(packet, packets.cmd_error):
			# handle special errors here
			# the game got terminated by the client
			raise network.CommandError(packet.errorstr, type=packet.type)
		elif isinstance(packet, packets.cmd_fatalerror):
			self.log.error("[FATAL] Network message: %s", packet.errorstr)
			self.disconnect(server_may_disconnect=True)
			raise network.FatalError(packet.errorstr)

		return [event.peer, packet]

	def _reset(self):
		self.log.debug("[RESET]")
		if self.is_connected:
			self.server_peer.reset()
			self.server_peer = None
		self.host.flush()
