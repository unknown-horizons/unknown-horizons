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

import logging

from horizons.util import LivingObject, ManualConstructionSingleton
import copy

class Scheduler(LivingObject):
	""""Class providing timed callbacks.
	To start a timed callback, call add_new_object() to make the TimingThread Class create a CallbackObject for you.
	@param timer: Timer instance the schedular registers itself with.
	"""
	__metaclass__ = ManualConstructionSingleton

	log = logging.getLogger("scheduler")

	def __init__(self, timer):
		super(Scheduler, self).__init__()
		self.schedule = {}
		self.cur_tick = 0
		self.timer = timer
		self.timer.add_call(self.tick)

	def end(self):
		self.log.debug("Scheduler end; len: %s", len(self.schedule))
		self.schedule = None
		self.timer.remove_call(self.tick)
		self.timer = None
		super(Scheduler, self).end()

	def tick(self, tick_id):
		"""Threads main loop
		@param tick_id: int id of the tick.
		"""
		self.cur_tick = tick_id
		if self.cur_tick in self.schedule:
			self.log.debug("Scheduler: tick is %s, callbacks: %s", self.cur_tick, [ str(i) for i in self.schedule[self.cur_tick]])
			# DEBUG test: check if every callback really is executed
			num_callbacks = len(self.schedule[self.cur_tick])
			for callback in copy.copy(self.schedule[self.cur_tick]):
				self.log.debug("Scheduler(t:%s) calling %s", tick_id, str(callback))
				callback.callback()
				assert callback.loops >= -1
				if callback.loops != 0:
					self.add_object(callback) # readd object
				num_callbacks -= 1
			assert num_callbacks == 0
			del self.schedule[self.cur_tick]
		assert (len(self.schedule) == 0) or self.schedule.keys()[0] > self.cur_tick

	def add_object(self, callback_obj):
		"""Adds a new CallbackObject instance to the callbacks list
		@param callback_obj: CallbackObject type object, containing all neccessary  information
		"""
		if callback_obj.loops > 0:
			callback_obj.loops -= 1
		tick_key = self.cur_tick + callback_obj.runin
		if not tick_key in self.schedule:
			self.schedule[tick_key] = []
		self.log.debug("Adding new object %s at tick %s", callback_obj, tick_key)
		self.schedule[tick_key].append(callback_obj)

	def add_new_object(self, callback, class_instance, runin=1, loops=1):
		"""Creates a new CallbackObject instance and calls the self.add_object() function.
		@param callback: lambda function callback, which is called runin ticks.
		@param class_instance: class instance the function belongs to.
		@param runin: int number of ticks after which the callback is called. Standard is 1, run next tick.
		@param loops: How often the callback is called. -1 = infinit times. Standard is 1, run once."""
		callback_obj = CallbackObject(self, callback, class_instance, runin, loops)
		self.add_object(callback_obj)

	def rem_object(self, callback_obj):
		"""Removes a CallbackObject from all callback lists
		@param callback_obj: CallbackObject to remove
		@return: int, number of removed calls
		"""
		removed_objs = 0
		if self.schedule is not None:
			for key in self.schedule:
				for i in xrange(0, self.schedule[key].count(callback_obj)):
					self.schedule[key].remove(callback_obj)
					removed_objs += 1
		return removed_objs


	#TODO: Check if this is still necessary for weak referenced objects
	def rem_all_classinst_calls(self, class_instance):
		"""Removes all callbacks from the scheduler that belong to the class instance class_inst."""
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance is class_instance:
					self.schedule[key].remove(callback_obj)

	def rem_call(self, instance, callback):
		"""Removes all callbacks of 'instance' that are 'callback'
		@param instance: the instance that would execute the call
		@param callback: the function to remove
		@return: int, number of removed calls
		"""
		assert callable(callback)
		removed_calls = 0
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance is instance and callback_obj.callback == callback:
					self.schedule[key].remove(callback_obj)
					removed_calls += 1
		return removed_calls

	def get_classinst_calls(self, instance, callback = None):
		"""Returns all CallbackObjects of instance.
		Optionally, a specific callback can be specified.
		@param instance: the instance to execute the call
		@param callback: None to get all calls of instance,
		                 else only calls that execute callback.
		@return: dict, entries: { CallbackObject: remaining_ticks_to_executing }
		"""
		calls = {}
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance is instance:
					if callback is None:
						calls[callback_obj] = key - self.cur_tick
					elif callback_obj.callback == callback:
						calls[callback_obj] = key - self.cur_tick
		return calls

	def get_remaining_ticks(self, instance, callback):
		"""Returns in how many ticks a callback is executed. You must specify 1 single call.
		@param *: just like get_classinst_calls
		@return int."""
		calls = self.get_classinst_calls(instance, callback)
		assert len(calls) == 1, 'got %i calls for %s %s' % (len(calls), instance, callback)
		return calls.values()[0]

	def get_ticks(self, seconds):
		"""Call propagated to time instance"""
		return self.timer.get_ticks(seconds)


class CallbackObject(object):
	"""Class used by the TimerManager Class to organize callbacks."""
	def __init__(self, scheduler, callback, class_instance, runin=1, loops=1):
		"""Creates the CallbackObject instance.
		@param scheduler: reference to the scheduler, necessary to react properly on weak reference callbacks
		@param callback: lambda function callback, which is called runin ticks.
		@param class_instance: class instance the original function(not the lambda function!) belongs to.
		@param runin: int number of ticks after which the callback is called. Standard is 1, run next tick.
		@param loops: How often the callback is called. -1 = infinit times. Standard is 1, run once.
		"""
		assert runin > 0, "Can't schedule callbacks in the past, runin must be a positive number"
		assert (loops > 0) or (loops == -1), \
			"Loop count must be a positive number or -1 for infinite repeat"
		assert callable(callback)

		self.callback = callback

		self.scheduler = scheduler
		self.runin = runin
		self.loops = loops
		self.class_instance = class_instance

	def __str__(self):
		return "Callback("+str(self.callback)+" on "+str(self.class_instance)+")"
