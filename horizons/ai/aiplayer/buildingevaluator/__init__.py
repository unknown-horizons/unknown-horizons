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

import copy

from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.entities import Entities
from horizons.util import WorldObject
from horizons.constants import RES

class BuildingEvaluator(WorldObject):
	def __init__(self, area_builder, builder, worldid=None):
		super(BuildingEvaluator, self).__init__(worldid)
		self.area_builder = area_builder
		self.builder = builder

	def __cmp__(self, other):
		if abs(self.value - other.value) > 1e-9:
			return 1 if self.value < other.value else -1
		return self.builder.worldid - other.builder.worldid

	@property
	def purpose(self):
		raise NotImplementedError, 'This function has to be overridden.'

	def execute(self):
		if not self.builder.have_resources():
			return (BUILD_RESULT.NEED_RESOURCES, None)
		if not self.area_builder._build_road_connection(self.builder):
			return (BUILD_RESULT.IMPOSSIBLE, None)
		building = self.builder.execute()
		if not building:
			return (BUILD_RESULT.UNKNOWN_ERROR, None)
		for coords in self.builder.position.tuple_iter():
			self.area_builder.plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
		self.area_builder.plan[sorted(self.builder.position.tuple_iter())[0]] = (self.purpose, self.builder)
		self.area_builder.production_buildings.append(building)
		return (BUILD_RESULT.OK, building)

decorators.bind_all(BuildingEvaluator)
