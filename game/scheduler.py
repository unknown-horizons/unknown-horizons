# ###################################################
# Copyright (C) 2008 The OpenAnno Team
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

import game.main
from game.util import livingObject
import weakref

class Scheduler(livingObject):
	""""Class providing timed callbacks.
	To start a timed callback, call add_new_object() to make the TimingThread Class create a CallbackObject for you.
	@param timer: Timer instance the schedular registers itself with.
	"""
	def begin(self, timer):
		super(Scheduler, self).begin()
		self.schedule = {}
		self.cur_tick = 0
		self.timer = timer
		self.timer.add_call(self.tick)

	def tick(self, tick_id):
		"""Threads main loop
		@param tick_id: int id of the tick.
		"""
		self.cur_tick = tick_id
		if self.schedule.has_key(self.cur_tick):
			for callback in self.schedule[self.cur_tick]:
				callback.callback()
				assert callback.loops >= -1
				if callback.loops is not 0:
					self.add_object(callback) # readd object
			del self.schedule[self.cur_tick]
		assert (len(self.schedule) == 0) or self.schedule.keys()[0] > self.cur_tick

	def add_object(self, callback_obj):
		"""Adds a new CallbackObject instance to the callbacks list
		@param callback_obj: CallbackObject type object, containing all neccessary  information
		"""
		if not self.schedule.has_key(self.cur_tick + callback_obj.runin):
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
		for key in self.schedule:
			for i in xrange(0, self.schedule[key].count(callback_obj)):
				self.schedule[key].remove(callback_obj)			
		

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
		"""
		for key in self.schedule:
			for callback_obj in self.schedule[key]:
				if callback_obj.class_instance is instance and callback_obj.callback == callback:
					print 'REM_CALL', callback_obj.callback
					self.schedule[key].remove(callback_obj)

	def end(self):
		self.schedule = {}
		self._is_ended = True
		self.timer.remove_call(self.tick)
		self.timer = None

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
		
		# Do some input validation, otherwise errors occure long after wrong data was added
		if not callable(callback):
			raise ValueError("callback parameter is not callable")			

		if runin < 1:
			raise ValueError("Can't schedule callbacks in the past, runin must be a positive number")
			
		if (loops < -1) or (loops is 0):
			raise ValueError("Loop count must be a positive number or -1 for infinite repeat")
		
		# We have to unwrap bound methods, because they normally hold a strong reference
		from new import instancemethod
		if isinstance(callback, instancemethod):
			func = callback.im_func
			ref = weakref.ref(callback.im_self)
			self.callback = lambda: func(ref())
		else:
			self.callback = callback
		
		# Check for persisting strong references
		if __debug__:
			import gc
			if (class_instance in gc.get_referents(self.callback)):
				del self.callback
				raise ValueError("callback has strong reference to class_instance")
				
		self.scheduler = scheduler
		self.runin = runin
		self.loops = loops	
		self.class_instance = weakref.ref(class_instance, lambda ref: self.scheduler.rem_object(self))
	
