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

from horizons.constants import BUILDINGS, RES, GAME_SPEED
from horizons.world.production.productionline import ProductionLine

class VirtualBuilding(object):
	def __init__(self, session, building_id):
		self.id = building_id
		self.production_lines = []
		db_result = session.db("SELECT id FROM production_line WHERE object_id = ? AND enabled_by_default = 1", self.id)
		for production_line in db_result:
			self.production_lines.append(ProductionLine(production_line[0]))

class VirtualFarm(VirtualBuilding):
	def __init__(self, session):
		super(VirtualFarm, self).__init__(session, BUILDINGS.FARM_CLASS)

	def get_expected_production_level(self, resource_id, num_fields):
		# TODO: make this work for the other resources / different field types
		for production_line in self.production_lines:
			if resource_id not in production_line.produced_res:
				continue

			if resource_id == RES.FOOD_ID:
				amount = 0
				for sub_amount in production_line.produced_res.itervalues():
					amount += sub_amount
				return 0.0375 * num_fields * float(amount) / production_line.time / GAME_SPEED.TICKS_PER_SECOND
		return None

class VirtualFisher(VirtualBuilding):
	def __init__(self, session):
		super(VirtualFisher, self).__init__(session, BUILDINGS.FISHERMAN_CLASS)

	def get_expected_production_level(self, resource_id):
		# TODO: make this provide a more realistic expectation depending on the location
		if resource_id != RES.FOOD_ID:
			return None
		production_line = self.production_lines[0]
		amount = 0
		for sub_amount in production_line.produced_res.itervalues():
			amount += sub_amount
		return float(amount) / production_line.time / GAME_SPEED.TICKS_PER_SECOND

class VirtualClayPit(VirtualBuilding):
	def __init__(self, session):
		super(VirtualClayPit, self).__init__(session, BUILDINGS.CLAY_PIT_CLASS)

	def get_expected_production_level(self, resource_id):
		if resource_id != RES.CLAY_ID:
			return None
		production_line = self.production_lines[0]
		amount = 0
		for sub_amount in production_line.produced_res.itervalues():
			amount += sub_amount
		return float(amount) / production_line.time / GAME_SPEED.TICKS_PER_SECOND
