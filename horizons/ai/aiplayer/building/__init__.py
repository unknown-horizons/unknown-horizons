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

from horizons.ai.aiplayer.constants import BUILD_RESULT
from horizons.entities import Entities
from horizons.constants import BUILDINGS, GAME_SPEED
from horizons.util.python import decorators
from horizons.world.production.productionline import ProductionLine

class AbstractBuilding:
	def __init__(self, building_id, name, production_line_ids):
		self.id = building_id
		self.name = name
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
	def load(cls, db, building_id):
		production_line_ids = cls.load_production_line_ids(db, building_id)
		name = cls.load_name(db, building_id)
		return cls(building_id, name, production_line_ids)

	def get_expected_production_level(self, resource_id):
		if resource_id not in self.lines:
			return None
		line = self.lines[resource_id]
		return line.produced_res[resource_id] / line.time / GAME_SPEED.TICKS_PER_SECOND

	def have_resources(self, settlement_manager):
		return Entities.buildings[self.id].have_resources([settlement_manager.land_manager.settlement], settlement_manager.owner)

	def iter_potential_locations(self, settlement_manager):
		for (x, y) in settlement_manager.production_builder.plan:
			yield (x, y, 0)

	@property
	def evaluator_class(self):
		raise NotImplementedError, 'This function has to be overridden.'

	def build(self, settlement_manager, resource_id):
		if not self.have_resources(settlement_manager):
			return BUILD_RESULT.NEED_RESOURCES

		options = []
		for x, y, orientation in self.iter_potential_locations(settlement_manager):
			evaluator = self.evaluator_class.create(settlement_manager.production_builder, x, y, orientation)
			if evaluator is not None:
				options.append(evaluator)

		for evaluator in sorted(options):
			return evaluator.execute()
		return BUILD_RESULT.IMPOSSIBLE

decorators.bind_all(AbstractBuilding)
