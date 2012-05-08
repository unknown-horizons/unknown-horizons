# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from horizons.ai.aiplayer.goal.improvecollectorcoverage import ImproveCollectorCoverageGoal
from horizons.util.python import decorators
from horizons.constants import RES
from horizons.component.storagecomponent import StorageComponent

class StorageSpaceGoal(ImproveCollectorCoverageGoal):
	def get_personality_name(self):
		return 'StorageSpaceGoal'

	def _need_more_storage(self):
		limit = self.settlement.get_component(StorageComponent).inventory.get_limit(RES.FOOD)
		if limit >= self.personality.max_required_storage_space:
			return False
		important_resources = [RES.FOOD, RES.TEXTILE, RES.LIQUOR]
		for resource_id in important_resources:
			if self.settlement.get_component(StorageComponent).inventory[resource_id] + self.personality.full_storage_threshold >= limit:
				return True
		return False

	def update(self):
		if self._need_more_storage():
			super(StorageSpaceGoal, self).update()
			if not self._is_active:
				self._is_active = True
				self._problematic_buildings = self.production_builder.production_buildings
		else:
			self._is_active = False

	def execute(self):
		result = self._build_extra_storage()
		self._log_generic_build_result(result, 'storage space provider')
		return self._translate_build_result(result)

decorators.bind_all(StorageSpaceGoal)
