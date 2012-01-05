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
from functools import partial, wraps

import mock
from horizons.util.dbreader import DbReader
from horizons.util.random_map import generate_map_from_seed
from horizons.util.savegameaccessor import SavegameAccessor

from tests.game import game_test


def dbreader_call(func):
	"""
	Wrapper around DbReader.__call__ to convert Dummy objects to valid values.

	This is needed because some classes attempt to store Dummy objects in the
	database, e.g. ConcreteObject with self._instance.getActionRuntime().
	We fix this by replacing it with zero, SQLite doesn't care much about types,
	and hopefully a number is less likely to break code than None.

	Yes, this is ugly and will most likely break later. For now, it works.
	"""
	@wraps(func)
	def wrapper(self, command, *args):
		args = list(args)
		for i in range(len(args)):
			if args[i].__class__.__name__ == 'Dummy':
				args[i] = 0
		return func(self, command, *args)

	wrapper.__original__ = func
	return wrapper
	

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

	DbReader.__call__ = dbreader_call(DbReader.__call__)

	# SavegameManager.write_metadata tries to create a screenshot and breaks when
	# accessing fife properties
	with mock.patch('horizons.spsession.SavegameManager'):
		assert session.save(savegamename=filename)

	DbReader.__call__ = DbReader.__call__.__original__

	SavegameAccessor(filename)

	os.unlink(filename)


# this disables the test in general and only makes it being run when
# called like this: run_tests.py -a long
test_save_trivial.long = True
