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
from constants import BUILD_RESULT

from horizons.entities import Entities
from horizons.constants import BUILDINGS
from horizons.command.building import Build
from horizons.util.python import decorators
from horizons.util import Point, WorldObject

class ProductionChain:
	def __init__(self, settlement_manager, resource_id, chain):
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.chain = chain

	@classmethod
	def _get_chain(cls, settlement_manager, resource_id, resource_producer, production_ratio):
		""" Returns the first chain that can produce the given resource or None if it is impossible """
		if resource_id in resource_producer:
			for production_line, abstract_building in resource_producer[resource_id]:
				possible = True
				sources = []
				for consumed_resource, amount in production_line.consumed_res.iteritems():
					next_production_ratio = abs(production_ratio * amount / production_line.produced_res[resource_id])
					tail = cls._get_chain(settlement_manager, consumed_resource, resource_producer, next_production_ratio)
					if not tail:
						possible = False
						break
					sources.append(tail)
				if possible:
					return ProductionChainSubtree(settlement_manager, resource_id, production_line, abstract_building, sources, production_ratio)
		return None

	@classmethod
	def create(cls, settlement_manager, resource_id):
		"""Creates a production chain that can produce the given resource"""
		resource_producer = {}
		for abstract_building in AbstractBuilding.buildings.itervalues():
			for resource, production_line in abstract_building.lines.iteritems():
				if resource not in resource_producer:
					resource_producer[resource] = []
				resource_producer[resource].append((production_line, abstract_building))
		return ProductionChain(settlement_manager, resource_id, cls._get_chain(settlement_manager, resource_id, resource_producer, 1.0))

	def __str__(self):
		return 'ProductionChain(%d)\n%s' % (self.resource_id, self.chain)

	def build(self, amount):
		"""Builds a building that gets it closer to producing at least amount of resource per tick."""
		return self.chain.build(amount)

class ProductionChainSubtree:
	def __init__(self, settlement_manager, resource_id, production_line, abstract_building, children, production_ratio):
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.production_line = production_line
		self.abstract_building = abstract_building
		self.children = children
		self.production_ratio = production_ratio
		self.buildings = 0

	def __str__(self, level = 0):
		result = '%sProduce %d (ratio %.2f) in %s\n' % ('  ' * level, self.resource_id, self.production_ratio, self.abstract_building.name)
		for child in self.children:
			result += child.__str__(level + 1)
		return result

	def need_more_buildings(self, amount):
		production_level = self.abstract_building.get_expected_production_level(self.resource_id)
		if production_level is None:
			return False # building must be triggered by children instead
		production = self.buildings * production_level
		return amount * self.production_ratio > production + 1e-7

	def build(self, amount):
		result = None
		for child in self.children:
			result = child.build(amount)
			if result == BUILD_RESULT.ALL_BUILT:
				continue # build another child
			elif result == BUILD_RESULT.NEED_PARENT_FIRST:
				break # parent building has to be built before child (example: farm before field)
			elif result != BUILD_RESULT.OK:
				return result # error

		if result == BUILD_RESULT.NEED_PARENT_FIRST or self.need_more_buildings(amount):
			result = self.abstract_building.build(self.settlement_manager, self.resource_id)
			if result == BUILD_RESULT.OK:
				self.buildings += 1
			return result
		return BUILD_RESULT.ALL_BUILT

decorators.bind_all(ProductionChain)
decorators.bind_all(ProductionChainSubtree)
