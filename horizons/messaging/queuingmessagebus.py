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

from collections import defaultdict, deque
from typing import Any

from horizons.messaging.messagebus import MessageBus


class QueuingMessageBus(MessageBus):
	"""The QueuingMessageBus class is used to send Message instances from a sender to
	one or multiple recipients, with the additional property that messages will
	be saved to a queue if no callback is subscribed at the time they are sent."""

	def __init__(self) -> None:
		MessageBus.__init__(self)
		# Queue up messages if there is no registered subscriber
		self.message_queue: defaultdict[type[Any], deque[Any]] = defaultdict(deque)

	def subscribe_globally(self, messagetype: type[Any], callback: Any) -> None:
		MessageBus.subscribe_globally(self, messagetype, callback)

		while self.message_queue[messagetype]:
			self.broadcast(self.message_queue[messagetype].popleft())

	def subscribe_locally(self, messagetype: type[Any], instance: Any, callback: Any) -> None:
		MessageBus.subscribe_locally(self, messagetype, instance, callback)

		# Iterate over a list copy of the queue to avoid RuntimeError when removing items
		for message in list(self.message_queue[messagetype]):
			if (type(message), message.sender) == (messagetype, instance):
				self.broadcast(message)
				self.message_queue[messagetype].remove(message)

	def broadcast(self, message: Any) -> None:
		messagetype = message.__class__
		pair = (messagetype, message.sender)

		# check if the message will go anywhere, if not, then queue it
		if not len(self.global_receivers[messagetype]) and not len(self.local_receivers[pair]):
			self.message_queue[messagetype].append(message)
		else:
			MessageBus.broadcast(self, message)

	def clear(self, messagetype: type[Any]) -> None:
		self.message_queue[messagetype].clear()

	def queue_len(self, messagetype: type[Any]) -> int:
		return len(self.message_queue[messagetype])

	def reset(self) -> None:
		self.message_queue.clear()
		super().reset()
