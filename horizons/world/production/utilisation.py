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

from horizons.constants import PRODUCTION
from horizons.scheduler import Scheduler

class Utilisation(object):
	"""Basic utilisation class used in producers"""

	def capacity_utilisation(self, instance):
		productions = instance.get_productions()
		total = 0
		if not productions:
			return 0 # catch the border case, else there'll be a div by 0
		for production in productions:
			state_history = production.get_state_history_times(False)
			total += state_history[PRODUCTION.STATES.producing.index]
		return total / len(productions)

	def capacity_utilisation_below(self, limit, instance):
		"""Returns whether the capacity utilisation is below a value.
		It is equivalent to "foo.capacity_utilisation <= value, but faster."""
		# idea: retrieve the value, then check how long it has to take until the limit
		# can be reached (from both sides). Within this timespan, don't check again.
		cur_tick = Scheduler().cur_tick
		if not hasattr(self, "_old_capacity_utilisation") or \
		   self._old_capacity_utilisation[0] < cur_tick or \
		   self._old_capacity_utilisation[1] != limit:
			capac = self.capacity_utilisation(instance)
			diff = abs(limit - capac)
			# all those values are relative values, so we can just do this:
			interval = diff * PRODUCTION.STATISTICAL_WINDOW
			self._old_capacity_utilisation = (cur_tick + interval, # expiration date
						                      limit, capac < limit )
		return self._old_capacity_utilisation[2]

class FullUtilisation(Utilisation):
	"""Used for producers where no utilisation calculation is necessary"""

	def capacity_utilisation(self, instance):
		return 1.0


class FieldUtilisation(Utilisation):

	max_fields_possible = 8 # only for utilisation calculation

	def capacity_utilisation(self, instance):
		"""
		Calculate productivity by the number of fields nearby.
		"""

		result = float(len(instance.instance._get_providers())) / self.max_fields_possible
		# sanity checks for theoretically impossible cases:
		result = min(result, 1.0)
		result = max(result, 0.0)
		return result
