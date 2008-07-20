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
from game.world.units.carriage import BuildingCarriage
from game.util import Rect, Point
import game.main

class Consumer(object):
	"""Class used for buildings that need some resource

	Has to be inherited by a building that also inherits from producer
	This includes e.g. lumberjack, weaver, storages
	"""
	def __init__(self):
		"""
		"""
		self.consumation = {}
		result = game.main.db("SELECT rowid FROM production_line where building = ?", self.id);
		for (production_line,) in result:
			self.consumation[production_line] = []

			consumed_resources = game.main.db("select resource, storage_size from storage where rowid in (select storage from production where production_line = ? and amount <= 0);",production_line)
			for (res, size) in consumed_resources:
				if not self.inventory.hasSlot(res):
					self.inventory.addSlot(res, size)
				self.consumation[production_line].append(res)

		# calculate coords where carriage can move
		# workaround for BuildinglessProducer (TODO: find better solution)
		if self.x is not None and self.y is not None:
			self.building_coords = [ (x,y) for x in xrange(self.x, self.x+self.size[0]) for y in xrange(self.y, self.y+self.size[1]) ]
			building_rect = Rect(self.x, self.y, self.x+self.size[0]-1, self.y+self.size[1]-1)
			self.radius_coords = \
				[ (x,y) for x in xrange(self.x-self.radius, self.x+self.size[0]+self.radius+1) \
				for y in xrange(self.y-self.radius, self.y+self.size[1]+self.radius+1) \
				if ( building_rect.distance( Point(x,y) ) <= self.radius ) and \
				(x,y) not in self.building_coords ]

		self.create_carriage()

		self.__registered_collectors = []

	def create_carriage(self):
		""" Creates carriage according to building type (chosen by polymorphism)
		"""
		self.local_carriages.append(game.main.session.entities.units[2](self))

	def get_consumed_res(self):
		return self.consumation[self.active_production_line] if self.active_production_line != -1 else [];

	def get_needed_res(self):
		# get needed res
		return [res for res in self.get_consumed_res() if self.inventory.get_value(res) < self.inventory.get_size(res)]

