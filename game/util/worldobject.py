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

class WorldObject(object):
	next_id = 1
	objects = []

	def getId(self):
		if not hasattr(self, "_WorldObject__id"):
			self.__id = WorldObject.next_id
			WorldObject.next_id = WorldObject.next_id + 1
			self.objects.append(self)
		return self.__id

	@classmethod
	def getObjectById(cls, id):
		return cls.objects[id-1]
