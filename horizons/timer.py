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

import time
import horizons.main

from horizons.util.living import LivingObject
from horizons.constants import GAME_SPEED
from horizons.scheduler import Scheduler

class Timer(LivingObject):
	"""
	The Timer class manages game-ticks, every tick executes a set of functions in its call lists,
	this is especially important for multiplayer, to allow synchronous play.
	"""
	TEST_PASS, TEST_SKIP = xrange(0, 2)

	ACCEPTABLE_TICK_DELAY = 0.2 # sec
	DEFER_TICK_ON_DELAY_BY = 0.4 # sec


	def __init__(self, tick_next_id = Scheduler.FIRST_TICK_ID, freeze_protection=False):
		"""
		NOTE: timer will not start until activate() is called
		@param tick_next_id: int next tick id
		@param freeze_protection: whether to check for tick delay and strech time in case (breaks mp)
		"""
		super(Timer, self).__init__()
		self._freeze_protection = freeze_protection
		self.ticks_per_second = GAME_SPEED.TICKS_PER_SECOND
		self.tick_next_id = tick_next_id
		self.tick_next_time = None
		self.tick_func_test = []
		self.tick_func_call = []

	def activate(self):
		"""Actually starts the timer"""
		horizons.main.fife.pump.append(self.check_tick)

	def end(self):
		if self.check_tick in horizons.main.fife.pump:
			horizons.main.fife.pump.remove(self.check_tick)
		super(Timer, self).end()

	def add_test(self, call):
		"""Adds a call to the test list
		@param call: function function which should be added
		"""
		self.tick_func_test.append(call)

	def add_call(self, call):
		"""Adds a call to the call list
		@param call: function function which should be added
		"""
		self.tick_func_call.append(call)

	def remove_test(self, call):
		"""Removes a call from the test list
		@param call: function function which were added before
		"""
		self.tick_func_test.remove(call)

	def remove_call(self, call):
		"""Removes a call from the call list
		@param call: function function which were added before
		"""
		self.tick_func_call.remove(call)

	def get_ticks(self, seconds):
		"""Returns the number of ticks for the specified number of seconds.
		@param seconds: number of seconds that are to be converted into ticks
		@return: int
		"""
		return int(round( seconds*GAME_SPEED.TICKS_PER_SECOND))

	def check_tick(self):
		"""check_tick is called by the engines _pump function to signal a frame idle."""
		if self.ticks_per_second == 0:
			return
		while time.time() >= self.tick_next_time:
			for f in self.tick_func_test:
				r = f(self.tick_next_id)
				if r == self.TEST_SKIP:
					# If a callback changed the speed to zero, we have to exit
					if self.ticks_per_second != 0:
						self.tick_next_time = (self.tick_next_time or time.time()) + 1.0 / self.ticks_per_second
					return
			if self._freeze_protection and self.tick_next_time:
				# stretch time if we're too slow
				diff = time.time() - self.tick_next_time
				if diff > self.ACCEPTABLE_TICK_DELAY:
					self.tick_next_time += self.DEFER_TICK_ON_DELAY_BY
			for f in self.tick_func_call:
				f(self.tick_next_id)
			self.tick_next_id += 1
			if self.ticks_per_second == 0:
				# If a callback changed the speed to zero, we have to exit
				return
			self.tick_next_time = (self.tick_next_time or time.time()) + 1.0 / self.ticks_per_second
