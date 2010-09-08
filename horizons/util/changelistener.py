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

class Changelistener(object):
	"""Trivial ChangeListener.
	The object that changes and the object that listens have to inherit from this class.
	An object calls _changed everytime something has changed, obviously.
	This function calls every Callback, that has been registered to listen for a change.
	NOTE: Changelisteners aren't saved, they have to be reregistered on load
	NOTE: Removelisteners must not access the object.
	"""
	def __init__(self, *args, **kwargs):
		super(Changelistener, self).__init__()
		self.__init()

	def __init(self):
		self.__listeners = WeakMethodList()
		self.__remove_listeners = WeakMethodList()

	## Normal change listener
	def add_change_listener(self, listener, call_listener_now = False):
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
		self.__remove_listeners.append(listener)

	def remove_remove_listener(self, listener):
		self.__remove_listeners.remove(listener)

	def has_remove_listener(self, listener):
		return (listener in self.__remove_listeners)

	def load(self, db, world_id):
		self.__init()

	def remove(self):
		for listener in self.__remove_listeners:
			listener()
		self.end()

	def end(self):
		self.__listeners = None
		self.__remove_listeners = None
