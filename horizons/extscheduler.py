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
import heapq

from horizons.util import ManualConstructionSingleton


class _ExtCallbackObject(object):
	"""Class used by the ExtScheduler Class to organize callbacks."""

	def __init__(self, callback, class_instance, run_in=1, loops=1):
		"""Creates the CallbackObject instance.
		@param callback: lambda function callback, which is called run_in ticks.
		@param class_instance: class instance the original function(not the lambda function!) belongs to.
		@param run_in: int number of ticks after which the callback is called. Standard is 1, run next tick.
		@param loops: How often the callback is called. -1 = infinite times. Standard is 1, run once.
		"""
		self.callback = callback
		self.class_instance = class_instance
		self.run_in = run_in
		self.loops = loops


	def __str__(self):
		return "ExtSchedCb(%s on %s)" % (self.callback, self.class_instance)


class ExtScheduler(object):
	"""The ExtScheduler is used for time based events that are not part of the simulation(gui, menu, scrolling).
	To start a timed callback, call add_new_object() to make the TimingThread Class create a CallbackObject for you.
	@param pump: pump list the scheduler registers itself with.
	"""
	__metaclass__ = ManualConstructionSingleton

	NOOP = _ExtCallbackObject(lambda : 42*1337-3.14, None)

	def __init__(self, pump):
		super(ExtScheduler, self).__init__()
		self.schedule = []
		self.pump = pump
		self.pump.append(self.tick)

	def tick(self):
		"""Threads main loop
		@param tick_id: int id of the tick.
		"""
		while self.schedule:
			elem = self.schedule[0] # heap, first elem is smallest
			if elem[0] <= time.time():
				dont_use = heapq.heappop(self.schedule)
				assert dont_use is elem
				obj = elem[1]
				obj.callback()
				if obj.loops > 0 or obj.loops is -1:
					self.add_object(obj) # re-add object
			else:
				break

	def add_object(self, obj):
		"""Adds a new CallbackObject instance to the callbacks list
		@param object: CallbackObject type object, containing all necessary information
		"""
		if obj.loops > 0:
			obj.loops -= 1
		# sort by first entry, which is execution time
		heapq.heappush(self.schedule, [(time.time() + obj.run_in), obj])

	def add_new_object(self, callback, class_instance, run_in=1, loops=1):
		"""Creates a new CallbackObject instance and calls the self.add_object() function.
		@param callback: function callback, which is called run_in time.
		@param class_instance: class instance the function belongs to.
		@param run_in: float number of seconds after which the callback is called. Standard is 1, run next second.
		@param loops: How often the callback is called. -1 = infinite times. Standard is 1, run once."""
		obj = _ExtCallbackObject(callback, class_instance, run_in, loops)
		self.add_object(obj)

	def rem_all_classinst_calls(self, class_instance):
		"""Removes all callbacks from the scheduler that belong to the class instance class_inst.
		@return: number of removed callbacks"""
		for tup in self.schedule:
			if tup[1].class_instance is class_instance:
				# don't destory heap
				tup[1] = self.__class__.NOOP

	def rem_call(self, instance, callback):
		"""Removes all callbacks of 'instance' that are 'callback'
		@param instance: the instance that would execute the call
		@param callback: the function to remove
		"""
		for tup in self.schedule:
			if tup[1].class_instance is instance and tup[1].callback == callback:
				# don't destroy heap
				tup[1] = self.__class__.NOOP

	def __del__(self):
		self.schedule = []
		self.pump.remove(self.tick)
		self.pump = None
