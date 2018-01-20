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

from typing import Callable, Dict


class Registry:
	"""Simple implementation of the registry pattern.

	Example

		class Test(Registry):
			def register_function(self, func):
				self.registry[func.__name__] = func

		x = Test()

		@x.register()
		def foo(): pass

	The function foo can now be retrieved with

		x.get('foo')

	See the Scenario system or the unit tests for further usage examples.
	"""
	def __init__(self):
		self.registry = {} # type: Dict[str, Callable]

	def register(self, **kwargs):
		"""Returns a decorator to register functions, all arguments are passed through
		to `register_function`. You can use that to allow registeration under a different name
		for example.
		"""
		def deco(func):
			self.register_function(func, **kwargs)
			return func
		return deco

	def register_function(self, func: Callable, **kwargs):
		"""Function that actually handles the registration. You need to implement this
		yourself.

		For `get` to work, you want to add the function to the `registry` dictionary
		under the same name that will be used to look it up later.
		"""
		raise NotImplementedError

	def get(self, name: str) -> Callable:
		"""Retrieve a function given by `name` from the registry."""
		return self.registry[name]
