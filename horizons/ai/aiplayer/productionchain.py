# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from building import AbstractBuilding

from horizons.entities import Entities
from horizons.constants import BUILDINGS
from horizons.command.building import Build
from horizons.util.python import decorators
from horizons.util import Point, WorldObject

class ProductionChain:
	def __init__(self, resource_id, chain):
		self.resource_id = resource_id
		self.chain = chain

	@classmethod
	def _get_chain(cls, resource_id, resource_producer):
		""" Returns the first chain that can produce the given resource or None if it is impossible """
		if resource_id in resource_producer:
			for production_line, abstract_building in resource_producer[resource_id]:
				possible = True
				sources = []
				for consumed_resource in production_line.consumed_res:
					tail = cls._get_chain(consumed_resource, resource_producer)
					if not tail:
						possible = False
						break
					sources.append(tail)
				if possible:
					return ProductionChainSubtree(resource_id, production_line, abstract_building, sources)
		return None

	@classmethod
	def create(cls, resource_id):
		"""Creates a production chain that can produce the given resource"""

		resource_producer = {}
		for abstract_building in AbstractBuilding.buildings.itervalues():
			for resource, production_line in abstract_building.lines.iteritems():
				if resource not in resource_producer:
					resource_producer[resource] = []
				resource_producer[resource].append((production_line, abstract_building))
		return ProductionChain(resource_id, cls._get_chain(resource_id, resource_producer))

	def __str__(self):
		return 'ProductionChain(%d)\n%s' % (self.resource_id, self.chain)

class ProductionChainSubtree:
	def __init__(self, resource_id, production_line, abstract_building, children):
		self.resource_id = resource_id
		self.production_line = production_line
		self.abstract_building = abstract_building
		self.children = children

	def __str__(self, level = 0):
		result = '%sProduce %d in %s\n' % ('  ' * level, self.resource_id, self.abstract_building.name)
		for child in self.children:
			result += child.__str__(level + 1)
		return result

decorators.bind_all(ProductionChain)
decorators.bind_all(ProductionChainSubtree)
