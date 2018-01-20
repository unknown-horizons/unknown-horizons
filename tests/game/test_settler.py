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

from horizons.command.building import Build
from horizons.command.uioptions import SetSettlementUpgradePermissions
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, GAME, RES, TIER
from tests.game import game_test, settle


@game_test()
def test_settler_level(s, p):
	"""
	Verify that settler level up works.
	"""
	settlement, island = settle(s)

	settler = Build(BUILDINGS.RESIDENTIAL, 22, 22, island, settlement=settlement)(p)

	# make it happy
	inv = settler.get_component(StorageComponent).inventory
	to_give = inv.get_free_space_for(RES.HAPPINESS)
	inv.alter(RES.HAPPINESS, to_give)
	level = settler.level

	s.run(seconds=GAME.INGAME_TICK_INTERVAL)

	# give upgrade res
	inv.alter(RES.BOARDS, 100)

	s.run(seconds=GAME.INGAME_TICK_INTERVAL)

	# should have leveled up
	assert settler.level == level + 1


@game_test()
def test_deny_upgrade_permissions_special(s, p):
	"""
	Verify that denying upgrade permissions works even though the settler
	leveled down after starting the upgrade process.
	"""
	settlement, island = settle(s)

	settler = Build(BUILDINGS.RESIDENTIAL, 22, 22, island, settlement=settlement)(p)

	# make it happy
	inv = settler.get_component(StorageComponent).inventory
	to_give = inv.get_free_space_for(RES.HAPPINESS)
	inv.alter(RES.HAPPINESS, to_give)

	s.run(seconds=GAME.INGAME_TICK_INTERVAL)

	# give upgrade res
	inv.alter(RES.BOARDS, 100)

	s.run(seconds=GAME.INGAME_TICK_INTERVAL)

	# should have leveled up
	assert settler.level == TIER.PIONEERS
	assert settler._upgrade_production is None

	# Start leveling up again
	settler._add_upgrade_production_line()
	assert settler._upgrade_production is not None

	s.run(seconds=1)

	# Force the settler to level down, even though it is currently
	# trying to upgrade
	settler.level_down()

	# Make sure this worked!
	assert settler._upgrade_production is None

	# Make sure forbidding upgrades works
	SetSettlementUpgradePermissions(settlement, TIER.SAILORS, False).execute(s)
	assert settler.level == TIER.SAILORS
