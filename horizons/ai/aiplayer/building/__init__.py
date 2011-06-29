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
from horizons.constants import BUILDINGS, GAME_SPEED, RES
from horizons.util.python import decorators
from horizons.world.production.productionline import ProductionLine

class AbstractBuilding(object):
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
		for production_line_id in production_line_ids:
			production_line = ProductionLine(production_line_id)
			assert len(production_line.produced_res) == 1
			self.lines[production_line.produced_res.keys()[0]] = production_line

	loaded = False
	buildings = {} # building_id: AbstractBuilding
	available_buildings = {} # building_id: subclass of AbstractBuilding

	@classmethod
	def load_all(cls, db):
		if cls.loaded:
			return

		for building_id, class_ref in cls.available_buildings.iteritems():
			cls.buildings[building_id] = class_ref.load(db, building_id)
		cls.loaded = True

	@classmethod
	def load_production_line_ids(cls, db, building_id):
		db_result = db("SELECT id FROM production_line WHERE object_id = ? AND enabled_by_default = 1", building_id)
		return [id for (id,) in db_result]
	
	@classmethod
	def load_name(cls, db, building_id):
		return db("SELECT name FROM building WHERE id = ?", building_id)[0][0]

	@classmethod
	def load_settler_level(cls, db, building_id):
		return db("SELECT settler_level FROM building WHERE id = ?", building_id)[0][0]

	@classmethod
	def load(cls, db, building_id):
		production_line_ids = cls.load_production_line_ids(db, building_id)
		name = cls.load_name(db, building_id)
		settler_level = cls.load_settler_level(db, building_id)
		return cls(building_id, name, settler_level, production_line_ids)

	def _get_costs(self):
		return Entities.buildings[self.id].costs

	def _get_running_cost(self):
		return Entities.buildings[self.id].running_costs

	monthly_gold_cost = 50
	resource_cost = {RES.GOLD_ID: 1, RES.BOARDS_ID: 20, RES.BRICKS_ID: 45, RES.TOOLS_ID: 50}

	def get_expected_building_cost(self):
		total = 0
		for resource_id, amount in self._get_costs().iteritems():
			total += self.resource_cost[resource_id] * amount
		total += self.monthly_gold_cost * self._get_running_cost()
		return total

	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		extra_buildings_needed = math.ceil(max(0.0, production_needed / self.get_expected_production_level(resource_id)))
		return extra_buildings_needed * self.get_expected_building_cost()

	def get_expected_production_level(self, resource_id):
		if resource_id not in self.lines:
			return None
		line = self.lines[resource_id]
		return line.produced_res[resource_id] / line.time / GAME_SPEED.TICKS_PER_SECOND

	def get_production_level(self, building, resource_id):
		""" Most buildings can get away with reporting the expected production level """
		return self.get_expected_production_level(resource_id)

	def have_resources(self, settlement_manager):
		return Entities.buildings[self.id].have_resources([settlement_manager.land_manager.settlement], settlement_manager.owner)

	def iter_potential_locations(self, settlement_manager):
		if self.width == self.height:
			for (x, y) in settlement_manager.production_builder.plan:
				if (x, y) in settlement_manager.island.last_changed[self.size]:
					yield (x, y, 0)
		else:
			for (x, y) in settlement_manager.production_builder.plan:
				if (x, y) in settlement_manager.island.last_changed[self.size]:
					yield (x, y, 0)
				if (x, y) in settlement_manager.island.last_changed[(self.size[1], self.size[0])]:
					yield (x, y, 1)

	@property
	def evaluator_class(self):
		raise NotImplementedError, 'This function has to be overridden.'

	@property
	def directly_buildable(self):
		""" A building is directly buildable if it doesn't need to be placed next to its children """
		return True

	@property
	def coverage_building(self):
		""" pavilions, schools, and taverns are buildings that need to be built even if the total production is enough """
		return False

	@property
	def ignore_production(self):
		""" Child buildings that should not be used for production calculation set this to true """
		return False

	def get_evaluators(self, settlement_manager, resource_id):
		options = []
		for x, y, orientation in self.iter_potential_locations(settlement_manager):
			evaluator = self.evaluator_class.create(settlement_manager.production_builder, x, y, orientation)
			if evaluator is not None:
				options.append(evaluator)
		return options

	def build(self, settlement_manager, resource_id):
		if not self.have_resources(settlement_manager):
			return (BUILD_RESULT.NEED_RESOURCES, None)

		for evaluator in sorted(self.get_evaluators(settlement_manager, resource_id)):
			result = evaluator.execute()
			if result[0] != BUILD_RESULT.IMPOSSIBLE:
				return result
		self.log.debug('%s.build(%s, %d): no possible evaluators', self.__class__.__name__, settlement_manager, resource_id)
		return (BUILD_RESULT.IMPOSSIBLE, None)

decorators.bind_all(AbstractBuilding)
