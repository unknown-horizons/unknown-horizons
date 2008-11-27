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

from game.world.storage import SizedSlotStorage
import game.main

class StorageHolder(object):
	def __init__(self, **kwargs):
		super(StorageHolder, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		self.inventory = SizedSlotStorage(30)
		self.inventory.addChangeListener(self._changed)

	def save(self, db):
		super(StorageHolder, self).save(db)
		self.inventory.save(db, self.getId())

	def load(self, db, worldid):
		super(StorageHolder, self).load(db, worldid)
		self.__init()
		self.inventory.load(db, worldid)