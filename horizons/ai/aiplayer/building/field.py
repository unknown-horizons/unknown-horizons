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

from horizons.ai.aiplayer.builder import Builder
from horizons.ai.aiplayer.building import AbstractBuilding
from horizons.ai.aiplayer.constants import BUILD_RESULT, PRODUCTION_PURPOSE
from horizons.constants import RES, BUILDINGS
from horizons.util import Point
from horizons.util.python import decorators

class AbstractField(AbstractBuilding):
	@classmethod
	def get_purpose(cls, resource_id):
		if resource_id == RES.POTATOES_ID:
			return PRODUCTION_PURPOSE.POTATO_FIELD
		elif resource_id == RES.LAMB_WOOL_ID:
			return PRODUCTION_PURPOSE.PASTURE
		elif resource_id == RES.RAW_SUGAR_ID:
			return PRODUCTION_PURPOSE.SUGARCANE_FIELD
		return None

	def build(self, settlement_manager, resource_id):
		production_builder = settlement_manager.production_builder
		purpose = self.get_purpose(resource_id)
		if not production_builder.unused_fields[purpose]:
			return BUILD_RESULT.NEED_PARENT_FIRST
		if not self.have_resources(settlement_manager):
			return BUILD_RESULT.NEED_RESOURCES

		assert len(production_builder.unused_fields[purpose]) > 0, 'expected field spot to be available'
		coords = production_builder.unused_fields[purpose][0]
		builder = Builder.create(self.id, settlement_manager.land_manager, Point(coords[0], coords[1]))
		if not builder.execute():
			return BUILD_RESULT.UNKNOWN_ERROR
		production_builder.unused_fields[purpose].popleft()
		production_builder.plan[coords] = (purpose, builder)
		settlement_manager.num_fields[purpose] += 1
		return BUILD_RESULT.OK

	@classmethod
	def register_buildings(cls):
		cls.available_buildings[BUILDINGS.POTATO_FIELD_CLASS] = cls
		cls.available_buildings[BUILDINGS.PASTURE_CLASS] = cls
		cls.available_buildings[BUILDINGS.SUGARCANE_FIELD_CLASS] = cls

AbstractField.register_buildings()

decorators.bind_all(AbstractField)
