# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

import logging
from collections import defaultdict

from horizons.messaging.messagebus import MessageBus
from horizons.util.python.singleton import Singleton


class SimpleMessageBus(object):
	"""Manages registration and calling of callbacks when events (strings) occur.

	Example:

		bus = SimpleMessageBus(('foo', 'bar'))
		bus.subscribe('foo', cb)

		bus.broadcast('foo')  # cb will be called
	"""

	def __init__(self, message_types):
		self._message_types = message_types
		self._callbacks = defaultdict(list)

	def subscribe(self, type, callback):
		if type not in self._message_types:
			raise TypeError("Unsupported type")
		if callback in self._callbacks[type]:
			raise Exception("Callback %s already subscribed to %s" % (callback, type))

		self._callbacks[type].append(callback)

	def unsubscribe(self, type, callback):
		self._callbacks[type].remove(callback)

	def discard(self, type, callback):
		if callback in self._callbacks[type]:
			self._callbacks[type].remove(callback)

	def broadcast(self, type, *args, **kwargs):
		if type not in self._message_types:
			return

		for cb in self._callbacks[type]:
			cb(*args, **kwargs)
