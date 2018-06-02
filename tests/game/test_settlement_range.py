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


from horizons.command.building import Build, Tear
from horizons.constants import BUILDINGS, RES
from tests.game import game_test


# FIXTURE is settlement with a lookout, some tents and some trees
@game_test(use_fixture='settlement-range')
def test_settlement_decrease(s):
	"""
	Check if destroying a lookout destroys surrounding buildings but not trees.
	"""
	settlement = s.world.player.settlements[0]
	lo = settlement.buildings_by_id[BUILDINGS.LOOKOUT][0]
	pos = lo.position.origin
	owner = lo.owner
	island = lo.island

	starting_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	old_tents = len(starting_tents)

	old_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	old_trees = island.num_trees

	Tear(lo)(owner)

	cur_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	new_tents = len(cur_tents)

	new_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	new_trees = island.num_trees

	assert new_trees == old_trees
	assert old_trees_owned > new_trees_owned
	assert new_tents < old_tents
