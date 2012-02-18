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

from functools import partial
from horizons.util.random_map import generate_map_from_seed
from tests.game import game_test

def test_ai_long():
	for seed in [1, 2, 3, 4]:
		yield run_ai_long, seed

def run_ai_long(seed):
	@game_test(mapgen = partial(generate_map_from_seed, seed), human_player = False, ai_players = 2, timeout = 1800)
	def test(session, _):
		"""Let 2 AI players play for 40 minutes."""
		session.run(seconds = 2400)
		assert session.world.settlements

	test()

# this disables the test in general and only makes it being run when
# called like this: run_tests.py -a long
test_ai_long.long = True
