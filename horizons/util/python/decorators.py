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

"""Save general python function decorators here"""

class cachedfunction(object):
	"""Decorator that caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned, and
   not re-evaluated.
   """
	def __init__(self, func):
		self.func = func
		self.cache = {}
	def __call__(self, *args):
		try:
			return self.cache[args]
		except KeyError:
			self.cache[args] = value = self.func(*args)
			return value
		except TypeError:
			assert False, "Supplied invalid argument to cache decorator"


class cachedmethod(object):
	"""Same as cachedfunction, but works also for methods. Results are saved per instance"""
	def __init__(self, func):
		self.cache={}
		self.func=func

	def __get__(self, instance, cls=None):
		self.instance = instance
		return self

	def __call__(self,*args):
		instance = self.instance
		try:
			return self.cache[(instance, args)]
		except KeyError:
			self.cache[(instance,args)] = value = self.func(instance, *args)
			return value
		except TypeError:
			assert False, "Supplied invalid argument to cache decorator"

