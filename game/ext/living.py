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

class livingProperty(object):
	def __init__(self):
		self.values = {}

	def __get__(self, obj, cls=None):
		return self.values.get(obj, None)

	def __set__(self, obj, value):
		if obj in self.values and hasattr(self.values[obj], 'end'):
			self.values[obj].end()
		if value == None:
			del self.values[obj]
		else:
			self.values[obj] = value
			if hasattr(value, 'begin'):
				value.begin()

	def __del__(self, obj):
		self.__set__(obj, None)

class livingObject(object):
	def begin(self):
		pass

	def end(self):
		self._is_ended = True

	def __del__(self):
		if not self._is_ended:
			print "Warning: Object is not ended but no reference is left."
