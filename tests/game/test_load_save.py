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
import bz2
import tempfile

from horizons.command.building import Build
from horizons.command.production import ToggleActive
from horizons.command.unit import CreateUnit
from horizons.constants import BUILDINGS, PRODUCTION, UNITS, RES, GAME
from horizons.util import WorldObject, Point
from horizons.world.production.producer import Producer
from horizons.component.collectingcomponent import CollectingComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.world.units.collectors import Collector
from horizons.scheduler import Scheduler

from tests.game import game_test, new_session, settle, load_session, TEST_FIXTURES_DIR


# utility
def saveload(session):
	"""Use like this:
	session = saveload(session)
	"""
	fd, filename = tempfile.mkstemp()
	os.close(fd)
	assert session.save(savegamename=filename)
	session.end(keep_map=True)
	session = load_session(filename)
	Scheduler().before_ticking() # late init finish (not ticking already)
	return session

@game_test(manual_session=True)
def test_load_inactive_production():
	"""
	create a savegame with a inactive production, load it
	"""
	session, player = new_session()
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK, 30, 30, island, settlement=settlement)(player)
	# Set lumberjack to inactive
	lj.get_component(Producer).set_active(active = False)
	worldid = lj.worldid

	session.run(seconds=1)

	fd, filename = tempfile.mkstemp()
	os.close(fd)

	assert session.save(savegamename=filename)

	session.end(keep_map=True)

	# Load game
	session = load_session(filename)
	loadedlj = WorldObject.get_object_by_id(worldid)

	# Make sure it really is not active
	producer = loadedlj.get_component(Producer)
	assert not producer.is_active()

	# Trigger bug #1359
	ToggleActive(producer).execute(session)

	session.end()

def create_lumberjack_production_session():
	"""Create a saved game with a producing production and then load it."""
	session, player = new_session()
	settlement, island = settle(session)

	for x in [29, 30, 31, 32]:
		Build(BUILDINGS.TREE, x, 29, island, settlement=settlement,)(player)
	building = Build(BUILDINGS.LUMBERJACK, 30, 30, island, settlement=settlement)(player)
	production = building.get_component(Producer).get_productions()[0]

	# wait for the lumberjack to start producing
	while True:
		if production.get_state() is PRODUCTION.STATES.producing:
			break
		session.run(ticks=1)

	fd1, filename1 = tempfile.mkstemp()
	os.close(fd1)
	assert session.save(savegamename=filename1)
	session.end(keep_map=True)

	# load the game
	session = load_session(filename1)
	return session

@game_test(manual_session=True)
def test_load_producing_production_fast():
	"""Create a saved game with a producing production, load it, and try to save again very fast."""
	session = create_lumberjack_production_session()
	session.run(ticks=2)

	# trigger #1395
	fd2, filename2 = tempfile.mkstemp()
	os.close(fd2)
	assert session.save(savegamename=filename2)
	session.end()

@game_test(manual_session=True)
def test_load_producing_production_slow():
	"""Create a saved game with a producing production, load it, and try to save again in a few seconds."""
	session = create_lumberjack_production_session()
	session.run(ticks=100)

	# trigger #1394
	fd2, filename2 = tempfile.mkstemp()
	os.close(fd2)
	assert session.save(savegamename=filename2)
	session.end()

@game_test(manual_session=True)
def test_hunter_save_load():
	"""Save/loading hunter in different states"""
	session, player = new_session()
	settlement, island = settle(session)

	# setup hunter, trees (to keep animals close) and animals

	hunter = Build(BUILDINGS.HUNTER, 30, 30, island, settlement=settlement)(player)
	hunter_worldid = hunter.worldid
	del hunter # invalid after save/load

	for x in xrange(27, 29):
		for y in xrange(25, 28):
			assert Build(BUILDINGS.TREE, x, y, island, settlement=settlement)(player)

	CreateUnit(island.worldid, UNITS.WILD_ANIMAL, 27, 27)(issuer=None)
	CreateUnit(island.worldid, UNITS.WILD_ANIMAL, 28, 27)(issuer=None)
	CreateUnit(island.worldid, UNITS.WILD_ANIMAL, 29, 27)(issuer=None)

	def get_hunter_collector(session):
		hunter = WorldObject.get_object_by_id(hunter_worldid)
		return hunter.get_component(CollectingComponent)._CollectingComponent__collectors[0]

	def await_transition(session, collector, old_state, new_state):
		assert collector.state == old_state, "expected old state %s, got %s" % (old_state, collector.state)
		while collector.state == old_state:
			session.run(seconds=1)
		assert collector.state == new_state, "expected new state %s, got %s" % (old_state, collector.state)


	sequence = [
	  Collector.states.idle,
	  Collector.states.waiting_for_animal_to_stop,
	  Collector.states.moving_to_target,
	  Collector.states.working,
	  Collector.states.moving_home,
	  Collector.states.idle
	  ]

	# do full run without saveload
	collector = get_hunter_collector(session)
	for i in xrange(len(sequence)-1):
		await_transition(session, collector, sequence[i], sequence[i+1])

	# do full run with saveload
	for i in xrange(len(sequence)-1):
		collector = get_hunter_collector(session)
		await_transition(session, collector, sequence[i], sequence[i+1])
		session = saveload(session)

	# last state reached successfully 2 times -> finished


@game_test(manual_session=True)
def test_settler_save_load():
	"""Save/loading """
	session, player = new_session()
	settlement, island = settle(session)

	# setup:
	# 1) build settler
	# 2) save/load
	# 3) build main square
	# -> settler won't load properly and not use the resources and die

	settler = Build(BUILDINGS.RESIDENTIAL, 25, 22, island, settlement=settlement)(player)
	assert settler

	main_square = Build(BUILDINGS.MAIN_SQUARE, 23, 24, island, settlement=settlement)(player)
	assert main_square
	main_square.get_component(StorageComponent).inventory.alter(RES.FOOD, 100)

	session = saveload(session)

	session.run(seconds=500)

	tile = session.world.get_tile(Point(25, 22))

	# tile will contain ruin in case of failure
	assert tile.object.id == BUILDINGS.RESIDENTIAL


@game_test(manual_session=True)
def test_savegame_upgrade():
	"""Loads an old savegame and keeps it running for a while"""
	fd, filename = tempfile.mkstemp()
	os.close(fd)

	path = os.path.join(TEST_FIXTURES_DIR, 'large.sqlite.bz2')
	compressed_data = open(path, "r").read()
	data = bz2.decompress( compressed_data )
	f = open(filename, "w")
	f.write(data)
	f.close()

	# check if loading and running fails
	session = load_session(filename)
	session.run(seconds=30)


@game_test
def test_settler_level_save_load(s, p):
	"""
	Verify that settler level up with save/load works
	"""
	for test_level in xrange(3): # test upgrade 0->1, 1->2 and 2->3
		session, player = new_session()
		settlement, island = settle(s)

		settler = Build(BUILDINGS.RESIDENTIAL, 22, 22, island, settlement=settlement)(p)
		settler.level += test_level
		settler_worldid = settler.worldid
		
		# make it happy
		inv = settler.get_component(StorageComponent).inventory
		to_give = inv.get_free_space_for(RES.HAPPINESS)
		inv.alter(RES.HAPPINESS, to_give)
		level = settler.level

		# wait for it to realize it's supposed to upgrade
		s.run(seconds=GAME.INGAME_TICK_INTERVAL)

		session = saveload(session)
		settler = WorldObject.get_object_by_id(settler_worldid)
		inv = settler.get_component(StorageComponent).inventory

		# continue
		s.run(seconds=GAME.INGAME_TICK_INTERVAL)

		assert settler.level == level
		# give upgrade res
		inv.alter(RES.BOARDS, 100)
		inv.alter(RES.BRICKS, 100)
		
		# give it max population
		settler.inhabitants = settler.inhabitants_max		

		s.run(seconds=GAME.INGAME_TICK_INTERVAL)

		# should have leveled up
		assert settler.level == level + 1
