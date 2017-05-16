# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import pytest

import horizons.globals
import horizons.main


@pytest.fixture
def s():
	# FIXME For now this is necessary for the game_test decorator to work with pytest.
	# Otherwise it complains about unknown fixtures `s` and `p` (the arguments injected by the
	# decorator).
	pass


@pytest.fixture
def p():
	# FIXME For now this is necessary for the game_test decorator to work with pytest.
	# Otherwise it complains about unknown fixtures `s` and `p` (the arguments injected by the
	# decorator).
	pass


@pytest.fixture(autouse=True)
def database(request):
	"""
	Provide each tests with a fresh database automatically.
	"""
	db = horizons.main._create_main_db()
	horizons.globals.db = db

	yield db

	db.close()
