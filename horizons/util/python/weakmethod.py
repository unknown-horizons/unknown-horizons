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

import types
import weakref

class WeakMethod(object):
	def __init__(self, function):
		assert callable(function)

		if isinstance(function, types.MethodType) and function.im_self is not None:
			self.function = function.im_func
			self.instance = weakref.ref(function.im_self)
		else:
			self.function = function
			self.instance = None

	def __call__(self, *args, **kwargs):
		if self.instance is None:
			return self.function(*args, **kwargs)
		elif self.instance() is not None:
			return self.function(self.instance(), *args, **kwargs)
		else:
			raise ReferenceError("Instance: " + str(self.instance()) + \
													 " Function: "+ str(self.function) + \
													 " Function from module: " + str(self.function.__module__))

	def __eq__(self, other):
		if isinstance(other, WeakMethod):
			# check also if either instance is None or else if instances are equal
			return self.function == other.function and \
						 (other.instance is None if self.instance is None else
							self.instance() == other.instance())
		elif callable(other):
			return self == WeakMethod(other)
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __str__(self):
		return str(self.function)
