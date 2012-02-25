# -*- coding: utf-8 -*-

# enum.py
# Part of enum, a package providing enumerated types for Python.
#
# Copyright © 2007 Ben Finney
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later
# or, at your option, the terms of the Python license.

"""Robust enumerated type support in Python

This package provides a module for robust enumerations in Python.

An enumeration object is created with a sequence of string arguments
to the Enum() constructor::

    >>> from enum import Enum
    >>> Colours = Enum('red', 'blue', 'green')
    >>> Weekdays = Enum('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')

The return value is an immutable sequence object with a value for each
of the string arguments. Each value is also available as an attribute
named from the corresponding string argument::

    >>> pizza_night = Weekdays[4]
    >>> shirt_colour = Colours.green

The values are constants that can be compared only with values from
the same enumeration; comparison with other values will invoke
Python's fallback comparisons::

    >>> pizza_night == Weekdays.fri
    True
    >>> shirt_colour > Colours.red
    True
    >>> shirt_colour == "green"
    False

Each value from an enumeration exports its sequence index
as an integer, and can be coerced to a simple string matching the
original arguments used to create the enumeration::

    >>> str(pizza_night)
    'fri'
    >>> shirt_colour.index
    2
"""

__author_name__ = "Ben Finney"
__author_email__ = "ben+python@benfinney.id.au"
__author__ = "%s <%s>" % (__author_name__, __author_email__)
__date__ = "2007-01-24"
__copyright__ = "Copyright © %s %s" % (
	__date__.split('-')[0], __author_name__
)
__license__ = "Choice of GPL or Python license"
__url__ = "http://cheeseshop.python.org/pypi/enum/"
__version__ = "0.4.3"


class EnumException(Exception):
	""" Base class for all exceptions in this module """
	def __init__(self):
		super(EnumException, self).__init__()
		if self.__class__ is EnumException:
			raise NotImplementedError("%s is an abstract class for subclassing" % self.__class__)

class EnumEmptyError(AssertionError, EnumException):
	""" Raised when attempting to create an empty enumeration """

	def __str__(self):
		return "Enumerations cannot be empty"

class EnumBadKeyError(TypeError, EnumException):
	""" Raised when creating an Enum with non-string keys """

	def __init__(self, key):
		self.key = key

	def __str__(self):
		return "Enumeration keys must be strings: %s" % (self.key,)

class EnumImmutableError(TypeError, EnumException):
	""" Raised when attempting to modify an Enum """

	def __init__(self, *args):
		self.args = args

	def __str__(self):
		return "Enumeration does not allow modification"


class EnumValue(object):
	""" A specific value of an enumerated type """

	def __init__(self, enumtype, index, key):
		""" Set up a new instance """
		self._enumtype = enumtype
		self._index = index
		self._key = key

	def _get_enumtype(self):
		return self._enumtype
	enumtype = property(_get_enumtype)

	def _get_key(self):
		return self._key
	key = property(_get_key)

	def __str__(self):
		return "%s" % (self.key)

	def _get_index(self):
		return self._index
	index = property(_get_index)

	def __repr__(self):
		return "EnumValue(%s, %s, %s)" % (
			repr(self._enumtype),
			repr(self._index),
			repr(self._key),
		)

	def __hash__(self):
		return hash(self._index)

	def __eq__(self, other):
		try:
			return self._enumtype == other._enumtype and self._index == other._index
		except AttributeError:
			return False

	def __cmp__(self, other):
		result = NotImplemented
		self_type = self.enumtype
		try:
			assert self_type == other.enumtype
			result = cmp(self.index, other.index)
		except (AssertionError, AttributeError):
			result = NotImplemented

		return result


class Enum(object):
	""" Enumerated type """

	def __init__(self, *keys, **kwargs):
		""" Create an enumeration instance """

		value_type = kwargs.get('value_type', EnumValue)

		if not keys:
			raise EnumEmptyError()

		keys = tuple(keys)
		values = [None] * len(keys)

		for i, key in enumerate(keys):
			value = value_type(self, i, key)
			values[i] = value
			try:
				super(Enum, self).__setattr__(key, value)
			except TypeError as e:
				raise EnumBadKeyError(key)

		super(Enum, self).__setattr__('_keys', keys)
		super(Enum, self).__setattr__('_values', values)

	@classmethod
	def get_extended(cls, base_enum, *keys, **kwargs):
		keys = base_enum._keys + keys
		return cls(*keys, **kwargs)

	def __setattr__(self, name, value):
		raise EnumImmutableError(name)

	def __delattr__(self, name):
		raise EnumImmutableError(name)

	def __len__(self):
		return len(self._values)

	def __getitem__(self, index):
		return self._values[index]

	def __setitem__(self, index, value):
		raise EnumImmutableError(index)

	def __delitem__(self, index):
		raise EnumImmutableError(index)

	def __iter__(self):
		return iter(self._values)

	def __contains__(self, value):
		is_member = False
		if isinstance(value, basestring):
			is_member = (value in self._keys)
		else:
			try:
				is_member = (value in self._values)
			except EnumValueCompareError as e:
				is_member = False
		return is_member

	def get_item_for_string(self, key):
		"""Get an enum value for a string
		@throws KeyError on key not found"""
		try:
			try:
				index =  self._keys.index(key)
			except AttributeError:
				# WORKAROUND: python 2.5 doesn't have tuple.index
				index = 0
				for i in self._keys:
					if i == key:
						break
					index += 1
				if index == len(self._keys): # not found
					raise ValueError
				# </WORKAROUND>

		except ValueError:
			raise KeyError # keyerror is more natural here, since the value is a key
		return self[index]

