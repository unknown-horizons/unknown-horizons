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

from tests.game import settle, game_test, SPSession

@game_test
def test_productivity_low(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.CHARCOAL_BURNER_CLASS, 30, 30, island, settlement=settlement)(player)

	called = [False]

	def add_icon(message):
		isinstance(message, AddStatusIcon)
		if message.icon.__class__ == ProductivityLowStatus:
			called.__setitem__(0, True)

	session.message_bus.subscribe_globally(AddStatusIcon, add_icon)


	# precondition
	assert abs(lj.get_component(Producer).capacity_utilisation) < 0.0001

	# Not yet low
	assert not called[0]

	session.run(seconds=60)

	# Now low
	assert called[0]

@game_test
def test_settler_unhappy(session, player):
	settlement, island = settle(session)
	assert isinstance(session, SPSession)

	called = [False]

	def add_icon(message):
		isinstance(message, AddStatusIcon)
		if message.icon.__class__ == SettlerUnhappyStatus:
			called.__setitem__(0, True)

	session.message_bus.subscribe_globally(AddStatusIcon, add_icon)

	settler = Build(BUILDINGS.RESIDENTIAL_CLASS, 30, 30, island, settlement=settlement)(player)

	# certainly not unhappy
	assert settler.happiness > 0.45
	assert not called[0]

	# make it unhappy
	settler.get_component(StorageComponent).inventory.alter(RES.HAPPINESS_ID, -settler.happiness)
	assert settler.happiness < 0.1
	assert called[0]



@game_test
def test_decommissioned(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	called = [False]

	def add_icon(message):
		isinstance(message, AddStatusIcon)
		if message.icon.__class__ == DecommissionedStatus:
			called.__setitem__(0, True)

	session.message_bus.subscribe_globally(AddStatusIcon, add_icon)

	assert not called[0]

	ToggleActive(lj.get_component(Producer))(player)

	assert called[0]

@game_test
def test_inventory_full(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	called = [False]

	def add_icon(message):
		isinstance(message, AddStatusIcon)
		if message.icon.__class__ == InventoryFullStatus:
			called.__setitem__(0, True)

	session.message_bus.subscribe_globally(AddStatusIcon, add_icon)

	# Not full
	assert not called[0]

	inv = lj.get_component(StorageComponent).inventory
	res = RES.BOARDS_ID
	inv.alter(res, inv.get_free_space_for( res ) )

	# Full
	assert called[0]






