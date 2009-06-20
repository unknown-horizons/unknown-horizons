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

import horizons.main

from horizons.util import WeakList
from storageholder import StorageHolder

class AbstractConsumer(StorageHolder):
	"""The AbstractConsumer represents things that consume resources, as buildings and settlers.
	This AbstractConsumer does not offer any automatic loading from the database or
	productionlines. In order to use the AbstractConsumer you have add the needed resources
	by hand. See the Consumer or Settler class for an implementation.


	TUTORIAL: You should now check out the Consumer(consumer.py) class to see how a real
	implementation of this class works.
	"""

	def __init__(self, **kwargs):
		super(AbstractConsumer, self).__init__(**kwargs)
		self.__init()
		self.create_collector()


	def __init(self):
		"""Part of initiation that __init__() and load() share"""
		self._resources = {} # dict of productionline ids as keys and resources as values

		# list of local collectors that holds the collectors that belong to this building.
		self.local_collectors = []

		# In case the class derived from this class is a Building, set it's radius
		from horizons.world.building.building import Building
		if isinstance(self, Building):
			self.radius_coords = self.position.get_radius_coordinates(self.radius)

		self.__collectors = WeakList()


	def create_collector(self):
		""" Creates collector according to building type (chosen by polymorphism)
		"""
		horizons.main.session.entities.units[2](self)

	def get_needed_res(self):
		"""Returns list of resources, where free space in the inventory exists,
		because a building doesn't need resources, that it can't store
		"""
		return [res for res in self.get_consumed_res() if self.inventory[res] < self.inventory.limit]

	def get_consumed_res(self):
		"""Returns list of resource ids, that the building uses, without
		considering, if it currently needs them
		"""
		raise NotImplementedError, "This function has to be overidden"

	def save(self, db):
		super(AbstractConsumer, self).save(db)
		for collector in self.local_collectors:
			collector.save(db)

	def load(self, db, worldid):
		super(AbstractConsumer, self).load(db, worldid)
		self.__init()
