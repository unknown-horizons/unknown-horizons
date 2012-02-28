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

from horizons.command.building import Build
from horizons.command.production import ToggleActive
from horizons.constants import BUILDINGS, PRODUCTION
from horizons.util.worldobject import WorldObject
from horizons.world.production.producer import Producer

from tests.game import game_test, new_session, settle, load_session

@game_test(manual_session=True)
def test_load_inactive_production():
	"""
	create a savegame with a inactive production, load it
	"""
	session, player = new_session()
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)
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
		Build(BUILDINGS.TREE_CLASS, x, 29, island, settlement=settlement,)(player)
	building = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)
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
