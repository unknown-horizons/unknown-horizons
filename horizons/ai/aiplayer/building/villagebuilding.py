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
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import RES, BUILDINGS
from horizons.util.python import decorators

class AbstractVillageBuilding(AbstractBuilding):
	@classmethod
	def get_purpose(cls, resource_id):
		if resource_id == RES.FAITH_ID:
			return BUILDING_PURPOSE.PAVILION
		elif resource_id == RES.EDUCATION_ID:
			return BUILDING_PURPOSE.VILLAGE_SCHOOL
		elif resource_id == RES.GET_TOGETHER_ID:
			return BUILDING_PURPOSE.TAVERN
		return None

	def build(self, settlement_manager, resource_id):
		village_builder = settlement_manager.village_builder
		building_purpose = self.get_purpose(resource_id)

		for coords, (purpose, builder) in village_builder.plan.iteritems():
			if purpose == building_purpose:
				object = village_builder.land_manager.island.ground_map[coords].object
				if object is None or object.id != self.id:
					if not builder.have_resources():
						return (BUILD_RESULT.NEED_RESOURCES, None)
					building = builder.execute()
					if not building:
						return (BUILD_RESULT.UNKNOWN_ERROR, None)
					return (BUILD_RESULT.OK, building)
		return (BUILD_RESULT.SKIP, None)

	@classmethod
	def register_buildings(cls):
		cls.available_buildings[BUILDINGS.PAVILION_CLASS] = cls
		cls.available_buildings[BUILDINGS.VILLAGE_SCHOOL_CLASS] = cls
		cls.available_buildings[BUILDINGS.TAVERN_CLASS] = cls

AbstractVillageBuilding.register_buildings()

decorators.bind_all(AbstractVillageBuilding)
