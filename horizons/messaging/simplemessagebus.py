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

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class SimpleMessageBus:
	"""Manages registration and calling of callbacks when events (strings) occur.

	Example:

		bus = SimpleMessageBus(('foo', 'bar'))
		bus.subscribe('foo', cb)

		bus.broadcast('foo')  # cb will be called
	"""

	def __init__(self, message_types: tuple[str, ...]) -> None:
		self._message_types = message_types
		self._callbacks: defaultdict[str, list[Callable[..., Any]]] = defaultdict(list)

	def subscribe(self, type: str, callback: Callable[..., Any]) -> None:
		if type not in self._message_types:
			raise TypeError("Unsupported type")
		if callback in self._callbacks[type]:
			raise Exception(f"Callback {callback} already subscribed to {type}")

		self._callbacks[type].append(callback)

	def unsubscribe(self, type: str, callback: Callable[..., Any]) -> None:
		self._callbacks[type].remove(callback)

	def discard(self, type: str, callback: Callable[..., Any]) -> None:
		if callback in self._callbacks[type]:
			self._callbacks[type].remove(callback)

	def broadcast(self, type: str, *args: Any, **kwargs: Any) -> None:
		if type not in self._message_types:
			return

		for cb in self._callbacks[type]:
			cb(*args, **kwargs)

	def is_message_type_known(self, type: str) -> bool:
		return type in self._message_types
