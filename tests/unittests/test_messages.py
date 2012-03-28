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

import unittest

from horizons.messaging import Message

import mock


class ExampleMessage(Message):
	pass

class FooMessage(Message):
	arguments = ('a', 'b', )


class TestMessageBus(unittest.TestCase):

	def setUp(self):
		self.cb = mock.Mock()

	def assert_called_once_with(self, cb, message_type, **arguments):
		assert cb.call_count == 1
		msg = cb.call_args[0][0]
		for name, value in arguments.items():
			assert getattr(msg, name) == value

	def test_global_subscribe(self):
		ExampleMessage.subscribe(self.cb)

		# correct message type, cb is called
		ExampleMessage.broadcast(self)
		self.assert_called_once_with(self.cb, ExampleMessage, sender=self)
		self.cb.reset_mock()

		# wrong message type, cb is not called
		Message.broadcast(self)
		self.assertFalse(self.cb.called)

	def test_local_subscribe(self):
		ExampleMessage.subscribe(self.cb, sender=self)

		# correct message type, correct sender, cb is called
		ExampleMessage.broadcast(self)
		self.assert_called_once_with(self.cb, ExampleMessage, sender=self)
		self.cb.reset_mock()

		# correct message type, wrong sender, cb is not called
		ExampleMessage.broadcast(1)
		self.assertFalse(self.cb.called)
		self.cb.reset_mock()

		# wrong message type, correct sender, cb is not called
		Message.broadcast(self)
		self.assertFalse(self.cb.called)

	def test_unsubscribe(self):
		ExampleMessage.subscribe(self.cb)
		Message.subscribe(self.cb, sender=self)

		# broadcast local and global message, cb called two times
		ExampleMessage.broadcast(self)
		Message.broadcast(self)
		assert self.cb.call_count == 2
		self.cb.reset_mock()

		# after unsubscribing globally, only the local message is received
		ExampleMessage.unsubscribe(self.cb)
		ExampleMessage.broadcast(self)
		Message.broadcast(self)
		self.assert_called_once_with(self.cb, Message, sender=self)
		self.cb.reset_mock()

		# after unsubscribing locally, all subscriptions should be gone, cb not called
		Message.unsubscribe(self.cb, sender=self)
		ExampleMessage.broadcast(self)
		Message.broadcast(self)
		self.assertFalse(self.cb.called)


class TestMessage(unittest.TestCase):

	def test_sender_argument(self):
		msg = Message(self)
		self.assertEqual(msg.sender, self)

	def test_additional_arguments(self):
		msg = FooMessage(self, 1, 2)
		self.assertEqual(msg.sender, self)
		self.assertEqual(msg.a, 1)
		self.assertEqual(msg.b, 2)

	def test_wrong_arguments(self):
		self.assertRaises(Exception, FooMessage, self, 1)
