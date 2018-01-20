# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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


class WeakMethod:
	def __init__(self, function):
		assert callable(function)

		if isinstance(function, types.MethodType) and function.__self__ is not None:
			self.function = function.__func__
			self.instance = weakref.ref(function.__self__)
		else:
			self.function = function
			self.instance = None

	def __call__(self, *args, **kwargs):
		if self.instance is None:
			return self.function(*args, **kwargs)
		elif self.instance() is not None:
			return self.function(self.instance(), *args, **kwargs)
		else:
			raise ReferenceError("Instance: {}  Function: {}  Function from module: {}"
			                     .format(self.instance(), self.function, self.function.__module__))

	def __eq__(self, other):
		if isinstance(other, WeakMethod):
			if self.function != other.function:
				return False
			# check also if either instance is None or else if instances are equal
			if self.instance is None:
				return other.instance is None
			else:
				return self.instance() == other.instance()
		elif callable(other):
			return self == WeakMethod(other)
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash((self.instance, self.function))

	def __str__(self):
		return str(self.function)
