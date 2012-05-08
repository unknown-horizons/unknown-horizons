# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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


from horizons.util.pathfinding.pathnodes import ConsumerBuildingPathNodes
from horizons import entities
from horizons.component import Component

class CollectingComponent(Component):
	"""The CollectingBuilding class represents a object that uses collectors
	to collect resources from other ResourceHolder objects. It is used to
	organize Collector instances.
	NOTE: Anything inheriting from this class must also inherit from the
	Building class.

	Base class for most producing/collecting buildings.
	"""

	NAME = 'CollectingComponent'

	## INIT/DESTRUCT
	def __init__(self, collectors):
		super(CollectingComponent, self).__init__()
		self.__collector_templates = collectors

	def initialize(self):
		self.__init()
		self.create_collector(self.__collector_templates)

	def __init(self):
		"""Part of initiation that __init__() and load() share"""
		# list that holds the collectors that belong to this building.
		self.__collectors = []

		self.path_nodes = ConsumerBuildingPathNodes(self.instance)

	def create_collector(self, collectors):
		"""Creates collectors for building according to db."""
		for collector_class, count in collectors.iteritems():
			for i in xrange(0, count):
				self.add_collector(collector_class)

	def add_collector(self, collector_class):
		"""Creates a collector and adds it to this building.
		@param collector_class: unit class of collector to create
		"""
		collector = entities.Entities.units[collector_class](self.instance, session=self.session, owner=self.instance.owner)
		collector.initialize()


	def remove(self):
		# remove every non-ship collectors (those are independent)
		for collector in self.__collectors[:]:
			if not collector.is_ship:
				collector.remove()
			else:
				collector.decouple_from_home_building()
		assert len([c for c in self.__collectors]) == 0
		super(CollectingComponent, self).remove()
		self.__collectors = None
		self.path_nodes = None

	def save(self, db):
		super(CollectingComponent, self).save(db)
		for collector in self.__collectors:
			# collectors, that are ship (e.g. fisher ship) are viewed as independent
			# units, and therefore managed by world. This is justified, since they survive
			# the removal of their assigned fisher hut, and therefore require their own
			# saving mechanism
			if not collector.is_ship:
				collector.save(db)


	def load(self, db, worldid):
		super(CollectingComponent, self).load(db, worldid)
		self.__init()


	## INTERFACE
	def add_local_collector(self, collector):
		assert collector not in self.__collectors
		self.__collectors.append(collector)

	def remove_local_collector(self, collector):
		self.__collectors.remove(collector)

	def get_local_collectors(self):
		return self.__collectors
