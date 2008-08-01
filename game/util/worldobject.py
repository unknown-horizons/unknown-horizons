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

import weakref
from changelistener import Changelistener

class WorldObject(Changelistener):
	__next_id = 1
	__objects = weakref.WeakValueDictionary()
	def __init__(self, **kwargs):
		super(WorldObject, self).__init__(**kwargs)

	def getId(self):
		if not hasattr(self, "_WorldObject__id"):
			self.__id = WorldObject.__next_id
			WorldObject.__next_id = WorldObject.__next_id + 1
			WorldObject.__objects[self.__id] = self
		return self.__id

	@classmethod
	def getObjectById(cls, id):
		return cls.__objects[id]

	@classmethod
	def reset(cls):
		cls.__next_id = 1
		cls.__objects.clear()
		
	def save(self, db):
		pass
