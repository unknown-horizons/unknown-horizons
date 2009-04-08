# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import weakref

import horizons.main

from changelistener import Changelistener

class WorldObject(Changelistener):
	__next_id = 1
	__objects = weakref.WeakValueDictionary()
	def __init__(self, **kwargs):
		super(WorldObject, self).__init__(**kwargs)

	def getId(self):
		if not hasattr(self, "_WorldObject__id"):
			assert WorldObject.__next_id not in WorldObject.__objects
			self.__id = WorldObject.__next_id
			WorldObject.__next_id = WorldObject.__next_id + 1
			WorldObject.__objects[self.__id] = self
		return self.__id

	@classmethod
	def get_object_by_id(cls, id):
		return cls.__objects[id]

	@classmethod
	def reset(cls):
		cls.__next_id = 1
		cls.__objects.clear()

	def save(self, db):
		pass

	def load(self, db, worldid):
		assert not hasattr(self, '_WorldObject__id')
		assert worldid not in WorldObject.__objects
		if horizons.main.debug:
			print 'loading worldobject', worldid, self

		self.__id = worldid
		WorldObject.__objects[worldid] = self

		# Make sure that new WorldIDs are always higher than every other WorldObject
		WorldObject.__next_id = max(self.__next_id, worldid + 1)

	# for testing:
	@classmethod
	def get_objs(self): return self.__objects
