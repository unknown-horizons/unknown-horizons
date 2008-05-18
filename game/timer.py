# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

class Timer:
	"""
	The Timer class manages game-ticks, every tick executes a set of functions in its call lists,
	this is espacialy important for multiplayer, to allow syncronous play.
	"""
	TEST_PASS, TEST_SKIP, TEST_RETRY_RESET_NEXT_TICK_TIME, TEST_RETRY_KEEP_NEXT_TICK_TIME = xrange(0, 4)

	def __init__(self, ticks_per_second, tick_next_id = 0):
		"""
		@var ticks_per_second: int times per second the timer is to tick
		@var tick_next_id: int next tick id
		"""
		self.ticks_per_second = ticks_per_second
		self.tick_next_id = tick_next_id
		self.tick_next_time = None
		self.tick_func_test = []
		self.tick_func_call = []

	def add_test(self, call):
		"""Adds a call to the test list
		@var call: function function which should be added
		"""
		self.tick_func_test.append(call)

	def add_call(self, call):
		"""Adds a call to the call list
		@var call: function function which should be added
		"""
		self.tick_func_call.append(call)

	def remove_test(self, call):
		"""Removes a call from the test list
		@var call: function function which were added before
		"""
		self.tick_func_test.remove(call)

	def remove_call(self, call):
		"""Removes a call from the call list
		@var call: function function which were added before
		"""
		self.tick_func_call.remove(call)

	def check_tick(self):
		"""check_tick is called by the engines _pump function to signal a frame idle."""
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
			self.tick_next_time = (self.tick_next_time or time.time()) + 1.0 / self.ticks_per_second
			self.tick_next_id += 1
