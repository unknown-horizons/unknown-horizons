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

from functools import partial
from horizons.util.random_map import generate_map
from tests.game import game_test

def test_ai_long():
	def generate_test(seed):
		@game_test(mapgen = partial(generate_map, seed), is_ai = True)
		def do_test(session, player):
			"""
			Let the AI play alone for 1 hour.
			"""
			session.run(seconds = 3600)
			assert session.world.settlements
		return do_test

	# 1: a single island
	# 2: many very small islands
	# 3: 2 large, 2 small islands
	# 4: a variety of small and large islands
	for seed in [1, 2, 3, 4]:
		yield generate_test(seed)
