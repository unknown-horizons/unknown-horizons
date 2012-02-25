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

from horizons.util.python import WeakMethodList
from horizons.util.python.callback import Callback

class ChangeListener(object):
	"""Trivial ChangeListener.
	The object that changes and the object that listens have to inherit from this class.
	An object calls _changed everytime something has changed, obviously.
	This function calls every Callback, that has been registered to listen for a change.
	NOTE: ChangeListeners aren't saved, they have to be reregistered on load
	NOTE: RemoveListeners must not access the object, as it is in progress of being destroyed.
	"""
	def __init__(self, *args, **kwargs):
		super(ChangeListener, self).__init__()
		self.__init()

	def __init(self):
		self.__listeners = WeakMethodList()
		self.__remove_listeners = WeakMethodList()
		# number of event calls
		# if any event is triggered increase the number, after all callbacks are executed decrease it
		# if it reaches 0 it means that in the current object all event callbacks were executed
		self.__event_call_number = 0
		self.__hard_remove = True

	def __remove_listener(self, listener_list, listener):
		# check if the listener should be hard removed
		# if so switch it in the list to None
		try:
			if self.__hard_remove:
				listener_list.remove(listener)
			else:
				listener_list[listener_list.index(listener)] = None
		except ValueError as e: # nicer error:
			raise ValueError(str(e)+
			                 "\nTried to remove: "+str(listener)+"\nat "+str(self)+
			                 "\nList: "+str([str(i) for i in listener_list]))

	def __call_listeners(self, listener_list):
		# instead of removing from list, switch the listener in position to None
		# this way, iteration won't be affected while listeners may modify the list
		self.__hard_remove = False
		# increase the event call number
		self.__event_call_number += 1
		for listener in listener_list:
			if listener:
				try:
					listener()
				except ReferenceError, e:
					# listener object is dead, don't crash since it doesn't need updates now anyway
					print 'Warning: the dead are listening to', self, ': ', e
					import traceback
					traceback.print_stack()

		self.__event_call_number -= 1

		if self.__event_call_number == 0:
			self.__hard_remove = True
			listener_list[:] = [ l for l in listener_list if l ]

	## Normal change listener
	def add_change_listener(self, listener, call_listener_now=False, no_duplicates=False):
		assert callable(listener)
		if not no_duplicates or listener not in self.__listeners:
			self.__listeners.append(listener)
		if call_listener_now: # also call if duplicate is adde
			listener()

	def remove_change_listener(self, listener):
		self.__remove_listener(self.__listeners, listener)

	def has_change_listener(self, listener):
		return (listener in self.__listeners)

	def discard_change_listener(self, listener):
		"""Remove listener if it's there"""
		if self.has_change_listener(listener):
			self.remove_change_listener(listener)

	def clear_change_listeners(self):
		"""Removes all change listeners"""
		self.__listeners = WeakMethodList()

	def _changed(self):
		"""Calls every listener when an object changed"""
		self.__call_listeners(self.__listeners)

	## Removal change listener
	def add_remove_listener(self, listener):
		"""A listener that listens for removal of the object"""
		assert callable(listener)
		self.__remove_listeners.append(listener)

	def remove_remove_listener(self, listener):
		self.__remove_listener(self.__remove_listeners, listener)

	def has_remove_listener(self, listener):
		return (listener in self.__remove_listeners)

	def load(self, db, world_id):
		self.__init()

	def remove(self):
		self.__call_listeners(self.__remove_listeners)
		self.end()

	def end(self):
		self.__listeners = None
		self.__remove_listeners = None


""" Class decorator that adds methods for listening for certain events to a class.
These methods get added automatically (eventname is the name you pass to the decorator):
- add_eventname_listener(listener):
    Adds listener callback. This function must take the object as first parameter plus
		any parameter that might be provided additionally to on_eventname.
- remove_eventname_listener(listener);
    Removes a listener previously added.
- has_eventname_listener(listener)
    Checks if a certain listener has been added.
- on_eventname
    This is used to call the callbacks when the event occured.
    Additional parameters may be provided, which are passed to the callback.

The goal is to simplify adding special listeners, as for example used in the
production_finished listener.
"""
def metaChangeListenerDecorator(event_name):
	def decorator(clas):
		list_name = "__"+event_name+"_listeners"
		event_call_number = "__"+event_name+"call_number"
		hard_remove_event = "__hard_remove"+event_name
		# trivial changelistener operations
		def add(self, listener):
			assert callable(listener)
			getattr(self, list_name).append(listener)

		def rem(self, listener):
			if getattr(self, hard_remove_event):
				getattr(self, list_name).remove(listener)
			else:
				listener_list = getattr(self, list_name)
				listener_list[listener_list.index(listener)] = None

		def has(self, listener):
			return listener in getattr(self, list_name)

		def on(self, *args, **kwargs):
			setattr(self, hard_remove_event, False)
			call_number = getattr(self, event_call_number) + 1
			setattr(self, event_call_number, call_number)
			for f in getattr(self, list_name):
				if f:
					# workaround for encapsuled arguments
					if isinstance(f, Callback):
						f()
					else:
						f(self, *args, **kwargs)

			call_number = getattr(self, event_call_number) - 1
			setattr(self, event_call_number, call_number)
			if getattr(self, event_call_number) == 0:
				setattr(self, hard_remove_event, True)
				setattr(self, list_name, [ l for l in getattr(self, list_name) if l ])

		# add methods to class
		setattr(clas, "add_"+event_name+"_listener", add)
		setattr(clas, "remove_"+event_name+"_listener", rem)
		setattr(clas, "has_"+event_name+"_listener", has)
		setattr(clas, "on_"+event_name, on)

		# use black __new__ magic to add the methods to the instances
		# think of it as being executed in __init__
		old_new = clas.__new__
		def new(cls, *args, **kwargs):
			# this is a proposed way of calling the "old" new:
			#obj = super(cls, cls).__new__(cls)
			# which results in endless recursion, if you construct an instance of a class,
			# that inherits from a base class on which the decorator has been applied.
			# therefore, this workaround is used:
			obj = old_new(cls, *args, **kwargs)
			setattr(obj, list_name, [])
			setattr(obj, event_call_number, 0)
			setattr(obj, hard_remove_event, True)
			return obj
		clas.__new__ = staticmethod(new)
		return clas
	return decorator
