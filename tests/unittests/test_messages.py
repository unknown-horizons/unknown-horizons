# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
	Check whether mock `cb` was called with an instance of `message_type` and the given
	`arguments`.
	"""
	assert cb.call_count == 1
	msg = cb.call_args[0][0]
	for name, value in arguments.items():
		assert getattr(msg, name) == value


def test_messagebus_global_subscribe():
	"""
	Test global (sender-independent) subscription to messages.
	"""
	cb = mock.Mock()
	sender = object()

	ExampleMessage.subscribe(cb)

	# correct message type, cb is called
	ExampleMessage.broadcast(sender)
	assert_called_once_with_message(cb, ExampleMessage, sender=sender)
	cb.reset_mock()

	# wrong message type, cb is not called
	Message.broadcast(sender)
	assert not cb.called


def test_messagebus_local_subscribe():
	"""
	Test local (sender-specific) subscription to messages.
	"""
	cb = mock.Mock()
	sender = object()

	ExampleMessage.subscribe(cb, sender=sender)

	# correct message type, correct sender, cb is called
	ExampleMessage.broadcast(sender)
	assert_called_once_with_message(cb, ExampleMessage, sender=sender)
	cb.reset_mock()

	# correct message type, wrong sender, cb is not called
	ExampleMessage.broadcast(1)
	assert not cb.called
	cb.reset_mock()

	# wrong message type, correct sender, cb is not called
	Message.broadcast(sender)
	assert not cb.called


def test_messagebus_unsubscribe():
	"""
	Test unsubscribe from messages.
	"""
	cb = mock.Mock()
	sender = object()

	ExampleMessage.subscribe(cb)
	Message.subscribe(cb, sender=sender)

	# broadcast local and global message, cb called two times
	ExampleMessage.broadcast(sender)
	Message.broadcast(sender)
	assert cb.call_count == 2
	cb.reset_mock()

	# after unsubscribing globally, only the local message is received
	ExampleMessage.unsubscribe(cb)
	ExampleMessage.broadcast(sender)
	Message.broadcast(sender)
	assert_called_once_with_message(cb, Message, sender=sender)
	cb.reset_mock()

	# after unsubscribing locally, all subscriptions should be gone, cb not called
	Message.unsubscribe(cb, sender=sender)
	ExampleMessage.broadcast(sender)
	Message.broadcast(sender)
	assert not cb.called
