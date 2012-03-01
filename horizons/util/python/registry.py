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


class Registry(type):
	"""Simple implementation of the registry pattern.

	Example

		class Test(object):
			__metaclass__ = Registry

			@classmethod
			def register_function(cls, func):
				cls.registry[func.__name__] = func


		@Test.register()
		def foo(): pass

	The function foo can now be retrieved with

		Test.get('foo')

	See the Scenario system or the unit tests for further usage examples.
	"""
	def __init__(cls, name, bases, dict):
		setattr(cls, 'registry', {})

	def register(cls, **kwargs):
		"""Returns a decorator to register functions, all arguments are passed through
		to `register_function`. You can use that to allow registeration under a different name
		for example.
		"""
		def deco(func):
			cls.register_function(func, **kwargs)
			return func
		return deco

	def register_function(cls, func, **kwargs):
		"""Function that actually handles the registration. You need to implement this
		yourself.

		For `get` to work, you want to add the function to the `registry` dictionary
		under the same name that will be used to look it up later.
		"""
		raise NotImplementedError

	def get(cls, name):
		"""Retrieve a function given by `name` from the registry."""
		return cls.registry[name]
