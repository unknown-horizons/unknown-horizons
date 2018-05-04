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

from pathlib import PurePath

from horizons.util.platform import get_user_game_directory


def test_get_user_game_directory_windows(mocker, tmpdir):
	mocker.patch('horizons.util.platform.get_home_directory',
	             return_value=PurePath(str(tmpdir)))
	mocker.patch('platform.system', return_value='Windows')

	assert str(get_user_game_directory()) == tmpdir.join('My Games', 'unknown-horizons')


def test_get_user_game_directory_unix(mocker, tmpdir):
	mocker.patch('horizons.util.platform.get_home_directory',
	             return_value=PurePath(str(tmpdir)))
	mocker.patch('platform.system', return_value='Linux')

	assert str(get_user_game_directory()) == tmpdir.join('.unknown-horizons')
