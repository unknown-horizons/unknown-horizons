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

from unittest import TestCase
from unittest.mock import Mock

from horizons.scheduler import Scheduler


class TestScheduler(TestCase):

	def setUp(self):
		self.callback = Mock()
		self.timer = Mock()
		Scheduler.create_instance(self.timer)
		self.scheduler = Scheduler()
		self.timer.reset_mock()

	def tearDown(self):
		Scheduler.destroy_instance()

	def test_create_then_register_with_timer(self):
		# create a new scheduler but do not reset timer mock
		Scheduler.destroy_instance()
		Scheduler.create_instance(self.timer)
		self.scheduler = Scheduler()
		self.timer.add_call.assert_called_once_with(self.scheduler.tick)

	def test_end_then_unregister_from_timer(self):
		self.scheduler.end()
		self.timer.remove_call.assert_called_once_with(self.scheduler.tick)

	def test_multiple_sequential_ticks(self):
		self.scheduler.before_ticking()
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertEqual(Scheduler.FIRST_TICK_ID, self.scheduler.cur_tick)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1)
		self.assertEqual(Scheduler.FIRST_TICK_ID + 1, self.scheduler.cur_tick)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 2)
		self.assertEqual(Scheduler.FIRST_TICK_ID + 2, self.scheduler.cur_tick)

	def test_fail_when_missing_start_tick(self):
		def tick():
			self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1)
		self.scheduler.before_ticking()
		self.assertRaises(Exception, tick)

	def test_fail_when_same_tick_twice(self):
		def tick():
			self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.scheduler.before_ticking()
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertRaises(Exception, tick)

	def test_add_callback_before_first_tick(self):
		self.scheduler.add_new_object(self.callback, None, run_in=0)
		self.scheduler.before_ticking()
		self.callback.assert_called_once_with()

	def test_add_callback_run_in_1_on_first_tick(self):
		self.scheduler.add_new_object(self.callback, None, run_in=1)
		self.scheduler.before_ticking()
		self.assertFalse(self.callback.called)

		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.callback.assert_called_once_with()

	def test_add_callback_only_triggered_once(self):
		self.scheduler.before_ticking()
		self.scheduler.add_new_object(self.callback, None, run_in=2)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertFalse(self.callback.called)

		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1) # callback called here
		self.callback.reset_mock()

		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 2)
		self.assertFalse(self.callback.called)

	def test_started_ticking_then_add_callback_for_next_tick(self):
		self.scheduler.before_ticking()
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.scheduler.add_new_object(self.callback, None, run_in=0)
		self.assertFalse(self.callback.called)

		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1)
		self.callback.assert_called_once_with()

	def test_started_ticking_then_add_callback_for_future(self):
		self.scheduler.before_ticking()
		self.scheduler.add_new_object(self.callback, None, run_in=2)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertFalse(self.callback.called)

		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1)
		self.callback.assert_called_once_with()

	def test_within_callback_add_new_callback_for_same_tick(self):
		self.scheduler.before_ticking()
		callback2 = Mock()
		def add_callback():
			self.scheduler.add_new_object(callback2, None, run_in=0)
		self.callback.side_effect = add_callback

		self.scheduler.add_new_object(self.callback, None, run_in=1)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		callback2.assert_called_once_with()

	def test_within_callback_add_new_callback_for_future_tick(self):
		self.scheduler.before_ticking()
		callback2 = Mock()
		def add_callback():
			self.scheduler.add_new_object(callback2, None, run_in=1)
		self.callback.side_effect = add_callback

		self.scheduler.add_new_object(self.callback, None, run_in=1)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertFalse(callback2.called)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1)
		callback2.assert_called_once_with()

	def test_add_periodic_callback_called_every_tick_3_times(self):
		self.scheduler.before_ticking()
		self.scheduler.add_new_object(self.callback, None, run_in=1, loops=4)
		for i in range(Scheduler.FIRST_TICK_ID, 4):
			self.scheduler.tick(i)
			self.callback.assert_called_once_with()
			self.callback.reset_mock()

		self.scheduler.tick(4)
		self.assertFalse(self.callback.called)

	def test_add_periodic_callback_run_every_other_tick_3_times(self):
		self.scheduler.before_ticking()
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.scheduler.add_new_object(self.callback, None, run_in=1, loops=3, loop_interval=2)

		for i in range(Scheduler.FIRST_TICK_ID + 1, 7):
			self.scheduler.tick(i)
			if (i % 2 - 1 == 0):
				self.callback.assert_called_once_with()
				self.callback.reset_mock()
			else:
				self.assertFalse(self.callback.called)

		self.scheduler.tick(7)
		self.assertFalse(self.callback.called)

	def test_remove_call_from_instance(self):
		self.scheduler.before_ticking()
		instance1 = Mock()
		instance2 = Mock()
		self.scheduler.add_new_object(self.callback, instance1, run_in=1)
		self.scheduler.add_new_object(self.callback, instance2, run_in=1)
		self.scheduler.rem_call(instance1, self.callback)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.callback.assert_called_once_with() # instance2 callback kept

	def test_list_and_manually_remove_all_classinstance_callbacks(self):
		self.scheduler.before_ticking()
		instance1 = Mock()
		self.scheduler.add_new_object(self.callback, instance1, run_in=1)
		self.scheduler.add_new_object(self.callback, instance1, run_in=1)

		callbacks = self.scheduler.get_classinst_calls(instance1)
		for callback in callbacks:
			self.scheduler.rem_object(callback)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertFalse(self.callback.called)

	def test_remove_all_classinstance_callbacks(self):
		self.scheduler.before_ticking()
		instance1 = Mock()
		self.scheduler.add_new_object(self.callback, instance1, run_in=1)
		self.scheduler.add_new_object(self.callback, instance1, run_in=1)

		self.scheduler.rem_all_classinst_calls(instance1)
		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertFalse(self.callback.called)

	def test_get_remaining_tick_until_callback(self):
		self.scheduler.before_ticking()
		instance = Mock()
		self.scheduler.add_new_object(self.callback, instance, run_in=2)
		self.assertEqual(2, self.scheduler.get_remaining_ticks(instance, self.callback))

		self.scheduler.tick(Scheduler.FIRST_TICK_ID)
		self.assertEqual(1, self.scheduler.get_remaining_ticks(instance, self.callback))

	def test_get_remaining_tick_periodic_callback(self):
		self.scheduler.before_ticking()
		instance = Mock()
		self.scheduler.add_new_object(self.callback, instance, run_in=1, loops=2, loop_interval=3)
		self.assertEqual(1, self.scheduler.get_remaining_ticks(instance, self.callback))

		self.scheduler.tick(Scheduler.FIRST_TICK_ID) # first time fired
		self.assertEqual(3, self.scheduler.get_remaining_ticks(instance, self.callback))
		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 1)
		self.assertEqual(2, self.scheduler.get_remaining_ticks(instance, self.callback))
		self.scheduler.tick(Scheduler.FIRST_TICK_ID + 2)
		self.assertEqual(1, self.scheduler.get_remaining_ticks(instance, self.callback))
