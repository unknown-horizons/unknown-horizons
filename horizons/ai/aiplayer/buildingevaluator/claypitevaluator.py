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

from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS, RES

class ClayPitEvaluator(BuildingEvaluator):
	def __init__(self, production_builder, builder):
		super(ClayPitEvaluator, self).__init__(production_builder, builder)
		self.value = 0
		self.production_level = None

	def get_expected_production_level(self, resource_id):
		assert resource_id == RES.CLAY_ID
		return self.production_builder.owner.virtual_clay_pit.get_expected_production_level(resource_id)

	@classmethod
	def create(cls, production_builder, x, y):
		builder = production_builder.make_builder(BUILDINGS.CLAY_PIT_CLASS, x, y, True)
		if not builder:
			return None
		return ClayPitEvaluator(production_builder, builder)

	def execute(self):
		if not self.production_builder.have_resources(self.builder.building_id):
			return BUILD_RESULT.NEED_RESOURCES
		if not self.production_builder._build_road_connection(self.builder):
			return BUILD_RESULT.IMPOSSIBLE
		building = self.builder.execute()
		if not building:
			return BUILD_RESULT.UNKNOWN_ERROR
		for coords in self.builder.position.tuple_iter():
			self.production_builder.plan[coords] = (PRODUCTION_PURPOSE.RESERVED, None)
		self.production_builder.plan[sorted(self.builder.position.tuple_iter())[0]] = (PRODUCTION_PURPOSE.CLAY_PIT, self.builder)
		self.production_builder.production_buildings.append(building)
		return BUILD_RESULT.OK

decorators.bind_all(ClayPitEvaluator)
