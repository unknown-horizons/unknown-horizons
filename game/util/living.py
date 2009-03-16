# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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

class livingProperty(object):
	def __init__(self):
		self.__value = None

	def __get__(self, obj, cls=None):
		return self.__value

	def __set__(self, obj, value):
		#print "Setting:", obj, value
		#print "Value:", self.__value
		if hasattr(self.__value, 'end'):
			self.__value.end()
		self.__value = value

	def __delete__(self, obj):
		self.__set__(obj, None)

	def __del__(self):
		self.__value = None

class LivingObject(object):
	"""This class is intended to be used with the livingProperty to ensure all variables
	are safely deinited when intended by the programmer. The livingProperty calls the
	livingObject's end() function to deinit the object. This mostly replacing the __del__
	function, as it's behaviour is not well behaved."""

	def end(self):
		"""Put all the code the object needs to end safely here. Make sure it always
		contains the super(YOUROBJECT, self).end() call, to ensure all parentobjects are
		deinited correctly."""
		pass

