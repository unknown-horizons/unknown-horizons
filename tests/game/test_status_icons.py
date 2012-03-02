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

from horizons.command.building import Build
from horizons.command.production import ToggleActive
from horizons.world.production.producer import Producer
from horizons.world.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, RES
from horizons.world.status import SettlerUnhappyStatus, DecommissionedStatus, ProductivityLowStatus, InventoryFullStatus
from horizons.util.messaging.message import AddStatusIcon

import mock
from tests.game import settle, game_test

def assert_called_with_icon(cb, icon):
	assert cb.called
	# the first and only parameter is the message send
	assert cb.call_args[0][0].icon.__class__ == icon


@game_test
def test_productivity_low(session, player):
	settlement, island = settle(session)

	Build(BUILDINGS.CHARCOAL_BURNER_CLASS, 30, 30, island, settlement=settlement)(player)

	cb = mock.Mock()
	session.message_bus.subscribe_globally(AddStatusIcon, cb)

	# Not yet low
	assert not cb.called

	session.run(seconds=60)

	# Now low
	assert_called_with_icon(cb, ProductivityLowStatus)

@game_test
def test_settler_unhappy(session, player):
	settlement, island = settle(session)

	cb = mock.Mock()
	session.message_bus.subscribe_globally(AddStatusIcon, cb)

	settler = Build(BUILDINGS.RESIDENTIAL_CLASS, 30, 30, island, settlement=settlement)(player)

	# certainly not unhappy
	assert settler.happiness > 0.45
	assert not cb.called

	# make it unhappy
	settler.get_component(StorageComponent).inventory.alter(RES.HAPPINESS_ID, -settler.happiness)
	assert settler.happiness < 0.1
	assert_called_with_icon(cb, SettlerUnhappyStatus)


@game_test
def test_decommissioned(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	cb = mock.Mock()
	session.message_bus.subscribe_globally(AddStatusIcon, cb)

	assert not cb.called

	ToggleActive(lj.get_component(Producer))(player)

	assert_called_with_icon(cb, DecommissionedStatus)

@game_test
def test_inventory_full(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	cb = mock.Mock()
	session.message_bus.subscribe_globally(AddStatusIcon, cb)

	# Not full
	assert not cb.called

	inv = lj.get_component(StorageComponent).inventory
	res = RES.BOARDS_ID
	inv.alter(res, inv.get_free_space_for( res ) )

	session.run(seconds=1)

	# Full
	assert_called_with_icon(cb, InventoryFullStatus)
