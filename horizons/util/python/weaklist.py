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

# This file was stolen from http://home.gna.org/meals/ at 2008-07-24

"""
weaklist - list implementation that store objects with weakref
instead of strong ref
"""

import weakref

class _CopyDocFromParentClass(type):
	"""
    metaclass that copy, for a given class,
    all the docstring from their parents if there are not set
    """

	def __init__(cls, name, bases, dict):
		for name, method in dict.iteritems():
			try:
				if not method.__doc__:
					method.__doc__ = getattr(bases[0], name).__doc__
			except AttributeError:
				pass

class WeakList(list):
	"""
    A Weak_list can store objects but without keeping them
    alive with references couting incrementation.

    When objects are deleted or garbage_collected, they disappear from
    the list.

    ! WARNING: due to the *magic* deletion of item, some method here
    are not guaranteed to give the right result or even to work properly.

    This class is NOT thread safe and NOT GC safe.

    You can have problem with:

    - extend can add broken weakref in the list
    - sort can crash
    - __iter__, __str__, __repr__ and __reversed can return some None
    - all the rich comparison method
    - count can return wrong values or outdated
    - index can return too high values or forget to raise exceptions
    - __get_item__ and __set_item__ are useless

    Be also careful that your work with weakref, so some usual
    tips don't work:

    >>> weak = weaklist.WeakList(weakable_class())
    >>> len(a)
    0

    """

	# This copy all the list's doctstring into this class's method
	# So even if the class look undocumented, it is ! (use pydoc)
	__metaclass__ = _CopyDocFromParentClass


	## Basic custom

	def __init__(self, items=None):
		if items:
			list.__init__(self, self.__iter_over_weakref(items))
		else:
			list.__init__(self)

	def __str__(self):
		return '[' + ', '.join((repr(i) for i in self)) + ']'

	def __repr__(self):
		return 'Weak_list((' + ', '.join((repr(i) for i in self)) + '))'


	## Special method

	def __new_weakref(self, item):
		"""Create a weakref with the good callback"""
		return weakref.ref(item, self.__remove_ref)

	def __iter_over_weakref(self, iterable):
		"""For a given iterable, return an iterable generator over all weakref"""
		return (self.__new_weakref(i) for i in iterable)

	def __remove_ref(self, ref):
		"""
        When an object from the list is destroy, this
        method is call to remove it from list
        """

		list.remove(self, ref)


	## list method

	def extend(self, iterable):
		iterable = self.__iter_over_weakref(list(iterable))
		list.extend(self, iterable)

	def append(self, obj):
		list.append(self, weakref.ref(obj, self.__remove_ref))

	def remove(self, obj):
		list.remove(self, weakref.ref(obj))

	def count(self, value):
		return list.count(self, weakref.ref(value))

	def index(self, value, *args):
		return list.index(self, weakref.ref(value), *args)

	def pop(self, index=-1):
		return list.pop(self, index)()

	def sort(self, cmp=None, key=None, reverse=False):
		sortable = list(self)
		sortable.sort(cmp, key, reverse)
		del self[:]
		self.extend(sortable)

	def insert(self, index, obj):
		list.insert(self, index, self.__new_weakref(obj))


	## Emulating container types

	def __getitem__(self, index):
		return list.__getitem__(self, index)()

	def __setitem__(self, index, value):
		if isinstance(index, slice):
			list.__setitem__(self, index, self.__iter_over_weakref(value))
		else:
			list.__setitem__(self, index, self.__new_weakref(value))

	def __iter__(self):
		for i in list.__iter__(self):
			yield i()

	def __contains__(self, item):
		return list.__contains__(self, weakref.ref(item))

	def __getslice__(self, i, j):
		return WeakList(list(self)[i:j])

	def __setslice__(self, i, j, iterable):
		list.__setslice__(self, i, j, self.__iter_over_weakref(iterable))

	def __reversed__(self):
		return iter([i() for i in list.__reversed__(self)])


	## Emulating numeric types

	def __iadd__(self, other):
		self.extend(other)
		return self

	def __add__(self, other):
		return self.__class__(list(self) + list(other))


	## Rich comparison

	def __eq__(self, other):
		if isinstance(other, WeakList):
			other = list(other)
		return list.__eq__(list(self), other)

	def __ge__(self, other):
		if isinstance(other, WeakList):
			other = list(other)
		return list.__ge__(list(self), other)

	def __le__(self, other):
		if isinstance(other, WeakList):
			other = list(other)

		return list.__le__(list(self), other)

	def __gt__(self, other):
		if isinstance(other, WeakList):
			other = list(other)

		return list.__gt__(list(self), other)

	def __ne__(self, other):
		if isinstance(other, WeakList):
			other = list(other)

		return list.__ne__(list(self), other)

	def __lt__(self, other):
		if isinstance(other, WeakList):
			other = list(other)

		return list.__lt__(list(self), other)

### End of WeakList class
