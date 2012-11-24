import datetime
import logging

from horizons import network
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
	"""
	"""
	log = logging.getLogger("network")

	def __init__(self, process_async_packet, server_address, client_address=None):
		try:
			if client_address:
				client_address = enet.Address(*client_address)
			else:
				client_address = None

			self.host = enet.Host(client_address, MAX_PEERS, 0, 0, 0)
		except (IOError, MemoryError):
			# these exceptions do not provide any information.
			raise network.NetworkException("Unable to create network structure."
			                               "Maybe invalid or irresolvable client address.")
		
		self.server_address = enet.Address(*server_address)
		self.server_peer = None
		self.packetqueue = []
		self.process_async_packet = process_async_packet

	# Connection setup / keepalive

	@property
	def is_connected(self):
		return self.server_peer is not None

	def connect(self):
		"""
		"""
		if self.is_connected:
			raise network.AlreadyConnected("We are already connected to a server")

		self.log.debug("[CONNECT] to server %s" % (self.server_address))
		try:
			self.server_peer = self.host.connect(self.server_address, 1, SERVER_PROTOCOL)
		except (IOError, MemoryError):
			raise network.NetworkException("Unable to connect to server."
			                               "Maybe invalid or irresolvable server address.")

		event = self.host.service(SERVER_TIMEOUT)
		if event.type != enet.EVENT_TYPE_CONNECT:
			self.reset()
			raise network.UnableToConnect("Unable to connect to server")

	def disconnect(self, server_may_disconnect=False, later=False):
		"""End connection to server.

		This function should _never_ throw an exception.
		"""
		if not self.is_connected:
			return

		if self.server_peer.state == enet.PEER_STATE_DISCONNECTED:
			self.reset()
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
				if later:
					self.server_peer.disconnect_later()
				else:
					self.server_peer.disconnect()
				while True:
					event = self.host.service(SERVER_TIMEOUT)
					if event.type == enet.EVENT_TYPE_DISCONNECT:
						break
					elif event.type == enet.EVENT_TYPE_NONE:
						raise IOError("No packet from server")
		except IOError:
			self.log.debug("[DISCONNECT] Error while disconnecting from server. Maybe server isn't answering any more")

		self.reset()
		self.log.debug("[DISCONNECT] done")

	def reset(self):
		"""
		"""
		self.log.debug("[RESET]")
		if self.is_connected:
			self.server_peer.reset()
			self.server_peer = None
		self.flush()

	def flush(self):
		"""
		"""
		self.host.flush()

	def ping(self):
		"""
		enet doesn't need to send pings. instead we need to call enet_host_service
		on a regular basis. we call this ping and save received events
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

	def send_packet(self, packet, channelid=0):
		"""Send a packet to the server"""
		if self.server_peer is None:
			raise network.NotConnected()

		packet = enet.Packet(packet.serialize(), enet.PACKET_FLAG_RELIABLE)
		self.server_peer.send(channelid, packet)

	def _receive_event(self, timeout=SERVER_TIMEOUT):
		"""wait for event from network"""
		if self.server_peer is None:
			raise network.NotConnected()

		event = self.host.service(timeout)
		if event.type == enet.EVENT_TYPE_NONE:
			return None
		elif event.type == enet.EVENT_TYPE_DISCONNECT:
			self.reset()
			self.log.warning("Unexpected disconnect from %s" % (event.peer.address))
			raise network.CommandError("Unexpected disconnect from %s" % (event.peer.address))
		elif event.type == enet.EVENT_TYPE_CONNECT:
			self.reset()
			self.log.warning("Unexpected connection from %s" % (event.peer.address))
			raise network.CommandError("Unexpected connection from %s" % (event.peer.address))

		return event

	def _receive(self, timeout=SERVER_TIMEOUT):
		"""receives event from network and returns the unpacked packet"""
		event = self._receive_event(timeout)
		if event is None or event.type != enet.EVENT_TYPE_RECEIVE:
			return None

		packet = None
		try:
			packet = packets.unserialize(event.packet.data)
		except Exception as e:
			self.log.error("Unknown packet from %s!" % (event.peer.address))
			errstr = "Pickle/Security: %s" % (e)
			print "[FATAL] %s" % (errstr) # print that even when no logger is enabled!
			self.log.error("[FATAL] %s" % (errstr))
			self.disconnect()
			raise network.FatalError(errstr)

		if isinstance(packet, packets.cmd_error):
			# handle special errors here
			# FIXME: it's better to pass that to the interface,
			# but our ui error handler currently can't handle that

			# the game got terminated by the client
			"""
			# TODO
			if packet.type == ErrorType.TerminateGame:
				game = self.game
				# this will destroy self.game
				self.leavegame(stealth=True)
				self.call_callbacks("lobbygame_terminate", game, packet.errorstr)
				return None
			"""
			raise network.CommandError(packet.errorstr)
		elif isinstance(packet, packets.cmd_fatalerror):
			self.log.error("[FATAL] Network message: %s" % (packet.errorstr))
			self.disconnect(True)
			raise network.FatalError(packet.errorstr)

		return [event.peer, packet]

	def receive_packet(self, packet_type=None, timeout=SERVER_TIMEOUT):
		"""Return the first received packet.
		
		If packet_type is given, only a packet of that type will be returned.
		"""

		def assert_type(packet):
			if packet_type is None:
				return packet
			if packet is None:
				raise network.FatalError("No reply from server")
			elif not isinstance(packet[1], packet_type):
				raise network.CommandError("Unexpected packet")
			return packet

		if self.packetqueue:
			if packet_type is None:
				return self.packetqueue.pop(0)

			for p in self.packetqueue:
				if not isinstance(p[1], packet_type):
					continue
				self.packetqueue.remove(p)
				return assert_type(p)

		if packet_type is None:
			return self._receive(timeout)

		start = datetime.datetime.now()
		timeleft = timeout
		while timeleft > 0:
			packet = self._receive(timeleft)
			if packet is None:
				return None
			if isinstance(packet[1], packet_type):
				return assert_type(packet)
			if not self.process_async_packet(packet):
				self.packetqueue.append(packet)
			timeleft -= (datetime.datetime.now() - start).seconds
