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

import logging

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.constants import BUILD_RESULT
from horizons.constants import RES
from horizons.util.python import decorators

class ProductionChain(object):
	"""
	A production chain handles the building of buildings required to produce a resource.

	Production chains use the list of production lines and the available AbstractBuilding
	subclasses to figure out all ways of producing a certain resource and finding the
	right ratio of them to produce just enough of the resource. The result is a tree
	that can be used to produce the required resource.

	Each subtree reserves a portion of the total capacity of the buildings of the relevant
	type. This is a logical classification and doesn't affect the actual buildings in any way.
	Some subtrees can import the required resource from other islands using a mechanism
	similar to the previous one but in that case it acts as if the resource was produced
	without any subtrees. The imported amounts are added up over time and saved as an owed
	resource in the exporting settlement's resource manager (these restrictions are again
	just logical without affecting the way the settlements work in any way). That storage
	is realised by organising DomesticTrade missions that transfer the resources to the
	right settlements.
	"""

	log = logging.getLogger("ai.aiplayer.productionchain")

	def __init__(self, settlement_manager, resource_id, resource_producer):
		super(ProductionChain, self).__init__()
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.chain = self._get_chain(resource_id, resource_producer, 1.0)
		self.chain.assign_identifier('/%d,%d' % (self.settlement_manager.worldid, self.resource_id))

	def _get_chain(self, resource_id, resource_producer, production_ratio):
		"""Return a ProductionChainSubtreeChoice if it is possible to produce the resource, None otherwise."""
		options = []
		if resource_id in resource_producer:
			for production_line, abstract_building in resource_producer[resource_id]:
				possible = True
				sources = []
				for consumed_resource, amount in production_line.consumed_res.iteritems():
					next_production_ratio = abs(production_ratio * amount / production_line.produced_res[resource_id])
					subtree = self._get_chain(consumed_resource, resource_producer, next_production_ratio)
					if not subtree:
						possible = False
						break
					sources.append(subtree)
				if possible:
					options.append(ProductionChainSubtree(self.settlement_manager, resource_id, production_line, abstract_building, sources, production_ratio))
		if not options:
			return None
		return ProductionChainSubtreeChoice(options)

	@classmethod
	def create(cls, settlement_manager, resource_id):
		"""Create a production chain that can produce the given resource."""
		resource_producer = {}
		for abstract_building in AbstractBuilding.buildings.itervalues():
			for resource, production_line in abstract_building.lines.iteritems():
				if resource not in resource_producer:
					resource_producer[resource] = []
				resource_producer[resource].append((production_line, abstract_building))
		return ProductionChain(settlement_manager, resource_id, resource_producer)

	def __str__(self):
		return 'ProductionChain(%d): %.5f\n%s' % (self.resource_id, self.get_final_production_level(), self.chain)

	def build(self, amount):
		"""Build a building that gets it closer to producing at least the given amount of resource per tick."""
		return self.chain.build(amount)

	def reserve(self, amount, may_import):
		"""Reserve currently available production capacity and import from other islands if allowed."""
		return self.chain.reserve(amount, may_import)

	def need_to_build_more_buildings(self, amount):
		"""Return a boolean showing whether more buildings need to be built in order to produce at least amount of resource per tick."""
		return self.chain.need_to_build_more_buildings(amount)

	def get_final_production_level(self):
		"""Return the production level per tick at the bottleneck."""
		return self.chain.get_final_production_level()

	def get_ratio(self, resource_id):
		"""Return the ratio of the given resource needed given that 1 unit of the root resource is required."""
		return self.chain.get_ratio(resource_id)

class ProductionChainSubtreeChoice(object):
	"""An object of this class represents a choice between N >= 1 ways of producing the required resource."""

	log = logging.getLogger("ai.aiplayer.productionchain")
	coverage_resources = set([RES.COMMUNITY, RES.FAITH, RES.EDUCATION, RES.GET_TOGETHER])

	def __init__(self, options):
		super(ProductionChainSubtreeChoice, self).__init__()
		self.options = options # [ProductionChainSubtree, ...]
		self.resource_id = options[0].resource_id # the required resource
		self.production_ratio = options[0].production_ratio # given that 1 unit has to be produced at the root of the tree, how much has to be produced here?
		self.ignore_production = options[0].ignore_production # whether to try to build more buildings even when the required production capacity has been reached
		self.trade_manager = options[0].trade_manager # TradeManager instance
		self.settlement_manager = options[0].settlement_manager # SettlementManager instance

	def assign_identifier(self, prefix):
		"""Recursively assign an identifier to this subtree to know which subtree owns which resource quota."""
		self.identifier = prefix + ('/choice' if len(self.options) > 1 else '')
		for option in self.options:
			option.assign_identifier(self.identifier)

	def __str__(self, level=0):
		result = '%sChoice between %d options: %.5f\n' % ('  ' * level, len(self.options), self.get_final_production_level())
		for option in self.options:
			result += option.__str__(level + 1)
		if self.get_root_import_level() > 1e-9:
			result += '\n%sImport %.5f' % ('  ' * (level + 1), self.get_root_import_level())
		return result

	def get_root_import_level(self):
		"""Return the amount of the resource imported per tick."""
		return self.trade_manager.get_quota(self.identifier, self.resource_id) / self.production_ratio

	def get_final_production_level(self):
		"""Return the total reserved production capacity of the resource per tick (includes import)."""
		return sum(option.get_final_production_level() for option in self.options) + self.get_root_import_level()

	def get_expected_cost(self, amount):
		"""Return the expected utility cost of building enough buildings to produce a total of the given amount of the resource per tick."""
		return min(option.get_expected_cost(amount) for option in self.options)

	def _get_available_options(self):
		"""Return a list of the currently available options to produce the resource."""
		available_options = []
		for option in self.options:
			if option.available:
				available_options.append(option)
		return available_options

	def build(self, amount):
		"""Try to build a building in the subtree that is currently the cheapest. Return a BUILD_RESULT constant."""
		current_production = self.get_final_production_level()
		if amount < current_production + 1e-7 and self.resource_id not in self.coverage_resources:
			# we are already producing enough
			return BUILD_RESULT.ALL_BUILT

		available_options = self._get_available_options()
		if not available_options:
			self.log.debug('%s: no available options', self)
			return BUILD_RESULT.IMPOSSIBLE
		elif len(available_options) == 1:
			return available_options[0].build(amount)

		# need to increase production: build the cheapest subtree
		expected_costs = []
		for i in xrange(len(available_options)):
			option = available_options[i]
			cost = option.get_expected_cost(amount - current_production + option.get_final_production_level())
			if cost is not None:
				expected_costs.append((cost, i, option))

		if not expected_costs:
			self.log.debug('%s: no possible options', self)
			return BUILD_RESULT.IMPOSSIBLE
		else:
			for option in zip(*sorted(expected_costs))[2]:
				result = option.build(amount) # TODO: this amount should not include the part provided by the other options
				if result != BUILD_RESULT.IMPOSSIBLE:
					return result
			return BUILD_RESULT.IMPOSSIBLE

	def reserve(self, amount, may_import):
		"""Reserve currently available production capacity and import from other islands if allowed. Returns the total amount it can reserve or import."""
		total_reserved = 0.0
		for option in self._get_available_options():
			total_reserved += option.reserve(max(0.0, amount - total_reserved), may_import)

		# check how much we can import
		if may_import:
			required_amount = max(0.0, amount - total_reserved)
			self.trade_manager.request_quota_change(self.identifier, self.resource_id, required_amount * self.production_ratio)
			total_reserved += self.get_root_import_level()

		return total_reserved

	def need_to_build_more_buildings(self, amount):
		"""Return a boolean showing whether more buildings need to be built in order to produce at least the given amount of resource per tick."""
		current_production = self.get_final_production_level()
		if self.resource_id not in self.coverage_resources:
			return current_production + 1e-7 <= amount
		for option in self._get_available_options():
			if option.need_to_build_more_buildings(amount):
				return True
		return False

	def get_ratio(self, resource_id):
		"""Return the ratio of the given resource needed given that 1 unit of the root resource is required."""
		return sum(option.get_ratio(resource_id) for option in self.options)

class ProductionChainSubtree(object):
	"""An object of this type represents a subtree of buildings that need to be built in order to produce the given resource."""

	def __init__(self, settlement_manager, resource_id, production_line, abstract_building, children, production_ratio):
		super(ProductionChainSubtree, self).__init__()
		self.settlement_manager = settlement_manager # SettlementManager instance
		self.resource_manager = settlement_manager.resource_manager # ResourceManager instance
		self.trade_manager = settlement_manager.trade_manager # TradeManager instance
		self.resource_id = resource_id # the required resource
		self.production_line = production_line # ProductionLine instance
		self.abstract_building = abstract_building # AbstractBuilding instance
		self.children = children # [ProductionChainSubtreeChoice, ...]
		self.production_ratio = production_ratio # given that 1 unit has to be produced at the root of the tree, how much has to be produced here?
		self.ignore_production = abstract_building.ignore_production # whether to try to build more buildings even when the required production capacity has been reached

	def assign_identifier(self, prefix):
		"""Recursively assign an identifier to this subtree to know which subtree owns which resource quota."""
		self.identifier = '%s/%d,%d' % (prefix, self.resource_id, self.abstract_building.id)
		for child in self.children:
			child.assign_identifier(self.identifier)

	@property
	def available(self):
		"""Return a boolean showing whether this subtree is currently available."""
		return self.settlement_manager.owner.settler_level >= self.abstract_building.settler_level

	def __str__(self, level=0):
		result = '%sProduce %d (ratio %.2f) in %s (%.5f, %.5f)\n' % ('  ' * level, self.resource_id,
			self.production_ratio, self.abstract_building.name, self.get_root_production_level(), self.get_final_production_level())
		for child in self.children:
			result += child.__str__(level + 1)
		return result

	def get_expected_children_cost(self, amount):
		"""Return the expected utility cost of building enough buildings in the subtrees to produce a total of the given amount of the resource per tick."""
		total = 0
		for child in self.children:
			cost = child.get_expected_cost(amount)
			if cost is None:
				return None
			total += cost
		return total

	def get_expected_cost(self, amount):
		"""Return the expected utility cost of building enough buildings to produce a total of the given amount of the resource per tick."""
		children_cost = self.get_expected_children_cost(amount)
		if children_cost is None:
			return None

		production_needed = (amount - self.get_root_production_level()) * self.production_ratio
		root_cost = self.abstract_building.get_expected_cost(self.resource_id, production_needed, self.settlement_manager)
		if root_cost is None:
			return None
		return children_cost + root_cost

	def get_root_production_level(self):
		"""Return the currently reserved production capacity of this subtree at the root."""
		return self.resource_manager.get_quota(self.identifier, self.resource_id, self.abstract_building.id) / self.production_ratio

	def get_final_production_level(self):
		"""Return the currently reserved production capacity at the bottleneck."""
		min_child_production = None
		for child in self.children:
			if child.ignore_production:
				continue
			production_level = child.get_final_production_level()
			if min_child_production is None:
				min_child_production = production_level
			else:
				min_child_production = min(min_child_production, production_level)
		if min_child_production is None:
			return self.get_root_production_level()
		else:
			return min(min_child_production, self.get_root_production_level())

	def need_more_buildings(self, amount):
		"""Return a boolean showing whether more buildings of this specific type need to be built in order to produce at least the given amount of resource per tick."""
		if not self.abstract_building.directly_buildable:
			return False # building must be triggered by children instead
		if self.abstract_building.coverage_building:
			return True
		return amount > self.get_root_production_level() + 1e-7

	def build(self, amount):
		"""Build a building in order to get closer to the goal of producing at least the given amount of resource per tick at the bottleneck."""
		# try to build one of the lower level buildings (results in a depth first order)
		result = None
		for child in self.children:
			result = child.build(amount)
			if result == BUILD_RESULT.ALL_BUILT:
				continue # build another child or build this building
			elif result == BUILD_RESULT.NEED_PARENT_FIRST:
				break # parent building has to be built before child (example: farm before field)
			else:
				return result # an error or successful building

		if result == BUILD_RESULT.NEED_PARENT_FIRST or self.need_more_buildings(amount):
			# build a building
			(result, building) = self.abstract_building.build(self.settlement_manager, self.resource_id)
			if result == BUILD_RESULT.OUT_OF_SETTLEMENT:
				return self.settlement_manager.production_builder.extend_settlement(building)
			return result
		return BUILD_RESULT.ALL_BUILT

	def reserve(self, amount, may_import):
		"""Reserve currently available production capacity and import from other islands if allowed. Returns the total amount it can reserve or import."""
		total_reserved = amount
		for child in self.children:
			total_reserved = min(total_reserved, child.reserve(amount, may_import))

		self.resource_manager.request_quota_change(self.identifier, True, self.resource_id, self.abstract_building.id, amount * self.production_ratio)
		total_reserved = min(total_reserved, self.resource_manager.get_quota(self.identifier, self.resource_id, self.abstract_building.id) / self.production_ratio)
		return total_reserved

	def need_to_build_more_buildings(self, amount):
		"""Return a boolean showing whether more buildings in this subtree need to be built in order to produce at least the given amount of resource per tick."""
		for child in self.children:
			if child.need_to_build_more_buildings(amount):
				return True
		if not self.need_more_buildings(amount):
			return False
		return self.abstract_building.need_to_build_more_buildings(self.settlement_manager, self.resource_id)

	def get_ratio(self, resource_id):
		"""Return the ratio of the given resource needed given that 1 unit of the root resource is required."""
		result = self.production_ratio if self.resource_id == resource_id else 0
		return result + sum(child.get_ratio(resource_id) for child in self.children)

decorators.bind_all(ProductionChain)
decorators.bind_all(ProductionChainSubtreeChoice)
decorators.bind_all(ProductionChainSubtree)
