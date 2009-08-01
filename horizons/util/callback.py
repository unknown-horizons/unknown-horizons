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


class Callback(object):
	"""This class basically provides just callbacks with arguments.
	The same can be achieved via 'lambda: f(arg1, arg2)', but this class has
	more flexibility; e.g. you can compare callbacks, which can't be done with lambda functions.
	"""
	def __init__(self, callback, *args, **kwargs):
		assert callable(callback)
		self.callback = callback
		self.args = args
		self.kwargs = kwargs

	def __call__(self):
		self.callback(*self.args, **self.kwargs)

	def __eq__(self, other):
		try:
			if other.callback == self.callback and \
				 other.args == self.args and \
				 other.kwargs == self.kwargs:
				return True
			else:
				return False
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)
