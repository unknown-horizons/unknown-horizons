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
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer
from horizons.constants import BUILDINGS, RES, PRODUCTIONLINES, PRODUCTION

from tests.game import settle, game_test

@game_test
def test_basic_wood_production(session, player):
	"""This is a fairly detailed test of the simple wood production"""

	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)
	assert lj.id == BUILDINGS.LUMBERJACK_CLASS

	storage = lj.get_component(StorageComponent)
	assert isinstance(storage, StorageComponent)

	producer = lj.get_component(Producer)
	assert isinstance(producer, Producer)


	# Make sure wood production is added
	assert PRODUCTIONLINES.TREES in producer.get_production_lines()
	assert producer.has_production_line(PRODUCTIONLINES.TREES)
	production = producer._get_production(PRODUCTIONLINES.TREES)

	# Check if the production finished listener is called
	production_finished = [False]
	production.add_production_finished_listener(lambda _: production_finished.__setitem__(0, True))

	assert producer.is_active()

	# No res yet, waiting...
	assert producer._get_current_state() == PRODUCTION.STATES.waiting_for_res

	# Got res, producing
	storage.inventory.alter(RES.TREES_ID, 1)
	assert producer._get_current_state() == PRODUCTION.STATES.producing

	# Work half-way
	session.run(seconds=3)

	#  Pause
	producer.toggle_active()
	assert not producer.is_active()
	assert producer._get_current_state() == PRODUCTION.STATES.paused

	# Unpause
	producer.toggle_active()
	assert producer.is_active()
	assert producer._get_current_state() == PRODUCTION.STATES.producing

	# Finish work partly
	session.run(seconds=2)

	assert producer._get_current_state() == PRODUCTION.STATES.producing
	assert storage.inventory[RES.BOARDS_ID] == 0
	# Callback should not yet have been called
	assert not production_finished[0]

	# Finish work
	session.run(seconds=10)

	# out of res again, waiting for res
	assert producer._get_current_state() == PRODUCTION.STATES.waiting_for_res

	# Produced one board
	assert storage.inventory[RES.BOARDS_ID] == 1
	# Callback should have been called now
	assert production_finished[0]

	# Fillup storage
	storage.inventory.alter(RES.BOARDS_ID, storage.inventory.get_limit(RES.BOARDS_ID))

	# Cannot produce because inventory full
	assert producer._get_current_state() == PRODUCTION.STATES.inventory_full

	# Empty inventory, wait again
	storage.inventory.alter(RES.BOARDS_ID, -storage.inventory.get_limit(RES.BOARDS_ID))
	assert producer._get_current_state() == PRODUCTION.STATES.waiting_for_res