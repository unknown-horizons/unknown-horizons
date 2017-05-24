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

import pytest

from horizons.util.python.registry import Registry


def test_simple():
	class Example(Registry):
		def register_function(self, func):
			self.registry[func.__name__] = func

	instance = Example()
	with pytest.raises(KeyError):
		instance.get('foo')

	@instance.register()
	def foo(a, b):
		return a + b

	assert instance.get('foo') == foo


def test_with_arguments():
	"""Test arguments in the register decorator."""
	class Example(Registry):
		def register_function(self, func, name):
			self.registry[name] = func

	instance = Example()
	with pytest.raises(KeyError):
		instance.get('foo')

	@instance.register(name='bar')
	def foo(a, b):
		return a + b

	with pytest.raises(KeyError):
		instance.get('foo')

	assert instance.get('bar') == foo
