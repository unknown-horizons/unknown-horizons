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

from horizons.util.messaging.message import Message
from horizons.util.messaging.messagebus import MessageBus

import mock


class ExampleMessage(Message):
	pass

class FooMessage(Message):
	arguments = ('a', 'b', )


class TestMessageBus(unittest.TestCase):

	def setUp(self):
		self.bus = MessageBus()
		self.cb = mock.Mock()

	def test_global_subscribe(self):
		self.bus.subscribe_globally(ExampleMessage, self.cb)

		# correct message type, cb is called
		msg = ExampleMessage(self)
		self.bus.broadcast(msg)
		self.cb.assert_called_once_with(msg)
		self.cb.reset_mock()

		# wrong message type, cb is not called
		self.bus.broadcast(Message(self))
		self.assertFalse(self.cb.called)

	def test_local_subscribe(self):
		self.bus.subscribe_locally(ExampleMessage, self, self.cb)

		# correct message type, correct sender, cb is called
		msg = ExampleMessage(self)
		self.bus.broadcast(msg)
		self.cb.assert_called_once_with(msg)
		self.cb.reset_mock()

		# correct message type, wrong sender, cb is not called
		self.bus.broadcast(ExampleMessage(1))
		self.assertFalse(self.cb.called)
		self.cb.reset_mock()

		# wrong message type, correct sender, cb is not called
		self.bus.broadcast(Message(self))
		self.assertFalse(self.cb.called)

	def test_unsubscribe(self):
		self.bus.subscribe_globally(ExampleMessage, self.cb)
		self.bus.subscribe_locally(Message, self, self.cb)

		msg1 = ExampleMessage(self)
		msg2 = Message(self)

		# broadcast local and global message, cb called two times
		self.bus.broadcast(msg1)
		self.bus.broadcast(msg2)
		self.cb.assert_any_call(msg1)
		self.cb.assert_any_call(msg2)
		self.cb.reset_mock()

		# after unsubscribing globally, only the local message is received
		self.bus.unsubscribe_globally(ExampleMessage, self.cb)
		self.bus.broadcast(msg1)
		self.bus.broadcast(msg2)
		self.cb.assert_called_with(msg2)
		self.cb.reset_mock()

		# after unsubscribing locally, all subscriptions should be gone, cb not called
		self.bus.unsubscribe_locally(Message, self, self.cb)
		self.bus.broadcast(msg1)
		self.bus.broadcast(msg2)
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
