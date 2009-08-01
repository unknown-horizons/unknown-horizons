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

from living import LivingObject
from weakmethodlist import WeakMethodList

class Changelistener(LivingObject):
	def __init__(self, *args, **kwargs):
		super(Changelistener, self).__init__()
		self.__init()

	def __init(self):
		self.__listeners = WeakMethodList()

	def addChangeListener(self, listener, call_listener_now = False):
		self.__listeners.append(listener)
		if call_listener_now:
			listener()

	def removeChangeListener(self, listener):
		self.__listeners.remove(listener)

	def hasChangeListener(self, listener):
		if listener in self.__listeners:
			return True
		else:
			return False

	def _changed(self):
		for listener in self.__listeners:
			listener()

	def load(self, db, world_id):
		self.__init()

	def end(self):
		self.__listeners = None
