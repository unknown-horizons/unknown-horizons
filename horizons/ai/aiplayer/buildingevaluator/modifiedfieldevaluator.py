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
from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.util.python import decorators
from horizons.constants import BUILDINGS
from horizons.util import Point

class ModifiedFieldEvaluator(BuildingEvaluator):
	""" This evaluator evaluates the cost of changing the type of an unused field """

	def __init__(self, area_builder, builder, new_field_purpose):
		super(ModifiedFieldEvaluator, self).__init__(area_builder, builder)
		self.builder = builder
		self.new_field_purpose = new_field_purpose
		self.fields = 1 # required for comparison with FarmEvalutor-s

		self.value = 0
		personality = area_builder.owner.personality_manager.get('ModifiedFieldEvaluator')
		if new_field_purpose == BUILDING_PURPOSE.POTATO_FIELD:
			self.value += personality.add_potato_field_value
		elif new_field_purpose == BUILDING_PURPOSE.PASTURE:
			self.value += personality.add_pasture_value
		elif new_field_purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
			self.value += personality.add_sugarcane_field_value

		self.old_field_purpose = area_builder.plan[builder.point.to_tuple()][0]
		if self.old_field_purpose == BUILDING_PURPOSE.POTATO_FIELD:
			self.value -= personality.remove_unused_potato_field_penalty
		elif self.old_field_purpose == BUILDING_PURPOSE.PASTURE:
			self.value -= personality.remove_unused_pasture_penalty
		elif self.old_field_purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
			self.value -= personality.remove_unused_sugarcane_field_penalty

	@classmethod
	def create(cls, area_builder, x, y, new_field_purpose):
		building_id = None
		if new_field_purpose == BUILDING_PURPOSE.POTATO_FIELD:
			building_id = BUILDINGS.POTATO_FIELD_CLASS
		elif new_field_purpose == BUILDING_PURPOSE.PASTURE:
			building_id = BUILDINGS.PASTURE_CLASS
		elif new_field_purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
			building_id = BUILDINGS.SUGARCANE_FIELD_CLASS
		builder = Builder.create(building_id, area_builder.land_manager, Point(x, y))
		if not builder:
			return None
		return ModifiedFieldEvaluator(area_builder, builder, new_field_purpose)

	def execute(self):
		if not self.builder.have_resources():
			return (BUILD_RESULT.NEED_RESOURCES, None)

		building = self.builder.execute()
		if not building:
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)

		# remove the old designation
		self.area_builder.unused_fields[self.old_field_purpose].remove(self.builder.point.to_tuple())

		return (BUILD_RESULT.OK, building)

decorators.bind_all(ModifiedFieldEvaluator)
