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
from horizons.util.random_map import generate_map_from_seed
from tests.game import game_test

def test_ai_quick():
	def generate_test(seed):
		return lambda : True
		# TODO: specifying kwargs is broken, the parameters will always stay as kwargs in future occurences of @game_test
		#@game_test(mapgen = partial(generate_map_from_seed, seed), human_player = False, ai_players = 2)
		def do_test(session, _):
			"""
			Let 2 AI players play for three minutes.
			(disabled due to time limit)
			"""
			#session.run(seconds = 180)
			#assert session.world.settlements
		return do_test

	for seed in xrange(1, 16):
		yield generate_test(seed)
