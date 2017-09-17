# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.entities import Entities
from horizons.world.production.producer import Producer
from horizons.world.production.productionline import ProductionLine


class AbstractFakeResourceDeposit(AbstractBuilding):
	def __init__(self, building_id, name, settler_level):
		super().__init__(building_id, name, settler_level)
		self.lines = {} # output_resource_id: ProductionLine
		self.__init_production_lines()

	@classmethod
	def get_higher_level_building_id(cls):
		raise NotImplementedError('This function has to be overridden.')

	def __init_production_lines(self):
		production_lines = self._get_producer_building().get_component_template(Producer)['productionlines']
		for key, value in production_lines.items():
			production_line = ProductionLine(key, value)
			production_line.id = None
			production_line.production = {}
			production_line.produced_res = {}
			for resource_id, amount in production_line.consumed_res.items():
				production_line.production[resource_id] = -amount
				production_line.produced_res[resource_id] = -amount
			production_line.consumed_res = {}
			self.lines[list(production_line.produced_res.keys())[0]] = production_line

	def _get_producer_building(self):
		return Entities.buildings[self.get_higher_level_building_id()]

	@classmethod
	def load(cls, db, building_id):
		# load the higher level building data because resource deposits don't actually produce anything
		name = cls._load_name(db, building_id)
		settler_level = cls._load_settler_level(building_id)
		return cls(building_id, name, settler_level)

	def get_expected_cost(self, resource_id, production_needed, settlement_manager):
		""" you don't actually build resource deposits """
		return 0

	@property
	def directly_buildable(self):
		""" You don't actually build resource deposits """
		return False

	@property
	def ignore_production(self):
		return True
