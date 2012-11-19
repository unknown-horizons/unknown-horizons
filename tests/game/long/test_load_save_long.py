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

from horizons.util.random_map import generate_map_from_seed
from horizons.util.savegameaccessor import SavegameAccessor

from tests.game import game_test

@game_test(mapgen=partial(generate_map_from_seed, 2), human_player=False, ai_players=2, timeout=120)
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

	SavegameAccessor(filename, False)

	os.unlink(filename)

# this disables the test in general and only makes it being run when
# called like this: run_tests.py -a long
test_save_trivial.long = True
