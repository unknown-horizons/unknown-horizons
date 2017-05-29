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

import urllib.request
from pathlib import PurePosixPath, PureWindowsPath
from unittest import mock

import pytest

from horizons.util.checkupdates import check_for_updates, is_system_installed, is_version_newer


def test_check_for_updates(mocker):
	"""
	Skip update check for platforms other than Windows or iOS where it's likely that the game
	was installed using the system's package manager.
	"""
	mocker.patch('platform.system', return_value='Linux')
	mocker.patch('horizons.util.checkupdates.is_system_installed', return_value=True)
	urlopen = mocker.patch.object(urllib.request, 'urlopen')

	check_for_updates()

	assert not urlopen.called


@pytest.mark.parametrize('json_data,result', [
	(b'', None),
	(b'{x', None),
	(b'{}', None),
	(b'{"version": "2014.1"}', None),
	(b'{"version": "2017.2"}', {'version': '2017.2'})])
def test_check_for_updates_json_data(json_data, result, mocker):
	"""
	Test various cases for the JSON data.
	"""
	mocker.patch('horizons.constants.VERSION.RELEASE_VERSION',
			new_callable=mock.PropertyMock, return_value='2017.1')
	mocker.patch('platform.system', return_value='Windows')
	urlopen = mocker.patch.object(urllib.request, 'urlopen')

	# this beauty is a mock for the urlopen context manager
	(urlopen.return_value
		.__enter__ # context manager
		.return_value # returns a file-like object
		.read.return_value) = json_data # whose read method returns our json

	assert check_for_updates() == result


@pytest.mark.parametrize('original,candidate,result', [
	('2017.2', None, False),
	('2017.2', '', False),
	('2017.2', 'something wrong', False),
	('2017.2', '2017.1', False),
	('2017.2', '2017.2', False),
	('2017.2', '2017.3', True),
	('2017.2-610-g6f1c0da66', '2017.2', False),
	('2017.2-610-g6f1c0da66', '2017.3', True)])
def test_is_version_newer(original, candidate, result):
	assert is_version_newer(original, candidate) == result


@pytest.mark.parametrize('uh_path,home_dir,result', [
	(PurePosixPath('/usr/local/share/games/'), PurePosixPath('/home/max/'), True),
	(PurePosixPath('/home/max/games/'), PurePosixPath('/home/max/'), False),
	(PureWindowsPath('C:\\Programs\\Uh'), PureWindowsPath('C:\\Users\\max'), True),
	(PureWindowsPath('C:\\Users\\max\\uh'), PureWindowsPath('C:\\Users\\max'), False)])
def test_is_system_installed(uh_path, home_dir, result, mocker):
	mocker.patch('horizons.util.checkupdates.get_home_directory', return_value=home_dir)
	assert is_system_installed(uh_path) == result
