# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

class stablelist(object):
	def __init__(self, *values):
		self._free = []
		self._values = {}
		self._last = 0
		for v in values:
			self.append(v)

	def _getFreeKey(self):
		if len(self._free) > 0:
			return self._free.pop()
		else:
			self._last = self._last + 1
			return self._last
	
	def append(self, value):
		key = self._getFreeKey()
		self._values[key] = value
		return key

	def count(self):
		return len(self._values)

	def extend(self, *values):
		for v in values:
			self.append(v)

	def index(self, value):
		for k, v in self._values.items():
			if v == value:
				return k

	def pop(self, index = None):
		if index == None:
			index = self._last
		#index can be 0 if no item exists... -> error
		ret = self[index]
		del self[index]
		return ret

	def remove(self, value):
		del self[self.index(value)]

	def __add__(self, other):
		ret = stablelist(self)
		for v in other:
			ret.append(self)
		return ret

	def __contains__(self, value):
		try:
			return self.index(value) != 0
		except:
			return False

	def __delitem__(self, key):
		del self._values[key]
		if key == self._last:
			for i in xrange(key - 1, 0, -1):
				if i in self._values:
					self._last = i
					return
				else:
					self._free.remove(i)
			else:
				self._last = 0
		else:
			self._free.append(key)

	def __eq__(self, other):
		assert(other.__class__ == self.__class__)
		return self._values == other._values

	def __getitem__(self, key):
		return self._values[key]

	def __hash__(self):
		return hash(self._values)

	def __iadd__(self, other):
		ret = []
		for v in other:
			ret = ret + [self.append(v)]
		return ret

	def __iter__(self):
		return iter(self._values.values())

	def __len__(self):
		return len(self._values)

	def __ne__(self, other):
		return not (self == other)

	def __repr__(self):
		return repr(self._values)

	def __str__(self):
		return str(self._values)

	def __setitem__(self, key, value):
		if key not in self._values:
			if key in self._free:
				self._free.remove(key)
			else:
				for i in xrange(self._last + 1, key):
					self._free.append(i)
				self._last = key
		self._values[key] = value
