# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

from horizons.constants import RES, BUILDINGS
from horizons.command.building import Build, Tear

from tests.game import game_test

# FIXTURE is settlement with a lookout, some tents and some trees
@game_test(use_fixture='settlement-range')
def test_settlement_decrease(s):
	"""
	Check if destroying a lookout destroys surrounding buildings but not trees.
	"""
	settlement = s.world.player.settlements[0]
	lo = settlement.buildings_by_id[ BUILDINGS.LOOKOUT ][0]
	pos = lo.position.origin
	owner = lo.owner
	island = lo.island
	
	old_tents = []
	for coords in island.ground_map:
		tile = island.ground_map[coords]
		building = tile.object
		if building is None or building.id is not BUILDINGS.RESIDENTIAL:
			continue
		if building in old_tents:
			continue
		old_tents.append(building)

	old_trees = []
	for coords in island.ground_map:
		tile = island.ground_map[coords]
		building = tile.object
		if building is None or building.id is not BUILDINGS.TREE:
			continue
		if building in old_trees:
			continue
		old_trees.append(building)

	Tear(lo)(owner)
	
	new_tents = []
	for coords in island.ground_map:
		tile = island.ground_map[coords]
		building = tile.object
		if building is None or building.id is not BUILDINGS.RESIDENTIAL:
			continue
		if building in new_tents:
			continue
		new_tents.append(building)

	new_trees = []
	for coords in island.ground_map:
		tile = island.ground_map[coords]
		building = tile.object
		if building is None or building.id is not BUILDINGS.TREE:
			continue
		if building in new_trees:
			continue
		new_trees.append(building)

	assert len(old_tents) > len(new_tents)
	assert len(new_trees) == len(old_trees)

	trees_owned = True
	for tree in new_trees:
		if tree.owner is not owner:
			trees_owned = False
			break

	assert trees_owned == False
