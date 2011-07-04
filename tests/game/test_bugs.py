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

from horizons.command.building import Build, Tear

from tests.game import settle, game_test
from tests.game.test_buildings import test_brick_production_chain, test_tool_production_chain
from tests.game.test_farm import _build_farm, POTATO_FIELD


BOAT_BUILDER = 12
TRAIL = 15
CLAY_PIT = 23
MOUNTAIN = 34

RAW_IRON = 24
RAW_CLAY = 20


@game_test
def test_ticket_979(s, p):
	settlement, island = settle(s)
	storage_collectors = settlement.branch_office.get_local_collectors()

	farm = _build_farm(30, 30, POTATO_FIELD, island, settlement, p)

	# Let it work for a bit
	s.run(seconds=60)
	assert farm.inventory[5]

	# Build a road, connecting farm and branch office
	for y in range(23, 30):
		assert Build(TRAIL, 30, y, island, settlement=settlement)(p)

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

	farm = _build_farm(30, 30, POTATO_FIELD, island, settlement, p)

	# tear down job target, then home building (in the same tick)

	torn_down = False
	while not torn_down:
		s.run(seconds=1)
		for col in farm._CollectingBuilding__collectors:
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

	builder = Build(BOAT_BUILDER, 35, 20, island, settlement=settlement)(p)
	builder.inventory.alter(3, 5)	# textile
	builder.inventory.alter(4, 4)	# boards
	builder.add_production_by_id(15)

	s.run(seconds=130)

	assert len(s.world.ships) == 3


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
