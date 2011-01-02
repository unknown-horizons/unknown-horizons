# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

class ChangeListener(object):
	"""Trivial ChangeListener.
	The object that changes and the object that listens have to inherit from this class.
	An object calls _changed everytime something has changed, obviously.
	This function calls every Callback, that has been registered to listen for a change.
	NOTE: ChangeListeners aren't saved, they have to be reregistered on load
	NOTE: Removelisteners must not access the object, as it is in progress of being destroyed.
	"""
	def __init__(self, *args, **kwargs):
		super(ChangeListener, self).__init__()
		self._init()

	def _init(self):
		self.__listeners = WeakMethodList()
		self.__remove_listeners = WeakMethodList()

	## Normal change listener
	def add_change_listener(self, listener, call_listener_now = False):
		assert callable(listener)
		self.__listeners.append(listener)
		if call_listener_now:
			listener()

	def remove_change_listener(self, listener):
		self.__listeners.remove(listener)

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
		for listener in self.__listeners:
			listener()

	## Removal change listener
	def add_remove_listener(self, listener):
		"""A listener that listens for removal of the object"""
		assert callable(listener)
		self.__remove_listeners.append(listener)

	def remove_remove_listener(self, listener):
		self.__remove_listeners.remove(listener)

	def has_remove_listener(self, listener):
		return (listener in self.__remove_listeners)

	def load(self, db, world_id):
		self._init()

	def remove(self):
		for listener in self.__remove_listeners:
			listener()
		self.end()

	def end(self):
		self.__listeners = None
		self.__remove_listeners = None


""" Class decorator that adds methods for listening for certain events to a class.
These methods get added automatically (eventname is the name you pass to the decorator):
- add_eventname_listener(listener):
    adds listener callback. this function must take the object as first and only parameter
- remove_eventname_listener(listener);
    removes a listener previously added
- has_eventname_listener(listener)
    checks if a certain listener has been added
- on_eventname
    this is used to call the callbacks when the event occured.

The goal is to simplify adding special listeners, as for example used in the
production_finished listener.
"""
def metaChangeListenerDecorator(event_name):
	def decorator(clas):
		list_name = "__"+event_name+"_listeners"
		# trivial changelistener operations
		def add(self, listener):
			assert callable(listener)
			getattr(self, list_name).append(listener)
		def rem(self, listener):
			getattr(self, list_name).remove(listener)
		def has(self, listener):
			return listener in getattr(self, list_name)
		def on(self):
			for f in getattr(self, list_name):
				f(self)

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
			return obj
		clas.__new__ = staticmethod(new)
		return clas
	return decorator
