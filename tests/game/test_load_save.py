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
from functools import partial

from horizons.command.building import Build
from horizons.command.production import ToggleActive
from horizons.constants import BUILDINGS
from horizons.util.random_map import generate_map_from_seed
from horizons.util.savegameaccessor import SavegameAccessor
from horizons.util.worldobject import WorldObject
from horizons.world.production.producer import Producer

from tests.game import game_test, new_session, settle, load_session


@game_test(mapgen=partial(generate_map_from_seed, 2), human_player=False, ai_players=2, timeout=0)
def test_save_trivial(session, _):
	"""
	Let 2 AI players play for a while, then attempt to save the game.

	Be aware, this is a pretty simple test and it doesn't actually check what is
	beeing saved.
	"""
	session.run(seconds=4 * 60)

	fd, filename = tempfile.mkstemp()
	os.close(fd)

	assert session.save(savegamename=filename)

	SavegameAccessor(filename)

	os.unlink(filename)


# this disables the test in general and only makes it being run when
# called like this: run_tests.py -a long
test_save_trivial.long = True


@game_test(timeout=0, manual_session=True)
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
	assert not loadedlj.get_component(Producer).is_active()

	# Trigger bug #1359
	ToggleActive(loadedlj).execute(session)

	session.end()
