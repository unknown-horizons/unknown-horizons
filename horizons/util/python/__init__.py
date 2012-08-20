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
Put all code here that is not directly related to the game,
but rather a generic enhancement of the programming language.
"""

import decorators
from callback import Callback
from weaklist import WeakList
from weakmethod import WeakMethod
from weakmethodlist import WeakMethodList
from singleton import Singleton, ManualConstructionSingleton
from registry import Registry


class Const(object):
	"""An immutable type. Think C++-like const"""
	def __setattr__(self, name, value):
		"""Disallow changing an already set attribute, as an asymptote to const behaviour,
		which is not supported by python"""
		if name in self.__dict__:
			raise Exception("Can't change a ConstRect")
		super(Const, self).__setattr__(name, value)

def parse_port(port, allow_zero=False):
	"""str2int for network ports. Throws ValueError in case of error."""
	portInt = int(port)
	if allow_zero and portInt == 0:
		return portInt
	if portInt < 1 or portInt > 65535:
		raise ValueError()
	return portInt


def get_all_subclasses(cls):
	"""Recursivly find all subclasses of a given class."""
	result = set()
	for subclass in cls.__class__.__subclasses__(cls):
		if subclass not in result:
			result.add(subclass)
			result.update(get_all_subclasses(subclass))
	return result


def map_balance(value, n, m):
	"""
	Maps balance value defined in codomain of [1/n, n] for n >= 1, into linear balance (codomain of [-m, m]),
	having 1.0 as equal point for n-based balance, and 0.0 as equal point for linear balance.

	@param value: value to be mapped
	@type value: float
	@param n: fraction denominator
	@type n: float
	@param m: linear boundary
	@type m: float
	@return: value mapped into new balance type
	@rtype: float
	"""

	# normally we'd need to have special cases for value < 1.0 and value > 1.0
	# but we turn cases of 1/n into n instead
	if value < 1.0:
		value = 1./value
		m *= -1

	return ((value - 1.0) / (n - 1.0)) * m


def trim_value(value, min, max):
	if value < min:
		return min
	elif value > max:
		return max
	else:
		return value
