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

#because of unclean inheritance, bad usage of parameters and bad use of super in most world object, i cant trust that the init constructor is called.

from living import LivingObject
from weakmethod import WeakMethod

class Changelistener(LivingObject):
	def __init__(self, *args, **kwargs):
		super(Changelistener, self).__init__()
		self.__listeners = []

	def addChangeListener(self, listener):
		if not hasattr(self, '_Changelistener__listeners'):
			self.__listeners = []
		self.__listeners.append(WeakMethod(listener))

	def removeChangeListener(self, listener):
		if not hasattr(self, '_Changelistener__listeners'):
			self.__listeners = []
		self.__listeners.remove(WeakMethod(listener))

	def hasChangeListener(self, listener):
		if WeakMethod(listener) in self.__listeners:
			return True
		else:
			return False

	def _changed(self):
		if not hasattr(self, '_Changelistener__listeners'):
			self.__listeners = []
		for listener in self.__listeners:
			listener()

	def end(self):
		self.__listeners = None
