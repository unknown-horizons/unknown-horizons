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

import weakref
import horizons.main
from util.weakmethod import WeakMethod
from util.living import LivingObject

class Scheduler(LivingObject):
	""""Class providing timed callbacks.
	To start a timed callback, call add_new_object() to make the TimingThread Class create a CallbackObject for you.
	@param timer: Timer instance the schedular registers itself with.
	"""
	def __init__(self, timer):
		super(Scheduler, self).__init__()
		self.schedule = {}
		self.cur_tick = 0
		self.timer = timer
		self.timer.add_call(self.tick)

	def end(self):
		if horizons.main.debug:
			print "Scheduler len:", len(self.schedule)
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
			for callback in self.schedule[self.cur_tick]:
				if horizons.main.debug:
					print "Scheduler tick"
				callback.callback()
				assert callback.loops >= -1
				if callback.loops != 0:
					self.add_object(callback) # readd object
			del self.schedule[self.cur_tick]
		assert (len(self.schedule) == 0) or self.schedule.keys()[0] > self.cur_tick

	def add_object(self, callback_obj):
		"""Adds a new CallbackObject instance to the callbacks list
		@param callback_obj: CallbackObject type object, containing all neccessary  information
		"""
		if not (self.cur_tick + callback_obj.runin) in self.schedule:
			self.schedule[self.cur_tick + callback_obj.runin] = []
		if callback_obj.loops > 0:
			callback_obj.loops -= 1
		self.schedule[self.cur_tick + callback_obj.runin].append(callback_obj)

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
		"""
		if horizons.main.debug:
			print "Scheduler rem_object", callback_obj
		if self.schedule is not None:
			for key in self.schedule:
				for i in xrange(0, self.schedule[key].count(callback_obj)):
					self.schedule[key].remove(callback_obj)


	#TODO: Check if this is still necessary for weak referenced objects
	def rem_all_classinst_calls(self, class_instance):
		"""Removes all callbacks from the scheduler that belong to the class instance class_inst."""
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance() is class_instance:
					self.schedule[key].remove(callback_obj)

	def rem_call(self, instance, callback):
		"""Removes all callbacks of 'instance' that are 'callback'
		@param instance: the instance that would execute the call
		@param callback: the function to remove
		"""
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance() is instance and callback_obj.callback == callback:
					self.schedule[key].remove(callback_obj)

	def get_classinst_calls(self, instance, callback = None):
		"""Returns all CallbackObjects of instance.
		Optionally, a specific callback can be specified.
		@param instance: the instance to execute the call
		@param callback: None to get all calls of instance,
		                 else only calls that execute callback.
		                 Value has to be comparable to WeakMethod.
		@return: dict, entries: { CallbackObject: remaining_ticks_to_executing }
		"""
		calls = {}
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance() is instance:
					if callback is None:
						calls[callback_obj] = key - self.cur_tick
					elif callback_obj.callback == callback:
						calls[callback_obj] = key - self.cur_tick
		return calls


class CallbackObject(object):
	"""Class used by the TimerManager Class to organize callbacks."""
	def __init__(self, scheduler, callback, class_instance, runin=1, loops=1):
		"""Creates the CallbackObject instance.
		@param scheduler: reference to the scheduler, necessary to react properly on weak reference callbacks
		@param callback: lambda function callback, which is called runin ticks.
		@param class_instance: class instance the original function(not the lambda function!) belongs to.
		@param runin: int number of ticks after which the callback is called. Standard is 1, run next tick.
		@param loops: How often the callback is called. -1 = infinit times. Standard is 1, run once.
		@param weakref_aciton: A callback to register with the weak reference
		"""
		assert runin > 0, "Can't schedule callbacks in the past, runin must be a positive number"
		assert (loops > 0) or (loops == -1), \
			"Loop count must be a positive number or -1 for infinite repeat"

		self.callback = WeakMethod(callback)

		# Check for persisting strong references
		if horizons.main.debug:
			import gc
			if (class_instance in gc.get_referents(self.callback)):
				del self.callback
				raise ValueError("callback has strong reference to class_instance")

		self.scheduler = scheduler
		self.runin = runin
		self.loops = loops
		self.class_instance = weakref.ref(class_instance, lambda ref: self.scheduler.rem_object(self))
