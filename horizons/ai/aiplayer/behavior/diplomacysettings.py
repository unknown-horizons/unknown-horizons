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


class DiplomacySettings:
	upper_boundary = 5.0

	class Evil:
		# negative weights favors opposite balance, e.g. enemy is stronger => higher relationship_score
		weights = {
			'power': -0.6,
			'wealth': -0.3,
			'terrain': -0.1,
		}

		parameters_hostile = {
			'neutral': {'mid': 0.0, 'root': 2.0, 'peek': 0.2}, # parabola with the center at 0.0, of root at 2.0 and -2.0. Peek at 0.5 (on Y axis)
			'ally': {'root': 7.0, },
		}
		parameters_neutral = {
			'enemy': {'root': -2.5, },
			'ally': {'root': 5.0, 'peek': 0.7, },
		}
		parameters_allied = {
			'neutral': {'mid': -2.0, 'root': -0.5, 'peek': 0.2, }, # parabola with the center at -2.0, of root at -0.5 (the other at -3.5). Peek at 0.2 (on Y axis)
			'enemy': {'root': -3.5, }, # smaller chance to go straight from allied to hostile
		}

	class Good:
		weights = {
			'power': 0.4,
			'terrain': 0.4,
			'wealth': 0.0,
		}

		parameters_hostile = {
			'neutral': {'mid': -2.0, 'root': -0.5, 'peek': 0.2, },
			'ally': {'root': 1.0, },
		}

		parameters_neutral = {
			'ally': {'root': 4.0, },
			'enemy': {'root': -6.7, 'peek': 0.4},
		}

		parameters_allied = {
			'neutral': {'mid': -3.0, 'root': -1.5, 'peek': 0.2, },
			'enemy': {'root': -8.0, },
		}

	class Neutral:
		weights = {
			'wealth': -0.8,
			'power': -0.1,
			'terrain': -0.1,
		}

		parameters_hostile = {
			'neutral': {'mid': 0.0, 'root': 2.0, 'peek': 0.3, },
			'ally': {'root': 4.0, },
		}

		parameters_neutral = {
			'ally': {'root': 5.0, },
			'enemy': {'root': -5.0, },
		}

		parameters_allied = {
			'neutral': {'mid': -1.0, 'root': 0.0, 'peek': 0.3, },
			'enemy': {'root': -7.0, },
		}
