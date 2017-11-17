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

"""Save general python function decorators here"""

import functools
import time
from typing import Any, Dict, Tuple

FuncArgs = Tuple[Any, ...]
FuncKwargsTuple = Tuple[Tuple[str, Any]]


class cachedfunction:
	"""Decorator that caches a function's return value each time it is called.
	If called later with the same arguments, the cached value is returned, and
	not re-evaluated.
	"""
	def __init__(self, func):
		self.func = func
		self.cache = {} # type: Dict[Tuple[FuncArgs, FuncKwargsTuple], Any]

	def __call__(self, *args, **kwargs):
		# dicts are not hashable, convert kwargs to a tuple
		kwargs_tuple = tuple(sorted(kwargs.items()))

		try:
			return self.cache[(args, kwargs_tuple)]
		except KeyError:
			self.cache[(args, kwargs_tuple)] = value = self.func(*args, **kwargs)
			return value
		except TypeError:
			assert False, "Supplied invalid argument to cache decorator"


class cachedmethod:
	"""Same as cachedfunction, but works also for methods. Results are saved per instance"""
	def __init__(self, func):
		self.cache = {} # type: Dict[Tuple[Any, FuncArgs, FuncKwargsTuple], Any]
		self.func = func

	def __get__(self, instance, cls=None):
		self.instance = instance
		return self

	def __call__(self, *args, **kwargs):
		# dicts are not hashable, convert kwargs to a tuple
		kwargs_tuple = tuple(sorted(kwargs.items()))

		instance = self.instance

		try:
			return self.cache[(instance, args, kwargs_tuple)]
		except KeyError:
			self.cache[(instance, args, kwargs_tuple)] = value = self.func(instance, *args, **kwargs)
			return value
		except TypeError:
			assert False, "Supplied invalid argument to cache decorator"


def temporary_cachedmethod(timeout):
	"""
	Same as cachedproperty, but cached values only remain valid for a certain duration
	@param timeout: number of seconds to cache the value for
	"""
	class _temporary_cachedmethod(cachedmethod):
		def __init__(self, func, timeout):
			super().__init__(func)
			self.timeout = timeout
			self.cache_dates = {} # type: Dict[Tuple[Any, FuncArgs, FuncKwargsTuple], Any]

		def __call__(self, *args, **kwargs):
			key = self.instance, args, tuple(sorted(kwargs.items()))

			# check for expiration
			if key in self.cache_dates:
				if self.cache_dates[key] + self.timeout < time.time():
					# expired
					del self.cache[key]
					del self.cache_dates[key]
					return self(*args, **kwargs)
			else:
				self.cache_dates[key] = time.time() # new entry

			return super().__call__(*args, **kwargs)

	return functools.partial(_temporary_cachedmethod, timeout=timeout)

# cachedproperty taken from http://code.activestate.com/recipes/576563-cached-property/
# Licensed under MIT
# A cached property is a read-only property that is calculated on demand and automatically cached.
# If the value has already been calculated, the cached value is returned.


def cachedproperty(f):
	"""returns a cached property that is calculated by function f"""
	def get(self):
		try:
			return self._property_cache[f]
		except AttributeError:
			self._property_cache = {}
			x = self._property_cache[f] = f(self)
			return x
		except KeyError:
			x = self._property_cache[f] = f(self)
			return x

	return property(get)
