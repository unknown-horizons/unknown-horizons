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

from unittest import mock

import pytest

from horizons.messaging import Message, MessageBus
from horizons.messaging.queuingmessagebus import QueuingMessageBus


class ExampleMessage(Message):
	pass


@pytest.fixture
def bus():
    MessageBus().reset()
    instance = MessageBus()
    yield instance
    MessageBus().reset()


@pytest.fixture
def qbus():
    QueuingMessageBus().reset()
    instance = QueuingMessageBus()
    yield instance
    QueuingMessageBus().reset()


def test_reset_removes_all_subscriptions(bus):
	cb = mock.Mock()

	bus.subscribe_globally(ExampleMessage, cb)

	bus.reset()

	new_bus = MessageBus()

	assert new_bus is not bus

	new_bus.broadcast(ExampleMessage(object()))

	cb.assert_not_called()


def test_duplicate_global_subscriptions_receive_multiple_notifications(bus):
	cb = mock.Mock()

	bus.subscribe_globally(ExampleMessage, cb)
	bus.subscribe_globally(ExampleMessage, cb)

	bus.broadcast(ExampleMessage(object()))

	assert cb.call_count == 2


def test_unsubscribe_removes_one_duplicate_registration(bus):
	cb = mock.Mock()

	bus.subscribe_globally(ExampleMessage, cb)
	bus.subscribe_globally(ExampleMessage, cb)

	bus.unsubscribe_globally(ExampleMessage, cb)
	bus.broadcast(ExampleMessage(object()))

	cb.assert_called_once()


def test_global_and_local_subscription_both_receive_message(bus):
	cb = mock.Mock()
	sender = object()

	bus.subscribe_globally(ExampleMessage, cb)
	bus.subscribe_locally(ExampleMessage, sender, cb)

	bus.broadcast(ExampleMessage(sender))

	assert cb.call_count == 2


def test_qbus_queues_message_when_no_subscriber(qbus):
	sender = object()
	msg = ExampleMessage(sender)

	# Broadcast before any subscription
	qbus.broadcast(msg)

	assert qbus.queue_len(ExampleMessage) == 1


def test_qbus_delivers_queued_messages_on_global_subscription(qbus):
	cb = mock.Mock()
	msg = ExampleMessage(object())

	qbus.broadcast(msg)

	# Subscribing now should trigger delivery of queued messages
	qbus.subscribe_globally(ExampleMessage, cb)

	cb.assert_called_once_with(msg)
	assert qbus.queue_len(ExampleMessage) == 0


def test_qbus_delivers_only_matching_sender_on_local_subscription(qbus):
	cb = mock.Mock()
	sender_a = object()
	sender_b = object()

	msg_a = ExampleMessage(sender_a)
	msg_b = ExampleMessage(sender_b)

	qbus.broadcast(msg_a)
	qbus.broadcast(msg_b)

	# Subscribe only for sender_a
	qbus.subscribe_locally(ExampleMessage, sender_a, cb)

	cb.assert_called_once_with(msg_a)
	# msg_b should still be in the queue because sender_b wasn't subscribed
	assert qbus.queue_len(ExampleMessage) == 1


def test_qbus_clear_empties_specific_queue(qbus):
	qbus.broadcast(ExampleMessage(object()))
	assert qbus.queue_len(ExampleMessage) == 1

	qbus.clear(ExampleMessage)
	assert qbus.queue_len(ExampleMessage) == 0


def test_qbus_reset_clears_all_queues(qbus):
	qbus.broadcast(ExampleMessage(object()))
	assert qbus.queue_len(ExampleMessage) == 1

	qbus.reset()
	assert qbus.queue_len(ExampleMessage) == 0


def test_falsey_sender_is_local_subscription(bus):
	"""Ensure that senders who are false-y (0, False, "") are
	treated as valid local senders and not as global subscriptions.
	"""
	cb = mock.Mock()

	bus.subscribe_locally(ExampleMessage, 0, cb)
	bus.broadcast(ExampleMessage(0))
	assert cb.call_count == 1

	bus.broadcast(ExampleMessage(1))
	assert cb.call_count == 1

	bus.unsubscribe_locally(ExampleMessage, 0, cb)
