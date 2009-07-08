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

from building import Building
from buildable import BuildableRect
from horizons.world.production import PrimaryProduction

class GrowingBuilding(PrimaryProduction, BuildableRect, Building):
	""" Class for stuff that grows, such as trees
	"""
	part_of_nature = True
	walkable = True

	def __init__(self, **kwargs):
		super(GrowingBuilding, self).__init__(**kwargs)
		self.inventory.limit = 1 # this should be done by database query later on

	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = 1
		return super(GrowingBuilding, cls).getInstance(*args, **kwargs)

class Tree(GrowingBuilding):
	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = 2
		return super(GrowingBuilding, cls).getInstance(*args, **kwargs)

	def _can_produce(self):
		"""This function checks whether the producer is ready to start production.
		Can be overriden to implement buildingspecific behaviour.
		"""
		enough_room = False # used to check if there is enough room to produce at least one item
		for res, amount in self.production[self.active_production_line].production.items():
			if amount > 0 and self.inventory[res] + amount <= self.inventory.get_limit(res):
				enough_room = True
		return enough_room


