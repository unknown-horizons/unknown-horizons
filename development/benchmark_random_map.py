#!/usr/bin/env python2
# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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
import sys
import timeit


# make this script work both when started inside development and in the uh root dir
if not os.path.exists('content'):
	os.chdir('..')
assert os.path.exists('content'), 'Content dir not found.'

sys.path.append('.')

from run_uh import init_environment
init_environment(False)


from horizons.util import random_map
from horizons.util.dbreader import DbReader


islands = random_map.generate_random_map("UHU", 150, 50, 70, 70, 30)


def run():
	db = DbReader(":memory:")
	with open('content/map-template.sql') as template:
		db.execute_script(template.read())

	for index, island_string in enumerate(islands):
		random_map.create_random_island(db, index, island_string)


t = timeit.Timer('run()', setup='from __main__ import run')
print t.timeit(10)
