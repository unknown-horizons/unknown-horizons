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

from horizons.constants import SETTLER

class IngameType(type):

	def action_sets_by_level(self, action_sets):
		as_by_level = {}
		for i in xrange(0, SETTLER.CURRENT_MAX_INCR+1):
			as_by_level[i] = []
			for setname, value in action_sets.iteritems():
				if 'level' in value and value['level'] == i:
					as_by_level[i].append(setname)
				elif 'level' not in value and i == 0:
					as_by_level[i] = setname
		return as_by_level
