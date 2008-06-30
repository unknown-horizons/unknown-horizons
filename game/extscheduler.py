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

from game.scheduler import CallbackObject
import time

class ExtScheduler():
	"""The ExtScheduler ist used for time based events that are not part of the simulation(gui, menu, scrolling).
	To start a timed callback, call add_new_object() to make the TimingThread Class create a CallbackObject for you.
	@param pump: pump list the schedular registers itself with.
	"""

	def __init__(self, pump):
		self.schedule = []
		self.pump = pump
		self.pump.append(self.tick)

	def tick(self):
		"""Threads main loop
		@param tick_id: int id of the tick.
		"""
		for tup in self.schedule:
			if tup[0] <= time.time():
				object = self.schedule.pop(0)[1]
				object.callback()
				if object.loops > 0 or object.loops is -1:
					self.add_object(object) # re-add object
			else:
				break

	def add_object(self, object):
		"""Adds a new CallbackObject instance to the callbacks list
		@param object: CallbackObject type object, containing all neccessary  information
		"""
		if object.loops > 0:
			object.loops -= 1
		self.schedule.append(((time.time() + object.runin), object))
		self.schedule.sort()

	def add_new_object(self, callback, class_instance, runin=1, loops=1):
		"""Creates a new CallbackObject instance and calls the self.add_object() function.
		@param callback: function callback, which is called runin time.
		@param class_instance: class instance the function belongs to.
		@param runin: float number of seconds after which the callback is called. Standard is 1, run next tick.
		@param loops: How often the callback is called. -1 = infinit times. Standard is 1, run once."""
		object = CallbackObject(callback, class_instance, runin, loops)
		self.add_object(object)

	def rem_all_classinst_calls(self, class_instance):
		"""Removes all callbacks from the scheduler that belong to the class instance class_inst."""
		for tup in self.schedule:
			if tup[1].class_instance is class_instance:
				self.schedule.remove(tup)

	def __del__(self):
		self.schedule = []
		self.pump.remove(self.tick)
		self.pump = None
