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

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from horizons.util.python.singleton import Singleton

BusCallback = Callable[[Any], None]


class MessageBus(metaclass=Singleton):
    """The MessageBus class is used to send Message instances from a sender to
    one or multiple recipients."""

    log = logging.getLogger("messaging.messagebus")

    def __init__(self) -> None:
        # Register for a specific messagetype
        self.global_receivers: defaultdict[
            type[Any], list[BusCallback]
        ] = defaultdict(list)
        # Register for messages from a specific object
        self.local_receivers: defaultdict[
            tuple[type[Any], Any], list[BusCallback]
        ] = defaultdict(list)

    def subscribe_globally(
        self, messagetype: type[Any], callback: BusCallback
    ) -> None:
        """Register for a certain message type."""
        self.global_receivers[messagetype].append(callback)

    def subscribe_locally(
        self,
        messagetype: type[Any],
        instance: Any,
        callback: BusCallback,
    ) -> None:
        """Register for a certain message type from a specific instance."""
        pair = (messagetype, instance)
        self.local_receivers[pair].append(callback)

    def unsubscribe_globally(
        self, messagetype: type[Any], callback: BusCallback
    ) -> None:
        assert callback in self.global_receivers[messagetype]
        self.global_receivers[messagetype].remove(callback)

    def unsubscribe_locally(
        self,
        messagetype: type[Any],
        instance: Any,
        callback: BusCallback,
    ) -> None:
        pair = (messagetype, instance)
        assert callback in self.local_receivers[pair]
        self.local_receivers[pair].remove(callback)

    def discard_globally(
        self, messagetype: type[Any], callback: BusCallback
    ) -> None:
        if callback in self.global_receivers[messagetype]:
            self.unsubscribe_globally(messagetype, callback)

    def discard_locally(
        self,
        messagetype: type[Any],
        instance: Any,
        callback: BusCallback,
    ) -> None:
        pair = (messagetype, instance)
        if pair in self.local_receivers and callback in self.local_receivers[pair]:
            self.unsubscribe_locally(messagetype, instance, callback)

    def broadcast(self, message: Any) -> None:
        """Send a message to the bus and broadcast it to all recipients."""
        messagetype = message.__class__
        for callback in self.global_receivers[messagetype]:
            # Execute the callback
            callback(message)

        pair = (messagetype, message.sender)
        for callback in self.local_receivers[pair]:
            callback(message)

    def reset(self) -> None:
        """Reset to initial state. Drops all subscriptions."""
        # there shouldn't be anything left now, warn if there is
        for messagetype, cb_list in self.global_receivers.items():
            if cb_list:
                self.log.debug(
                    f"MessageBus: leftover global receivers "
                    f"{[str(i) for i in cb_list]} for {messagetype}"
                )
        for messagetype, cb_list in self.local_receivers.items():
            if cb_list:
                self.log.debug(
                    f"MessageBus: leftover local receivers "
                    f"{[str(i) for i in cb_list]} for {messagetype}"
                )

        # suicide, next instance will be created on demand
        self.__class__.destroy_instance()
