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

	def __init__(self, area_builder, builder, new_unused_field_purpose):
		super(ModifiedFieldEvaluator, self).__init__(area_builder, builder)
		self.builder = builder
		self.new_unused_field_purpose = new_unused_field_purpose
		self.fields = 1 # required for comparison with FarmEvalutor-s

		self.value = 0
		personality = area_builder.owner.personality_manager.get('ModifiedFieldEvaluator')
		if new_unused_field_purpose == BUILDING_PURPOSE.UNUSED_POTATO_FIELD:
			self.value += personality.add_unused_potato_field_value
		elif new_unused_field_purpose == BUILDING_PURPOSE.UNUSED_PASTURE:
			self.value += personality.add_unused_pasture_value
		elif new_unused_field_purpose == BUILDING_PURPOSE.UNUSED_SUGARCANE_FIELD:
			self.value += personality.add_unused_sugarcane_field_value

		self.old_unused_field_purpose = area_builder.plan[builder.point.to_tuple()][0]
		if self.old_unused_field_purpose == BUILDING_PURPOSE.UNUSED_POTATO_FIELD:
			self.value -= personality.remove_unused_potato_field_penalty
		elif self.old_unused_field_purpose == BUILDING_PURPOSE.UNUSED_PASTURE:
			self.value -= personality.remove_unused_pasture_penalty
		elif self.old_unused_field_purpose == BUILDING_PURPOSE.UNUSED_SUGARCANE_FIELD:
			self.value -= personality.remove_unused_sugarcane_field_penalty

	@classmethod
	def create(cls, area_builder, x, y, new_unused_field_purpose):
		building_id = None
		if new_unused_field_purpose == BUILDING_PURPOSE.UNUSED_POTATO_FIELD:
			building_id = BUILDINGS.POTATO_FIELD_CLASS
		elif new_unused_field_purpose == BUILDING_PURPOSE.UNUSED_PASTURE:
			building_id = BUILDINGS.PASTURE_CLASS
		elif new_unused_field_purpose == BUILDING_PURPOSE.UNUSED_SUGARCANE_FIELD:
			building_id = BUILDINGS.SUGARCANE_FIELD_CLASS
		builder = Builder.create(building_id, area_builder.land_manager, Point(x, y))
		if not builder:
			return None
		return ModifiedFieldEvaluator(area_builder, builder, new_unused_field_purpose)

	def execute(self):
		if not self.builder.have_resources():
			return (BUILD_RESULT.NEED_RESOURCES, None)

		building = self.builder.execute()
		if not building:
			self.log.debug('%s, unknown error', self)
			return (BUILD_RESULT.UNKNOWN_ERROR, None)

		# remove the old designation
		self.area_builder.unused_fields[BUILDING_PURPOSE.get_used_purpose(self.old_unused_field_purpose)].remove(self.builder.point.to_tuple())

		for x, y in self.builder.position.tuple_iter():
			self.area_builder.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
		self.area_builder.register_change(self.builder.position.origin.x, self.builder.position.origin.y, \
			BUILDING_PURPOSE.get_used_purpose(self.new_unused_field_purpose), self.builder)
		self.area_builder.display()
		return (BUILD_RESULT.OK, building)

decorators.bind_all(ModifiedFieldEvaluator)
