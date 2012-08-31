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

"""
DefaultWeakKeyDictionary - Works as a regular WeakKeyDictionary but supports default values.
Note: Default feature works slightly different than collections.defaultdict

Usage:

>>> d = DefaultWeakKeyDictionary(lambda key: key*2)
>>> d['foo'] = 4
>>> print d['foo']
4
>>> print d['bar']
'barbar'
"""
from weakref import WeakKeyDictionary

class DefaultWeakKeyDictionary(WeakKeyDictionary):
	"""
	WeakKeyDictionary with specified default value.
	"""
	def __init__(self, default_function):
		WeakKeyDictionary.__init__(self)
		assert default_function is not None, "Default function must be provided"
		self.default_function = default_function

	def __getitem__(self, item):
		if item not in self.items():
			return self.default_function(item)
		return WeakKeyDictionary.__getitem__(self, item)
