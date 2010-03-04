# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from util.living import LivingObject
from horizons.settings import Settings

class Timer(LivingObject):
	"""
	The Timer class manages game-ticks, every tick executes a set of functions in its call lists,
	this is especially important for multiplayer, to allow synchronous play.
	"""
	TEST_PASS, TEST_SKIP, TEST_RETRY_RESET_NEXT_TICK_TIME, TEST_RETRY_KEEP_NEXT_TICK_TIME = xrange(0, 4)

	possible_ticks_per_second = [16, 32, 48, 64]
	default_ticks_per_second = 16

	def __init__(self, tick_next_id = 0):
		"""
		@param tick_next_id: int next tick id
		"""
		super(Timer, self).__init__()
		Settings().addCategories('ticks')
		#Settings().ticks.setDefaults(default = 16, steps = [16, 32, 48, 64, 256])
		Settings().ticks.setDefaults(default = self.default_ticks_per_second, \
		                             steps = self.possible_ticks_per_second)
		self.ticks_per_second = Settings().ticks.default
		self.tick_next_id = tick_next_id
		self.tick_next_time = None
		self.tick_func_test = []
		self.tick_func_call = []
		horizons.main.fife.pump.append(self.check_tick)

	def end(self):
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
		return int(round( seconds*Settings().ticks.default ))

	def check_tick(self):
		"""check_tick is called by the engines _pump function to signal a frame idle."""
		if self.ticks_per_second == 0:
			return
		while time.time() >= self.tick_next_time:
			for f in self.tick_func_test:
				r = f(self.tick_next_id)
				if r == self.TEST_SKIP:
					self.tick_next_time = (self.tick_next_time or time.time()) + 1.0 / self.ticks_per_second
				elif r == self.TEST_RETRY_RESET_NEXT_TICK_TIME:
					self.tick_next_time = None
				elif r != self.TEST_RETRY_KEEP_NEXT_TICK_TIME:
					continue
				return
			for f in self.tick_func_call:
				f(self.tick_next_id)
			if self.ticks_per_second == 0:
				# If a callback changed the speed to zero, we have to exit
				return
			self.tick_next_time = (self.tick_next_time or time.time()) + 1.0 / self.ticks_per_second
			self.tick_next_id += 1
