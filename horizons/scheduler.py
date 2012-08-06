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

import logging

from collections import deque

import horizons.main

from horizons.util import LivingObject, ManualConstructionSingleton
from horizons.constants import GAME

class Scheduler(LivingObject):
	""""Class providing timed callbacks.
	Master of time.

	TODO:
	- Refactor to use a data structure that is suitable for iteration (ticking) as well as
	  searching/deleting by instance, possibly also by callback.
	  Suggestion: { tick -> { instance -> [callback] }} (basically a k-d tree)


	@param timer: Timer instance the schedular registers itself with.
	"""
	__metaclass__ = ManualConstructionSingleton

	log = logging.getLogger("scheduler")

	# the tick with this id is actually executed, and no tick with a smaller number can occur
	FIRST_TICK_ID = 0

	def __init__(self, timer):
		"""
		@param timer: Timer obj
		"""
		super(Scheduler, self).__init__()
		self.schedule = {}
		self.additional_cur_tick_schedule = [] # jobs to be executed at the same tick they were added
		self.calls_by_instance = {} # for get_classinst_calls
		self.cur_tick = self.__class__.FIRST_TICK_ID-1 # before ticking
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
		assert tick_id == self.cur_tick + 1
		self.cur_tick = tick_id

		if GAME.MAX_TICKS is not None and tick_id >= GAME.MAX_TICKS:
			horizons.main.quit()
			return

		if self.cur_tick in self.schedule:
			self.log.debug("Scheduler: tick %s, cbs: %s", self.cur_tick, len(self.schedule[self.cur_tick]))

			# use iteration method that works in case the list is altered during iteration
			# this can happen for e.g. rem_all_classinst_calls
			cur_schedule = self.schedule[self.cur_tick]
			while cur_schedule:
				callback = cur_schedule.popleft()
				# TODO: some system-level unit tests fail if this list is not processed in the correct order
				#       (i.e. if e.g. pop() was used here). This is an indication of invalid assumptions
				#       in the program and should be fixed.

				if hasattr(callback, "invalid"):
					self.log.debug("S(t:%s): %s: INVALID", tick_id, callback)
					continue
				self.log.debug("S(t:%s): %s", tick_id, callback)
				callback.callback()
				assert callback.loops >= -1
				if callback.loops != 0:
					self.add_object(callback, readd=True)
				else: # gone for good
					if callback.class_instance in self.calls_by_instance:
						# this can already be removed by e.g. rem_all_classinst_calls
						try:
							self.calls_by_instance[callback.class_instance].remove(callback)
						except ValueError:
							pass # also the callback can be deleted by e.g. rem_call
			del self.schedule[self.cur_tick]

			self.log.debug("Scheduler: finished tick %s", self.cur_tick)

		# run jobs added in the loop above
		self._run_additional_jobs()

		assert (not self.schedule) or self.schedule.iterkeys().next() > self.cur_tick

	def before_ticking(self):
		"""Called after game load and before game has started.
		Callbacks with run_in=0 are used as generic "do this as soon as the current context
		is finished". If this is done during load, it is supposed to mean tick -1, since it
		does not belong to the first tick. This method simulates this.
		"""
		self._run_additional_jobs()

	def _run_additional_jobs(self):
		for callback in self.additional_cur_tick_schedule:
			assert callback.loops == 0 # can't loop with no delay
			callback.callback()
		self.additional_cur_tick_schedule = []

	def add_object(self, callback_obj, readd=False):
		"""Adds a new CallbackObject instance to the callbacks list for the first time
		@param callback_obj: CallbackObject type object, containing all neccessary  information
		@param readd: Whether this object is added another time (looped)
		"""
		if callback_obj.loops > 0:
			callback_obj.loops -= 1
		if callback_obj.run_in == 0: # run in the current tick
			self.additional_cur_tick_schedule.append(callback_obj)
		else: # default: run in future tick
			interval = callback_obj.loop_interval if readd else callback_obj.run_in
			tick_key = self.cur_tick + interval
			if not tick_key in self.schedule:
				self.schedule[tick_key] = deque()
			callback_obj.tick = tick_key
			self.schedule[tick_key].append(callback_obj)
			if not readd:  # readded calls haven't been removed here
				if not callback_obj.class_instance in self.calls_by_instance:
					self.calls_by_instance[callback_obj.class_instance] = []
				self.calls_by_instance[callback_obj.class_instance].append( callback_obj )

	def add_new_object(self, callback, class_instance, run_in=1, loops=1, loop_interval=None):
		"""Creates a new CallbackObject instance and calls the self.add_object() function.
		@param callback: lambda function callback, which is called run_in ticks.
		@param class_instance: class instance the function belongs to.
		@param run_in: int number of ticks after which the callback is called. Defaults to 1, run next tick.
		@param loops: How often the callback is called. -1 = infinite times. Defautls to 1, run once.
		@param loop_interval: Delay between subsequent loops in ticks. Defaults to run_in."""
		callback_obj = _CallbackObject(self, callback, class_instance, run_in, loops, loop_interval)
		self.add_object(callback_obj)

	def rem_object(self, callback_obj):
		"""Removes a CallbackObject from all callback lists
		@param callback_obj: CallbackObject to remove
		@return: int, number of removed calls
		"""
		removed_objs = 0
		if self.schedule is not None:
			for key in self.schedule:
				while callback_obj in self.schedule[key]:
					self.schedule[key].remove(callback_obj)
					self.calls_by_instance[callback_obj.class_instance].remove(callback_obj)
					removed_objs += 1

		if not self.calls_by_instance[callback_obj.class_instance]:
			del self.calls_by_instance[callback_obj.class_instance]

		return removed_objs

	def rem_all_classinst_calls(self, class_instance):
		"""Removes all callbacks from the scheduler that belong to the class instance class_inst."""
		"""
		for key in self.schedule:
			callback_objects = self.schedule[key]
			for i in xrange(len(callback_objects) - 1, -1, -1):
				if callback_objects[i].class_instance is class_instance:
					del callback_objects[i]
		"""
		if class_instance in self.calls_by_instance:
			for callback_obj in self.calls_by_instance[class_instance]:
				callback_obj.invalid = True # don't remove, finding them all takes too long
			del self.calls_by_instance[class_instance]

		# filter additional callbacks as well
		self.additional_cur_tick_schedule = \
		    [ cb for cb in self.additional_cur_tick_schedule if cb.class_instance is not class_instance ]

	def rem_call(self, instance, callback):
		"""Removes all callbacks of 'instance' that are 'callback'
		@param instance: the instance that would execute the call
		@param callback: the function to remove
		@return: int, number of removed calls
		"""
		assert callable(callback)
		removed_calls = 0
		for key in self.schedule:
			callback_objects = self.schedule[key]
			for i in xrange(len(callback_objects) - 1, -1, -1):
				if callback_objects[i].class_instance is instance and callback_objects[i].callback == callback and \
				   not hasattr(callback_objects[i], "invalid"):
					del callback_objects[i]
					removed_calls += 1

		test = 0
		if removed_calls > 0: # there also must be calls in the calls_by_instance dict
			for i in xrange(len(self.calls_by_instance[instance]) - 1, -1, -1):
				obj = self.calls_by_instance[instance][i]
				if obj.callback == callback:
					del self.calls_by_instance[instance][i]
					test += 1
			assert test == removed_calls, "%s, %s" % (test, removed_calls)
			if not self.calls_by_instance[instance]:
				del self.calls_by_instance[instance]

		for i in xrange(len(self.additional_cur_tick_schedule) - 1, -1, -1):
			if self.additional_cur_tick_schedule[i].class_instance is instance and \
				self.additional_cur_tick_schedule[i].callback == callback:
					del callback_objects[i]
					removed_calls += 1

		return removed_calls

	def get_classinst_calls(self, instance, callback=None):
		"""Returns all CallbackObjects of instance.
		Optionally, a specific callback can be specified.
		@param instance: the instance to execute the call
		@param callback: None to get all calls of instance,
		                 else only calls that execute callback.
		@return: dict, entries: { CallbackObject: remaining_ticks_to_executing }
		"""
		calls = {}
		"""
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance is instance:
					if callback is None:
						calls[callback_obj] = key - self.cur_tick
					elif callback_obj.callback == callback:
						calls[callback_obj] = key - self.cur_tick
		"""
		if instance in self.calls_by_instance:
			for callback_obj in self.calls_by_instance[instance]:
				if  callback is None or callback_obj.callback == callback:
					calls[callback_obj] = callback_obj.tick - self.cur_tick
		return calls

	def get_remaining_ticks(self, instance, callback, assert_present=True):
		"""Returns in how many ticks a callback is executed. You must specify 1 single call.
		@param *: just like get_classinst_calls
		@param assert_present: assert that there must be sucha call
		@return int or possbile None if not assert_present"""
		calls = self.get_classinst_calls(instance, callback)
		if assert_present:
			assert len(calls) == 1, 'got %i calls for %s %s: %s' % (len(calls), instance, callback, [str(i) for i in calls])
			return calls.itervalues().next()
		else:
			return calls.itervalues().next() if calls else None

	def get_ticks(self, seconds):
		"""Call propagated to time instance"""
		return self.timer.get_ticks(seconds)

	def get_ticks_of_month(self):
		return self.timer.get_ticks(GAME.INGAME_TICK_INTERVAL)


class _CallbackObject(object):
	"""Class used by the TimerManager Class to organize callbacks."""
	def __init__(self, scheduler, callback, class_instance, run_in, loops, loop_interval):
		"""Creates the CallbackObject instance.
		@param scheduler: reference to the scheduler, necessary to react properly on weak reference callbacks
		@see Scheduler.add_new_object
		"""
		assert run_in >= 0, "Can't schedule callbacks in the past, run_in must be a non negative number"
		assert (loops > 0) or (loops == -1), \
			"Loop count must be a positive number or -1 for infinite repeat"
		assert callable(callback)
		assert loop_interval == None or loop_interval > 0

		self.callback = callback

		# TODO: check if this is used anywhere, it seems to be deprecated
		self.scheduler = scheduler

		self.run_in = run_in
		self.loops = loops
		self.loop_interval = loop_interval if loop_interval is not None else run_in
		self.class_instance = class_instance

	def __str__(self):
		cb = str(self.callback)
		if "_move_tick" in cb: # very crude measure to reduce log noise
			return "(_move_tick,%s)" %  self.class_instance.worldid

		return "SchedCb(%s on %s)" % (cb, self.class_instance)
