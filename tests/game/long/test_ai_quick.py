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
from horizons.command.building import Tear
from horizons.constants import BUILDINGS
from horizons.util.worldobject import WorldObject, WorldObjectNotFound

def test_ai_quick():
	for seed in xrange(1, 16):
		yield run_ai_quick, seed

def run_ai_quick(seed):
	@game_test(mapgen=partial(generate_map_from_seed, seed), human_player=False, ai_players=2, timeout=120)
	def test(session, _):
		"""Let 2 AI players play for four minutes."""
		session.run(seconds = 4 * 60)
		assert session.world.settlements

		# simple test for luck: storages are known to easily break on remove:
		for settlement in session.world.settlements:
			for stor in settlement.get_buildings_by_id(BUILDINGS.STORAGE_CLASS):
				wid = stor.worldid
				Tear(stor)(stor.owner)
				try:
					WorldObject.get_object_by_id(wid)
				except WorldObjectNotFound:
					pass
				else:
					assert False

			session.run(seconds = 4)

		# for the heck of it, tear the rest as well
		for settlement in session.world.settlements:
			for building in settlement.buildings[:]:
				if building.id != BUILDINGS.WAREHOUSE_CLASS:
					Tear(building)(building.owner)
			assert len(settlement.buildings) == 1

		session.run(seconds = 60)

	test()

# this disables the test in general and only makes it being run when
# called like this: run_tests.py -a long
test_ai_quick.long = True
