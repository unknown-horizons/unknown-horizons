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

from weakmethod import WeakMethod

class WeakMethodList(list):
	"""A class that handles zero to n callbacks."""

	def __init__(self, callbacks=None):
		"""
		@param callbacks: None, a function, a list of functions, or a tuple of functions
		"""
		super(WeakMethodList, self).__init__()
		self.append(callbacks)

	def append(self, callback):
		"""Just like list.append, except it can also handle lists and discards None-values"""
		if callback is None:
			pass
		elif callable(callback):
			list.append(self, WeakMethod(callback))
		elif isinstance(callback, list, tuple):
			for i in callback:
				self.append(i)
		else:
			assert False

	extend = append

	def execute(self):
		"""Execute all callbacks. Number of callbacks may be zero to n."""
		for callback in self:
			callback()

	def remove(self, elem):
		if not isinstance(elem, WeakMethod):
			elem = WeakMethod(elem)
		list.remove(self, elem)

	def __contains__(self, elem):
		if isinstance(elem, WeakMethod):
			return list.__contains__(self, elem)
		else:
			return WeakMethod(elem) in self

	def __str__(self):
		return str([str(i) for i in self])
