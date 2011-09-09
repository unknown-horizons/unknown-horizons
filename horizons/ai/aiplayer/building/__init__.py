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

import math
import logging

from horizons.ai.aiplayer.constants import BUILD_RESULT
from horizons.entities import Entities
from horizons.constants import GAME_SPEED, RES
from horizons.util.python import decorators
from horizons.world.production.productionline import ProductionLine

class AbstractBuilding(object):
	"""
	An object of this class tells the AI how to build a specific type of building.

	Instances of the subclasses are used by production chains to discover the set of
	buildings necessary to produce the right amount of resources.
	"""

	log = logging.getLogger("ai.aiplayer.building")

	def __init__(self, building_id, name, settler_level, production_line_ids):
		super(AbstractBuilding, self).__init__()
		self.id = building_id
		self.name = name
		self.settler_level = settler_level
		self.width = Entities.buildings[building_id].size[0]
		self.height = Entities.buildings[building_id].size[1]
		self.size = (self.width, self.height)
		self.radius = Entities.buildings[building_id].radius
		self.lines = {} # output_resource_id: ProductionLine
		if self.producer_building:
			for production_line_id in production_line_ids:
				production_line = ProductionLine(production_line_id)
				assert len(production_line.produced_res) == 1
				self.lines[production_line.produced_res.keys()[0]] = production_line

	__loaded = False
	buildings = {} # building_id: AbstractBuilding instance
	_available_buildings = {} # building_id: subclass of AbstractBuilding

	@classmethod
	def load_all(cls, db):
		"""Fill the cls.buildings dict so the registered buildings can be used."""
		if cls.__loaded:
			return

		for building_id, class_ref in cls._available_buildings.iteritems():
			cls.buildings[building_id] = class_ref.load(db, building_id)
		cls.__loaded = True

	@classmethod
	def _load_production_line_ids(cls, db, building_id):
		db_result = db("SELECT id FROM production_line WHERE object_id = ? AND enabled_by_default = 1", building_id)
		return [id for (id,) in db_result]

	@classmethod
	def _load_name(cls, db, building_id):
		return db("SELECT name FROM building WHERE id = ?", building_id)[0][0]

	@classmethod
	def _load_settler_level(cls, db, building_id):
		return db("SELECT settler_level FROM building WHERE id = ?", building_id)[0][0]

	@classmethod
	def load(cls, db, building_id):
		production_line_ids = cls._load_production_line_ids(db, building_id)
		name = cls._load_name(db, building_id)
		settler_level = cls._load_settler_level(db, building_id)
		return cls(building_id, name, settler_level, production_line_ids)

	monthly_gold_cost = 50
	resource_cost = {RES.GOLD_ID: 1, RES.BOARDS_ID: 20, RES.BRICKS_ID: 45, RES.TOOLS_ID: 50}

	def get_expected_building_cost(self):
		"""Return a value representing the utility cost of building the building."""
		total = 0
		for resource_id, amount in Entities.buildings[self.id].costs.iteritems():
			total += self.resource_cost[resource_id] * amount
		total += self.monthly_gold_cost * Entities.buildings[self.id].running_costs
		return total

	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		"""Return a value representing the utility cost of building enough buildings to produced the given amount of resource per tick."""
		buildings_needed = math.ceil(max(0.0, production_needed / self.get_expected_production_level(resource_id)))
		return buildings_needed * self.get_expected_building_cost()

	def get_expected_production_level(self, resource_id):
		"""Return the expected production capacity of a single building of this type producing the given resource."""
		if resource_id not in self.lines:
			return None
		line = self.lines[resource_id]
		return line.produced_res[resource_id] / line.time / GAME_SPEED.TICKS_PER_SECOND

	def get_production_level(self, building, resource_id):
		"""Return the actual production capacity of a single building of this type producing the given resource."""
		# most buildings can get away with reporting the expected production level
		return self.get_expected_production_level(resource_id)

	def have_resources(self, settlement_manager):
		"""Return a boolean showing whether the given settlement has enough resources to build a building of this type."""
		return Entities.buildings[self.id].have_resources([settlement_manager.land_manager.settlement], settlement_manager.owner)

	def iter_potential_locations(self, settlement_manager):
		"""Iterate over possible locations of the building in the given settlement in the form of (x, y, orientation)."""
		if self.width == self.height:
			for x, y in settlement_manager.production_builder.plan:
				if (x, y) in settlement_manager.island.last_changed[self.size]:
					yield (x, y, 0)
		else:
			for x, y in settlement_manager.production_builder.plan:
				if (x, y) in settlement_manager.island.last_changed[self.size]:
					yield (x, y, 0)
				if (x, y) in settlement_manager.island.last_changed[(self.size[1], self.size[0])]:
					yield (x, y, 1)

	@property
	def evaluator_class(self):
		"""Return the relevant BuildingEvaluator subclass."""
		raise NotImplementedError, 'This function has to be overridden.'

	@property
	def directly_buildable(self):
		"""Return a boolean showing whether the build function of this subclass can be used to build a building of this type."""
		return True

	@property
	def coverage_building(self):
		"""Return a boolean showing whether buildings of this type may need to be built even when the production capacity has been reached."""
		return False

	@property
	def ignore_production(self):
		"""Return a boolean showing whether instances of this building can be used to calculate the production capacity."""
		return False

	@property
	def producer_building(self):
		"""Return a boolean showing whether this building is supposed to have usable production lines."""
		return True

	def get_evaluators(self, settlement_manager, resource_id):
		"""Return a list of every BuildingEvaluator for this building type in the given settlement."""
		options = [] # [BuildingEvaluator, ...]
		for x, y, orientation in self.iter_potential_locations(settlement_manager):
			evaluator = self.evaluator_class.create(settlement_manager.production_builder, x, y, orientation)
			if evaluator is not None:
				options.append(evaluator)
		return options

	def build(self, settlement_manager, resource_id):
		"""Try to build the best possible instance of this building in the given settlement. Returns (BUILD_RESULT constant, building instance)."""
		if not self.have_resources(settlement_manager):
			return (BUILD_RESULT.NEED_RESOURCES, None)

		for evaluator in sorted(self.get_evaluators(settlement_manager, resource_id)):
			result = evaluator.execute()
			if result[0] != BUILD_RESULT.IMPOSSIBLE:
				return result
		self.log.debug('%s.build(%s, %d): no possible evaluators', self.__class__.__name__, settlement_manager, resource_id if resource_id else -1)
		return (BUILD_RESULT.IMPOSSIBLE, None)

	def need_to_build_more_buildings(self, settlement_manager, resource_id):
		"""Return a boolean showing whether another instance of the building should be built right now regardless of the production capacity."""
		return False

decorators.bind_all(AbstractBuilding)
