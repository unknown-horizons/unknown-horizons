#!/usr/bin/env python

# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import horizons.main
import time

from unittest import TestCase
from mock import Mock, MagicMock, patch

from horizons.timer import Timer
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED

class TestTimer(TestCase):

	TICK_START = Scheduler.FIRST_TICK_ID
	TICK_PER_SEC = GAME_SPEED.TICKS_PER_SECOND

	TIME_START = 1000
	TIME_TICK = 1.0 / TICK_PER_SEC

	def setUp(self):
		self.callback = Mock()
		self.test = Mock()
		# Mock fife
		self.fife = Mock()
		self.pump = MagicMock()
		self.fife.pump = self.pump
		horizons.main.fife = self.fife
		# Mock system time
		self.timePatcher = patch('time.time')
		self.clock = self.timePatcher.start()
		self.clock.return_value = self.TIME_START
		# Create timer
		self.timer = Timer(freeze_protection=False)
		self.timer.ticks_per_second = self.TICK_PER_SEC
		self.timer.add_call(self.callback)
		pass

	def tearDown(self):
		self.timePatcher.stop()
		pass

	def test_activate_register_end_unregister_from_pump(self):
		self.timer.activate()
		self.fife.pump.append.assert_called_once_with(self.timer.check_tick)
		self.fife.pump.__contains__.return_value = True
		self.timer.end()
		self.fife.pump.remove.assert_called_once_with(self.timer.check_tick)
		pass

	def test_first_pump_then_one_tick(self):	
		self.timer.check_tick()
		self.callback.assert_called_once_with(TestTimer.TICK_START)

	def test_two_pump_same_time_only_one_tick(self):
		self.timer.check_tick()
		self.timer.check_tick()
		self.callback.assert_called_once_with(TestTimer.TICK_START)
		
	def test_two_pump_with_delay_then_two_ticks(self):
		self.timer.check_tick()
		self.callback.reset_mock()
		self.clock.return_value = self.TIME_START + self.TIME_TICK
		self.timer.check_tick()
		self.callback.assert_called_once_with(TestTimer.TICK_START + 1)

	def test_two_pump_close_in_time_then_only_one_tick(self):
		self.timer.check_tick()
		self.callback.reset_mock()
		self.clock.return_value = self.TIME_START + (self.TIME_TICK / 2)
		self.timer.check_tick()
		self.assertFalse(self.callback.called)

	def test_fast_pumping_only_tick_alternately(self):
		# tick 1
		self.timer.check_tick()
		self.clock.return_value = self.TIME_START + (0.5 * self.TIME_TICK)
		self.timer.check_tick()
		# tick 2
		self.callback.reset_mock()
		self.clock.return_value = self.TIME_START + (1.0 * self.TIME_TICK)
		self.timer.check_tick()
		self.callback.assert_called_once_with(TestTimer.TICK_START + 1)
		self.callback.reset_mock()
		self.clock.return_value = self.TIME_START + (1.5 * self.TIME_TICK)
		self.timer.check_tick()
		self.assertFalse(self.callback.called)

	def test_slow_pump_multiple_ticks(self):
		self.timer.check_tick()
		self.clock.return_value = self.TIME_START + (3.0 * self.TIME_TICK)
		self.callback.reset_mock()
		self.timer.check_tick()
		expected = [((self.TICK_START + 1,),), ((self.TICK_START + 2,),), ((self.TICK_START + 3,),)]
		self.assertEquals(expected, self.callback.call_args_list)

	def test_paused_pump_then_no_ticks(self):
		self.timer.check_tick()
		self.callback.reset_mock()
		self.timer.ticks_per_second = 0
		self.clock.return_value = self.TIME_START + self.TIME_TICK
		self.timer.check_tick()
		self.assertFalse(self.callback.called)

	def test_pause_pump_unpack_pump(self):
		self.timer.check_tick()
		self.timer.ticks_per_second = 0
		self.clock.return_value = self.TIME_START + (1.0 * self.TIME_TICK)
		self.timer.check_tick()

		self.timer.ticks_per_second = self.TICK_PER_SEC
		self.clock.return_value = self.TIME_START + (1.0 * self.TIME_TICK)
		self.callback.reset_mock()
		self.timer.check_tick()
		self.callback.assert_called_once_with(TestTimer.TICK_START + 1)

	def test_pause_on_callback(self):
		def set_paused(tick_id):
			self.timer.ticks_per_second = 0
		self.callback.side_effect = set_paused
		self.timer.check_tick()

		self.clock.return_value = self.TIME_START + (1.0 * self.TIME_TICK)
		self.callback.side_effect = None
		self.callback.reset_mock()
		self.timer.check_tick()
		self.assertFalse(self.callback.called)

	def test_freeze_protection(self):
		self.timer = Timer(freeze_protection=True)
		self.timer.ticks_per_second = self.TICK_PER_SEC
		self.timer.add_call(self.callback)
		self.timer.check_tick()
		self.callback.reset_mock()
	
		self.clock.return_value = self.TIME_START + (1.01 * self.TIME_TICK) + Timer.ACCEPTABLE_TICK_DELAY
		self.timer.check_tick()
		self.assertTrue(self.callback.called) # some number of ticks depending on tick delay
		self.callback.reset_mock()

		# will tick once after defer timeout
		self.clock.return_value = self.TIME_START + (2.02 * self.TIME_TICK) + Timer.DEFER_TICK_ON_DELAY_BY
		self.timer.check_tick()
		self.callback.assert_called_once_with(TestTimer.TICK_START + 2)
	
	def test_pump_test_func_pass(self):
		self.test.return_value = Timer.TEST_PASS
		self.timer.add_test(self.test)
		self.timer.check_tick()
		self.assertTrue(self.callback.called)

	def test_pump_test_func_skip(self):
		self.test.return_value = Timer.TEST_SKIP
		self.timer.add_test(self.test)
		self.timer.check_tick()
		self.assertFalse(self.callback.called)
