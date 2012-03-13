# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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

from collections import defaultdict


class MessageBus(object):
	"""The MessageBus class is used to send Message instances from a sender to
	one or multiple recipients."""

	def __init__(self):
		# Register {MessageType: [list of receiver callbacks]}
		self.global_receivers = defaultdict(list)
		# Register for messages from a specific object
		# {(MessageType, instance): [list of receiver callbacks]}
		self.local_receivers = defaultdict(list)

	def subscribe_globally(self, messagetype, callback):
		"""Register for a certain message type.
		@param callback: Callback methode, needs to take 1 parameter: the message"""
		self.global_receivers[messagetype].append(callback)

	def subscribe_locally(self, messagetype, instance, callback):
		"""Register for a certain message type from a specific instance.
		@param callback: Callback methode, needs to take 1 parameter: the message"""
		pair = (messagetype, instance)
		self.local_receivers[pair].append(callback)

	def unsubscribe_globally(self, messagetype, callback):
		assert callback in self.global_receivers[messagetype]
		self.global_receivers[messagetype].remove(callback)

	def unsubscribe_locally(self, messagetype, instance, callback):
		pair = (messagetype, instance)
		assert callback in self.local_receivers[pair]
		self.local_receivers[pair].remove(callback)

	def discard_globally(self, messagetype, callback):
		if callback in self.global_receivers[messagetype]:
			self.unsubscribe_globally(messagetype, callback)

	def broadcast(self, message):
		"""Send a message to the bus and broadcast it to all recipients"""
		messagetype = message.__class__
		for callback in self.global_receivers[messagetype]:
			# Execute the callback
			callback(message)

		pair = (messagetype, message.sender)
		for callback in self.local_receivers[pair]:
			# Execute the callback
			callback(message)

