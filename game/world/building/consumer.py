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
from game.world.units.carriage import Carriage
import game.main

class Consumer(object):
	"""Class used for buildings that need some resource
	
	Has to be inherited by a building that also inherits from producer
	This includes e.g. lumberjack, weaver, storages
	"""
	def __init__(self):
		"""
		"""

		# for now:
		try: a = self.inited
		except:
			self.inited = True
			print 'CONSUMER FIRST INIT', self
		else:
			print "CONSUMER DOUBLE INIT ATTEMPT",self
			return
		
		self.consumation = {}
		result = game.main.db("SELECT rowid FROM production_line where building = ?", self.id);
		for (production_line,) in result:
			self.consumation[production_line] = []
			
			consumed_resources = game.main.db("select resource, storage_size from storage where rowid in (select resource from production where production_line = ? and amount <= 0);",production_line)
			for (res, size) in consumed_resources:
				self.inventory.addSlot(res, size)
				self.consumation[production_line].append(res)
			
		print 'ADDIN CAR FOR', self.id
		self.local_carriages.append(game.main.session.entities.units[2](6, self))
		
		
	def get_needed_resources(self):
		if self.active_production_line == -1:
			return []
		else:
			return self.consumation[self.active_production_line];
		
