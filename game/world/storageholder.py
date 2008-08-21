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

from game.world.storage import Storage
import game.main

class StorageHolder(object):
	def __init__(self, **kwargs):
		super(StorageHolder, self).__init__(**kwargs)
		self.inventory = Storage()
		self.inventory.addChangeListener(self._changed)
		for (res, size) in game.main.db("select resource, size from data.storage where %(type)s = ?" % {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id):
			if not self.inventory.hasSlot(res):
				self.inventory.addSlot(res, size)

	def save(self, db):
		super(StorageHolder, self).save(db)
		self.inventory.save(db, self.getId())
