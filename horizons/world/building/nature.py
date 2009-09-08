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

from building import BasicBuilding
from buildable import BuildableRect
from collectingbuilding import CollectingBuilding
from horizons.world.production.producer import ProducerBuilding
from horizons.world.building.collectingproducerbuilding import CollectingProducerBuilding
from horizons.constants import LAYERS

import horizons.main


class GrowingBuilding(ProducerBuilding, BuildableRect, BasicBuilding):
	""" Class for stuff that grows, such as trees
	"""
	walkable = True

	def __init__(self, **kwargs):
		super(GrowingBuilding, self).__init__(**kwargs)

	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = LAYERS.GROUND
		return super(GrowingBuilding, cls).getInstance(*args, **kwargs)

class Field(GrowingBuilding):
	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = LAYERS.OBJECTS
		return super(GrowingBuilding, cls).getInstance(*args, **kwargs)

class AnimalField(CollectingBuilding, Field):
	def create_collector(self):
		self.animals = []

		for (animal, number) in horizons.main.db("SELECT unit_id, count FROM data.animals \
		                                    WHERE building_id = ?", self.id):
			for i in xrange(0, number):
				Entities.units[animal](self)

		super(AnimalField, self).create_collector()

	def remove(self):
		while len(self.animals) > 0:
			self.animals[0].cancel()
			self.animals[0].remove()

class Tree(GrowingBuilding):
	buildable_upon = True
	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = LAYERS.OBJECTS
		return super(GrowingBuilding, cls).getInstance(*args, **kwargs)
