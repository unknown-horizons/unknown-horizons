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


class Callback(object):
	"""This class basically provides just callbacks with arguments.
	The same can be achieved via 'lambda: f(arg1, arg2)', but this class has
	more flexibility; e.g. you can compare callbacks, which can't be done with lambda functions.
	"""
	def __init__(self, callback_function, *args, **kwargs):
		assert callable(callback_function), "Argument to for callback_f is %s" % callback_function
		self.callback = callback_function
		self.args = args
		self.kwargs = kwargs

	@staticmethod
	def ChainedCallbacks(*args):
		"""Named constructor for callbacks executed in a row.
		Use Callback objects to pass arguments to the callbacks.
		It is guaranteed that the callbacks are executed in order.
		@param args: callables"""
		callbacks = [ Callback(i) for i in args ]
		def tmp():
			for i in callbacks:
				i()
		return Callback(tmp)

	def __call__(self):
		return self.callback(*self.args, **self.kwargs)

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

	def __hash__(self):
		return hash((self.callback, self.args,
		             tuple(self.kwargs.iteritems()))) # to tuple, dict is unhashable

	def __str__(self):
		return 'Callback(%s, %s, %s)' % (self.callback, self.args, self.kwargs)
