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
import os
import tempfile

from horizons.command.building import Build, Tear
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.collectingcompontent import CollectingComponent
from horizons.world.production.producer import Producer, QueueProducer
from horizons.constants import BUILDINGS, RES, PRODUCTIONLINES, GAME
from horizons.util.worldobject import WorldObject
from horizons.world.production.utilisation import FieldUtilisation

from tests.game import settle, game_test, new_session, load_session
from tests.game.test_buildings import test_brick_production_chain, test_tool_production_chain
from tests.game.test_farm import _build_farm


@game_test
def test_ticket_979(s, p):
	settlement, island = settle(s)
	storage_collectors = settlement.warehouse.get_component(CollectingComponent).get_local_collectors()

	farm = _build_farm(30, 30, BUILDINGS.POTATO_FIELD_CLASS, island, settlement, p)

	# Let it work for a bit
	s.run(seconds=60)
	assert farm.get_component(StorageComponent).inventory[RES.FOOD_ID]

	# Depending on auto unloading (which we aren't interested in here),
	# the settlement inventory may already be full of food: dispose of it
	settlement.get_component(StorageComponent).inventory.alter(RES.FOOD_ID, -settlement.get_component(StorageComponent).inventory[RES.FOOD_ID])
	assert settlement.get_component(StorageComponent).inventory[RES.FOOD_ID] == 0

	# Build a road, connecting farm and warehouse
	for y in range(23, 30):
		assert Build(BUILDINGS.TRAIL_CLASS, 30, y, island, settlement=settlement)(p)

	# Step forward in time until a collector picked a job
	got_job = False
	while not got_job:
		s.run()
		if any(c.job for c in storage_collectors):
			got_job = True

	Tear(farm)(p)

	# Let the collector reach the not existing target
	s.run(seconds=10)

@game_test
def test_ticket_1016(s, p):
	settlement, island = settle(s)

	farm = _build_farm(30, 30, BUILDINGS.POTATO_FIELD_CLASS, island, settlement, p)

	# tear down job target, then home building (in the same tick)

	torn_down = False
	while not torn_down:
		s.run(seconds=1)
		for col in farm.get_component(CollectingComponent)._CollectingComponent__collectors:
			if col.job:
				Tear(col.job.object)(p)
				Tear(farm)(p)
				torn_down = True
				break

	s.run(seconds=30)



@game_test
def test_ticket_1005(s, p):
	settlement, island = settle(s)
	assert len(s.world.ships) == 2

	builder = Build(BUILDINGS.BOATBUILDER_CLASS, 35, 20, island, settlement=settlement)(p)
	builder.get_component(StorageComponent).inventory.alter(RES.TEXTILE_ID, 5)
	builder.get_component(StorageComponent).inventory.alter(RES.BOARDS_ID, 4)
	builder.get_component(Producer).add_production_by_id(15)

	s.run(seconds=130)

	assert len(s.world.ships) == 3


@game_test
def test_ticket_1232(s, p):
	settlement, island = settle(s)
	assert len(s.world.ships) == 2

	boat_builder = Build(BUILDINGS.BOATBUILDER_CLASS, 35, 20, island, settlement=settlement)(p)
	boat_builder.get_component(StorageComponent).inventory.alter(RES.TEXTILE_ID, 10)
	boat_builder.get_component(StorageComponent).inventory.alter(RES.BOARDS_ID, 8)
	assert isinstance(boat_builder.get_component(Producer),QueueProducer)

	production_finished = [False]
	boat_builder.get_component(Producer).add_production_by_id(PRODUCTIONLINES.HUKER)
	production1 = boat_builder.get_component(Producer)._get_production(PRODUCTIONLINES.HUKER)
	production1.add_production_finished_listener(lambda _: production_finished.__setitem__(0, True))
	assert boat_builder.get_component(Producer).is_active()
	while not production_finished[0]:
		s.run(ticks=1)
	assert not boat_builder.get_component(Producer).is_active()
	assert len(s.world.ships) == 3
	# Make sure enough res are available
	boat_builder.get_component(StorageComponent).inventory.alter(RES.TEXTILE_ID, 10)
	boat_builder.get_component(StorageComponent).inventory.alter(RES.BOARDS_ID, 8)
	boat_builder.get_component(StorageComponent).inventory.alter(RES.TOOLS_ID, 5)

	boat_builder.get_component(Producer).add_production_by_id(PRODUCTIONLINES.HUKER)
	assert boat_builder.get_component(Producer).is_active()
	s.run(seconds=130)
	assert not boat_builder.get_component(Producer).is_active()
	assert len(s.world.ships) == 4


def test_brick_tool_interference():
	"""
	Running the brick test at first will break the tool test.
	"""
	test_brick_production_chain()
	test_tool_production_chain()


def test_tool_brick_interference():
	"""
	Running the tool test at first will break the brick test.
	"""
	test_tool_production_chain()
	test_brick_production_chain()

@game_test(manual_session=True)
def test_ticket_1427():
	"""Boatbuilder production progress should be saved properly"""

	session, player = new_session()
	settlement, island = settle(session)

	boat_builder = Build(BUILDINGS.BOATBUILDER_CLASS, 35, 20, island, settlement=settlement)(player)
	worldid = boat_builder.worldid

	# Make sure no boards are available
	settlement.get_component(StorageComponent).inventory.alter(RES.BOARDS_ID, -1000)

	bb_storage = boat_builder.get_component(StorageComponent)

	# Add production to use resources
	bb_producer =  boat_builder.get_component(Producer)
	bb_producer.add_production_by_id(PRODUCTIONLINES.HUKER)
	production = bb_producer._productions[PRODUCTIONLINES.HUKER]

	assert production.progress == 0.0

	bb_storage.inventory.alter(RES.TEXTILE_ID, 10)
	bb_storage.inventory.alter(RES.BOARDS_ID, 6)

	production_line = production._prod_line

	# Make sure the boatbuilder consumes everything in his inventory
	session.run(seconds=10)

	# Check if correctly consumed wood
	assert production_line.consumed_res[RES.BOARDS_ID] == -2

	# Save all production process for later
	expected_consumed_res = production_line.consumed_res
	expected_produced_res = production_line.produced_res
	expected_production = production_line.production
	expected_progress = production.progress

	# Make sure the producer used the boards
	assert bb_storage.inventory[RES.BOARDS_ID] == 0

	fd, filename = tempfile.mkstemp()
	os.close(fd)
	assert session.save(savegamename=filename)
	session.end(keep_map=True)

	# Load game
	session = load_session(filename)
	loadedbb = WorldObject.get_object_by_id(worldid)

	production_loaded = loadedbb.get_component(Producer)._productions[PRODUCTIONLINES.HUKER]
	production_line_loaded = production_loaded._prod_line

	# Make sure everything is loaded correctly
	assert expected_consumed_res == production_line_loaded.consumed_res
	assert expected_produced_res == production_line_loaded.produced_res
	assert expected_production == production_line_loaded.production
	assert expected_progress == production_loaded.progress

	# if you don't let the session run for a bit then collectors won't be fully initialized and can't be killed => another test will fail in session.end()
	session.run(seconds=1)
	session.end()


@game_test
def test_settler_level(s, p):
	"""
	Verify that settler level up works.
	"""
	settlement, island = settle(s)

	settler = Build(BUILDINGS.RESIDENTIAL_CLASS, 22, 22, island, settlement=settlement)(p)

	# make it happy
	inv = settler.get_component(StorageComponent).inventory
	to_give = inv.get_free_space_for(RES.HAPPINESS_ID)
	inv.alter(RES.HAPPINESS_ID, to_give)
	level = settler.level

	s.run(seconds=GAME.INGAME_TICK_INTERVAL)

	# give upgrade res
	inv.alter(RES.BOARDS_ID, 100)

	s.run(seconds=GAME.INGAME_TICK_INTERVAL)

	# should have leveled up
	assert settler.level == level + 1

@game_test
def test_ticket_1523(s, p):
	settlement, island = settle(s)

	farm = _build_farm(30, 30, BUILDINGS.POTATO_FIELD_CLASS, island, settlement, p)

	# Let it work for a bit
	s.run(seconds=60)
	assert farm.get_component(StorageComponent).inventory[RES.FOOD_ID]


	assert isinstance(farm.get_component(Producer)._Producer__utilisation, FieldUtilisation)
	# Should be 0.5
	assert not farm.get_component(Producer).capacity_utilisation_below(0.4)
	assert farm.get_component(Producer).capacity_utilisation > 0.4
