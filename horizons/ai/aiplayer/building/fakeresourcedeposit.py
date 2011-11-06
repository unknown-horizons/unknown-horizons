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

from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.world.production.productionline import ProductionLine
from horizons.util.python import decorators

class AbstractFakeResourceDeposit(AbstractBuilding):
	def __init__(self, building_id, name, settler_level, production_line_ids):
		super(AbstractFakeResourceDeposit, self).__init__(building_id, name, settler_level, [])
		self.lines = {} # output_resource_id: ProductionLine
		assert len(production_line_ids) == 1, 'expected exactly 1 production line'
		for production_line_id in production_line_ids:
			# create a fake production line that is similar to the higher level building one
			# TODO: use a better way of producing fake ProductionLine-s
			production_line = ProductionLine(production_line_id)
			production_line.id = None
			production_line.production = {}
			production_line.produced_res = {}
			for resource_id, amount in production_line.consumed_res.iteritems():
				production_line.production[resource_id] = -amount
				production_line.produced_res[resource_id] = -amount
			production_line.consumed_res = {}
			self.lines[production_line.produced_res.keys()[0]] = production_line

	@classmethod
	def get_higher_level_building_id(cls):
		raise NotImplementedError, 'This function has to be overridden.'

	@classmethod
	def load(cls, db, building_id):
		# load the higher level building data because resource deposits don't actually produce anything
		production_line_ids = cls._load_production_line_ids(db, cls.get_higher_level_building_id())
		name = cls._load_name(db, building_id)
		settler_level = cls._load_settler_level(db, building_id)
		return cls(building_id, name, settler_level, production_line_ids)

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

decorators.bind_all(AbstractFakeResourceDeposit)
