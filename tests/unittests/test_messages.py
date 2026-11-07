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

from horizons.messaging import Message


class ExampleMessage(Message):
	pass


class FooMessage(Message):
	arguments = ('a', 'b', )


def test_message_sender_argument():
	sender = object()
	msg = Message(sender)
	assert msg.sender == sender


def test_message_additional_arguments():
	sender = object()
	msg = FooMessage(sender, 1, 2)
	assert msg.sender == sender
	assert msg.a == 1
	assert msg.b == 2


def test_wrong_arguments():
	with pytest.raises(Exception):
		FooMessage(None, 1)


def assert_called_once_with_message(cb, message_type, **arguments):
	"""
	Check whether mock `cb` was called with an instance of `message_type`
	and the given `arguments`.
	"""
	cb.assert_called_once()
	msg = cb.call_args[0][0]
	assert isinstance(msg, message_type)
	for name, value in arguments.items():
		assert getattr(msg, name) == value


def test_messagebus_global_subscribe():
	"""
	Test global (sender-independent) subscription to messages.
	"""
	cb = mock.Mock()
	sender = object()

	ExampleMessage.subscribe(cb)
	try:
		# Correct message type: callback is called.
		ExampleMessage.broadcast(sender)
		assert_called_once_with_message(cb, ExampleMessage, sender=sender)

		cb.reset_mock()

		# Wrong message type: callback is not called.
		Message.broadcast(sender)
		cb.assert_not_called()
	finally:
		ExampleMessage.discard(cb)


def test_messagebus_local_subscribe():
	"""
	Test local (sender-specific) subscription to messages.
	"""
	cb = mock.Mock()
	sender = object()

	ExampleMessage.subscribe(cb, sender=sender)
	try:
		# Correct message type and sender: callback is called.
		ExampleMessage.broadcast(sender)
		assert_called_once_with_message(cb, ExampleMessage, sender=sender)

		cb.reset_mock()

		# Correct message type, wrong sender: callback is not called.
		ExampleMessage.broadcast(1)
		cb.assert_not_called()

		# Wrong message type, correct sender: callback is not called.
		Message.broadcast(sender)
		cb.assert_not_called()
	finally:
		ExampleMessage.discard(cb, sender=sender)


def test_messagebus_unsubscribe():
	"""
	Test unsubscribe from global and local message subscriptions.
	"""
	cb = mock.Mock()
	sender = object()

	ExampleMessage.subscribe(cb)
	Message.subscribe(cb, sender=sender)
	try:
		# Broadcast the global and local messages.
		ExampleMessage.broadcast(sender)
		Message.broadcast(sender)
		assert cb.call_count == 2
		cb.reset_mock()

		# After unsubscribing globally, only the local message is received.
		ExampleMessage.unsubscribe(cb)
		ExampleMessage.broadcast(sender)
		Message.broadcast(sender)
		assert_called_once_with_message(cb, Message, sender=sender)
		cb.reset_mock()

		# After unsubscribing locally, no messages are received.
		Message.unsubscribe(cb, sender=sender)
		ExampleMessage.broadcast(sender)
		Message.broadcast(sender)
		cb.assert_not_called()
	finally:
		# discard() is safe for subscriptions that have already been removed.
		ExampleMessage.discard(cb)
		Message.discard(cb, sender=sender)


def test_discard_nonexistent_global_subscription():
	cb = mock.Mock()

	# Discarding a missing subscription must not raise or subscribe the callback.
	ExampleMessage.discard(cb)
	ExampleMessage.broadcast(object())

	cb.assert_not_called()


def test_discard_nonexistent_local_subscription():
	cb = mock.Mock()
	sender = object()

	ExampleMessage.discard(cb, sender=sender)
	ExampleMessage.broadcast(sender)

	cb.assert_not_called()


def test_unsubscribe_nonexistent_global_subscription():
	cb = mock.Mock()

	with pytest.raises(Exception):
		ExampleMessage.unsubscribe(cb)


def test_unsubscribe_nonexistent_local_subscription():
	cb = mock.Mock()
	sender = object()

	with pytest.raises(Exception):
		ExampleMessage.unsubscribe(cb, sender=sender)


def test_broadcast_wrong_argument_count():
	with pytest.raises(Exception):
		FooMessage.broadcast(object(), 1)


def test_broadcast_too_many_arguments():
	with pytest.raises(Exception):
		FooMessage.broadcast(object(), 1, 2, 3)


def test_broadcast_passes_all_arguments():
	cb = mock.Mock()
	sender = object()

	FooMessage.subscribe(cb)
	try:
		FooMessage.broadcast(sender, 10, 20)
		assert_called_once_with_message(
			cb,
			FooMessage,
			sender=sender,
			a=10,
			b=20,
		)
	finally:
		FooMessage.discard(cb)


def test_multiple_subscribers_receive_message():
	cb1 = mock.Mock()
	cb2 = mock.Mock()

	ExampleMessage.subscribe(cb1)
	ExampleMessage.subscribe(cb2)
	try:
		ExampleMessage.broadcast(object())

		cb1.assert_called_once()
		cb2.assert_called_once()
	finally:
		ExampleMessage.discard(cb1)
		ExampleMessage.discard(cb2)


def test_duplicate_subscriptions():
	cb = mock.Mock()

	ExampleMessage.subscribe(cb)
	ExampleMessage.subscribe(cb)
	try:
		ExampleMessage.broadcast(object())
		assert cb.call_count == 2
	finally:
		# Remove both registrations.
		ExampleMessage.discard(cb)
		ExampleMessage.discard(cb)
