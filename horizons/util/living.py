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

from typing import Any, Optional


class livingProperty:
	"""livingProperty's are used to assign properties to a class, similar to python properties.
	The extra benefit with livingPropertys is, that they will call the previously assigned
	instances' end() function one being replaced. Note that all classes that are assigned
	to a livingProperty should subclass the LivingObject class, to ensure the existence of
	the end() method.
	The main purpose of the livingProperty is to ensure the correct deletion of objects,
	so Classes that derive from the LivingObject class will usually have all their __del__
	code in the end() method, to ensure it gets called upon being overwritten, even if
	other references to it exist (which should not!).
	Here is a small example on the usage:

	class Livetest:
	    prop1 = new livingProperty()

	    def __init__(self):
	        prop1 = new TestObj()
			prop1 = new Test2Obj() // TestObj().end() is called
			prop1 = new TestObj()  // Testobj2().end() is called

	class TestObj(LivingProperty):
	    def end():
		    print "TestObj end"

	class Testobj2(LivingProperty):
	    def end():
		    print "TestObj2 end"

	This would result in the following output:
	TestObj end
	TestObj2 end
	"""

	def __init__(self):
		self.__value = None # type: Optional[Any]

	def __get__(self, obj, cls=None):
		return self.__value

	def __set__(self, obj, value):
		if hasattr(self.__value, 'end'):
			self.__value.end()
		self.__value = value

	def __delete__(self, obj):
		self.__set__(obj, None)


class LivingObject:
	"""This class is intended to be used with the livingProperty to ensure all variables
	are safely deinited when intended by the programmer. The livingProperty calls the
	livingObject's end() function to deinit the object. This mostly replacing the __del__
	function, as its behavior is not well behaved."""

	def end(self):
		"""Put all the code the object needs to end safely here. Make sure it always
		contains the super(YOUROBJECT, self).end() call, to ensure all parentobjects are
		deinited correctly."""
		pass
