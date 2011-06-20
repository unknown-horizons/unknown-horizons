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

from horizons.entities import Entities
from horizons.constants import BUILDINGS
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

	@classmethod
	def load_all(cls, db):
		if cls.loaded:
			return

		class_id = {
			BUILDINGS.WEAVER_CLASS: AbstractBuilding,
			BUILDINGS.FARM_CLASS: AbstractBuilding,
			BUILDINGS.PASTURE_CLASS: AbstractBuilding,
			BUILDINGS.POTATO_FIELD_CLASS: AbstractBuilding,
			BUILDINGS.SUGARCANE_FIELD_CLASS: AbstractBuilding,
			BUILDINGS.DISTILLERY_CLASS: AbstractBuilding,
			BUILDINGS.TAVERN_CLASS: AbstractBuilding,
		}

		for building_id, class_ref in class_id.iteritems():
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
		return AbstractBuilding(building_id, name, production_line_ids)

decorators.bind_all(AbstractBuilding)
