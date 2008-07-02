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

from building import Building
from game.world.storage import Storage
import game.main

class Consumer(Storage):
	"""Class used for buildings that need some resource
	
	Has to be inherited by a building
	This includes e.g. lumberjack, weaver, storages
	"""
	def __init__(self):
		"""
		"""
		super(Consumer, self).__init__()
		self.consumed_res = []
		consumed_resources = game.main.db("SELECT resource, storage_size FROM consumation WHERE building = ?", self.id)
		for (res, size) in consumed_resources:
			self.addSlot(res, size)
			self.consumed_res.append(res)