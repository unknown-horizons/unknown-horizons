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
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################


from unittest import mock

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

	# Mock the confirmation dialog to return True (user accepts)
	# In test environment, Dummy is falsy so we need to patch it
	with mock.patch('horizons.world.island.Island.confirm_dialog_to_abandon_buildings', return_value=True):
		Tear(lo)(owner)

	cur_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	new_tents = len(cur_tents)

	new_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	new_trees = island.num_trees

	assert new_trees == old_trees
	# Trees are not torn down (filtered in additional_removals_after_tear)
	# but they ARE removed from settlement when range shrinks
	assert new_trees_owned == 0
	# Tents within lookout range but not warehouse range should be abandoned (torn down)
	assert new_tents < old_tents


@game_test(use_fixture='settlement-range')
def test_remove_settlement_confirmation_accept(s):
	"""
	Test that confirmation dialog is shown and accepted when removing a settlement
	building that would abandon outlying buildings.
	"""
	settlement = s.world.player.settlements[0]
	lo = settlement.buildings_by_id[BUILDINGS.LOOKOUT][0]
	owner = lo.owner
	island = lo.island

	starting_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	old_tents = len(starting_tents)

	old_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	old_trees = island.num_trees

	# Mock the confirmation dialog to return True (user accepts)
	# Patch the Island method directly since ingame_gui is a Dummy
	with mock.patch('horizons.world.island.Island.confirm_dialog_to_abandon_buildings', return_value=True) as mock_confirm:
		Tear(lo)(owner)
		mock_confirm.assert_called_once()

	cur_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	new_tents = len(cur_tents)

	new_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	new_trees = island.num_trees

	# Buildings should be abandoned
	assert new_trees == old_trees
	assert old_trees_owned > new_trees_owned
	assert new_tents < old_tents


@game_test(use_fixture='settlement-range')
def test_remove_settlement_confirmation_cancel(s):
	"""
	Test that cancelling the confirmation dialog preserves buildings and settlement range.
	"""
	settlement = s.world.player.settlements[0]
	lo = settlement.buildings_by_id[BUILDINGS.LOOKOUT][0]
	owner = lo.owner
	island = lo.island

	starting_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	old_tents = len(starting_tents)

	old_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	old_trees = island.num_trees

	# Mock the confirmation dialog to return False (user cancels)
	with mock.patch('horizons.world.island.Island.confirm_dialog_to_abandon_buildings', return_value=False) as mock_confirm:
		Tear(lo)(owner)
		mock_confirm.assert_called_once()

	# The lookout should still be torn down (it was the direct target)
	# but outlying buildings should be preserved
	cur_tents = settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	new_tents = len(cur_tents)

	new_trees_owned = len(settlement.buildings_by_id[BUILDINGS.TREE])
	new_trees = island.num_trees

	# Trees are never owned by settlement, so they don't change
	assert new_trees == old_trees
	# Trees owned by settlement should be preserved (they're not abandoned)
	assert new_trees_owned == old_trees_owned
	# Tents should be preserved (not abandoned due to cancel)
	assert new_tents == old_tents

	# The lookout itself should be gone
	remaining_lo = settlement.buildings_by_id[BUILDINGS.LOOKOUT]
	assert len(remaining_lo) == 0
