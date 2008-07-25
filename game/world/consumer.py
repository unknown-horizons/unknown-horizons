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
from game.world.storageholder import StorageHolder
from game.world.units.carriage import BuildingCarriage
from game.util import Rect, Point, WeakList
import game.main

class Consumer(StorageHolder):
	"""Class used for buildings that need some resource

	Has to be inherited by a building that also inherits from producer
	This includes e.g. lumberjack, weaver, storages
	"""
	def __init__(self, **kwargs):
		"""
		"""
		super(Consumer, self).__init__(**kwargs)
		self.consumation = {}


		if self.object_type == 0:
			#print self.id, "Consumer: IS A BUILDING"
			pass

		elif self.object_type == 1:
			#print self.id, "Consumer: IS A UNIT"
			pass
		else:
			print self.id, "Consumer: UNKNOWN TYPE"
			assert(False)

		result = game.main.db("SELECT rowid FROM data.production_line where %(type)s = ?" % {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id);
		for (production_line,) in result:
			self.consumation[production_line] = []

			consumed_resources = game.main.db("select resource, size from data.storage where %(type)s = ? and resource in (select resource from data.production p left join data.production_line l on p.production_line = l.rowid where l.%(type)s = ?);" % {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id, self.id)
			for (res, size) in consumed_resources:
				self.consumation[production_line].append(res)

		if len(self.consumation) == 0:
			self.active_production_line = -1
		else:
			self.active_production_line = min(self.consumation.keys())
		print 'production line:', self.active_production_line
		
		# calculate coords where carriage can move
		if isinstance(self, Building):
			self.radius_coords = self.building_position.get_radius_coordinates(self.radius)

		self.__registered_collectors = WeakList()

		self.create_carriage()

	def create_carriage(self):
		""" Creates carriage according to building type (chosen by polymorphism)
		"""
		self.local_carriages.append(game.main.session.entities.units[2](self))

	def get_needed_res(self):
		"""Returns list of resources, where free space in the inventory exists,
		because a building doesn't need resources, that it can't store"""
		return [res for res in self.get_consumed_res() if self.inventory.get_value(res) < self.inventory.get_size(res)]

	def get_consumed_res(self):
		"""Returns list of resources, that the building uses, without
		considering, if it currently needs them"""

		return self.consumation[self.active_production_line] if self.active_production_line != -1 else [];
