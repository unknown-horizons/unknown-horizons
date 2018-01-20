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

from horizons.ai.aiplayer.constants import GOAL_RESULT
from horizons.ai.aiplayer.goal import Goal


class DoNothingGoal(Goal):
	"""This goal makes the AI not do anything during a tick."""

	def get_personality_name(self):
		return 'DoNothingGoal'

	@property
	def priority(self):
		return self._priority

	@property
	def active(self):
		return super().active and self._is_active

	def update(self):
		""" whether to do nothing and if so then how important it is """
		if self.owner.session.random.random() >= self.personality.likelihood:
			# don't be lazy
			self._is_active = False
			self._priority = 0
		else:
			# be lazy
			self._is_active = True
			self._priority = self.owner.session.random.gauss(self.personality.default_priority, self.personality.priority_variance)

	def execute(self):
		# do nothing
		return GOAL_RESULT.BLOCK_ALL_BUILDING_ACTIONS
